"""
Ollama provider implementation for local LLM operations.
Handles text generation using local Ollama server.
"""

from typing import Any, List, Optional

import aiohttp

from src.exceptions import APIError, LLMProviderError
from src.models.model_info import (
    ModelCapabilities,
    ModelInfo,
    ModelListResponse,
    ModelPricing,
)
from src.utils.model_cache import ModelCacheManager

from ..base import LLMProvider


class OllamaProvider(LLMProvider):
    """Ollama implementation of LLM provider."""

    async def initialize(self) -> None:
        """Initialize Ollama provider."""
        # Ollama doesn't need API key, uses local server
        default_url = 'http://127.0.0.1:11434'
        self.base_url = self.config.get('base_url', default_url)
        self.default_model = self.config.get('default_model', 'llama2')
        self.timeout = self.config.get('timeout', 60)  # Longer timeout for local
        self.max_retries = self.config.get('max_retries', 3)

        self.log_operation(
            'initialized_ollama_provider',
            model=self.default_model,
            base_url=self.base_url,
        )

    async def cleanup(self) -> None:
        """Cleanup Ollama provider resources."""
        self.log_operation('cleaned_up_ollama_provider')

    async def health_check(self) -> bool:
        """Check Ollama provider health."""
        try:
            # Test Ollama server connection
            url = f"{self.base_url}/api/tags"

            async with aiohttp.ClientSession() as session:
                timeout = aiohttp.ClientTimeout(total=10)
                async with session.get(url, timeout=timeout) as response:
                    return response.status == 200
        except Exception as e:
            self.log_error(e, 'ollama_health_check_failed')
            return False

    async def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> str:
        """Generate text using Ollama."""
        model_name = model or self.default_model

        # Build request payload for Ollama
        payload = {
            'model': model_name,
            'prompt': prompt,
            'stream': False,
            'options': {
                'temperature': temperature or 0.7,
                'num_predict': max_tokens or 1000,
            },
        }

        url = f"{self.base_url}/api/generate"
        headers = {'Content-Type': 'application/json'}

        try:
            async with aiohttp.ClientSession() as session:
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                async with session.post(
                    url, json=payload, headers=headers, timeout=timeout
                ) as response:
                    response_data = await response.json()

                    if response.status != 200:
                        error_msg = response_data.get('error', 'Unknown error')
                        raise APIError(
                            f'Ollama API error: {error_msg}', provider='ollama'
                        )

                    # Extract generated text
                    generated_text = response_data.get('response', '')
                    if not generated_text:
                        raise LLMProviderError('No response text from Ollama')

                    self.log_operation(
                        'generated_text',
                        provider='ollama',
                        model=model_name,
                        prompt_length=len(prompt),
                        response_length=len(generated_text),
                    )

                    return generated_text

        except aiohttp.ClientError as e:
            error_msg = f'Ollama request failed: {e}'
            raise APIError(error_msg, provider='ollama') from e
        except KeyError as e:
            error_msg = f'Invalid Ollama response format: {e}'
            raise LLMProviderError(error_msg) from e

    async def generate_embeddings(
        self, texts: List[str], model: Optional[str] = None
    ) -> List[List[float]]:
        """Generate embeddings using Ollama."""
        # Ollama supports embeddings through /api/embeddings
        model_name = model or self.default_model

        embeddings = []

        for text in texts:
            payload = {'model': model_name, 'prompt': text}

            url = f"{self.base_url}/api/embeddings"
            headers = {'Content-Type': 'application/json'}

            try:
                async with aiohttp.ClientSession() as session:
                    timeout = aiohttp.ClientTimeout(total=self.timeout)
                    async with session.post(
                        url, json=payload, headers=headers, timeout=timeout
                    ) as response:
                        response_data = await response.json()

                        if response.status != 200:
                            error_msg = response_data.get('error', 'Unknown error')
                            raise APIError(
                                f'Ollama embedding error: {error_msg}',
                                provider='ollama',
                            )

                        embedding = response_data.get('embedding', [])
                        if not embedding:
                            raise LLMProviderError('No embedding in Ollama response')

                        embeddings.append(embedding)

            except aiohttp.ClientError as e:
                error_msg = f'Ollama embedding request failed: {e}'
                raise APIError(error_msg, provider='ollama') from e
            except KeyError as e:
                error_msg = f'Invalid Ollama embedding response: {e}'
                raise LLMProviderError(error_msg) from e

        self.log_operation(
            'generated_embeddings',
            provider='ollama',
            texts_count=len(texts),
            embedding_dimension=len(embeddings[0]) if embeddings else 0,
        )

        return embeddings

    async def list_models(self, use_cache: bool = True) -> ModelListResponse:
        """List available Ollama models with detailed information."""
        cache_manager = ModelCacheManager()

        # Try to get from cache first
        if use_cache:
            cached_response = cache_manager.get_cached_models('ollama')
            if cached_response:
                return cached_response

        try:
            # Fetch models from Ollama API
            url = f"{self.base_url}/api/tags"

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        error_data = await response.text()
                        raise APIError(f'Ollama API error: {error_data}')

                    data = await response.json()

            # Process model data
            models = []
            for model_data in data.get('models', []):
                model_id = model_data.get('name', '')

                if not model_id:
                    continue

                # Parse model info
                size_bytes = model_data.get('size', 0)
                size_gb = round(size_bytes / (1024**3), 1) if size_bytes else 0

                # Determine capabilities based on model name
                capabilities = [ModelCapabilities.TEXT_GENERATION]
                supports_tools = False
                multimodal = False
                max_tokens = None

                # Check for specific model types
                model_lower = model_id.lower()
                if 'embed' in model_lower:
                    capabilities = [ModelCapabilities.EMBEDDINGS]
                elif any(x in model_lower for x in ['llama', 'mistral', 'phi']):
                    supports_tools = True
                    max_tokens = 4096  # Default context for most models
                    capabilities.append(ModelCapabilities.TOOLS)

                if 'vision' in model_id.lower() or 'llava' in model_id.lower():
                    multimodal = True
                    capabilities.append(ModelCapabilities.VISION)

                model_info = ModelInfo(
                    id=model_id,
                    name=model_id,
                    provider='ollama',
                    description=f"Ollama local model ({size_gb}GB)",
                    max_tokens=max_tokens,
                    capabilities=capabilities,
                    pricing=ModelPricing(
                        input_price_per_million=0.0,  # Local models are free
                        output_price_per_million=0.0,
                    ),
                    multimodal=multimodal,
                    supports_tools=supports_tools,
                    supports_streaming=True,
                    created_at=model_data.get('modified_at'),
                    updated_at=model_data.get('modified_at'),
                    deprecated=False,
                )
                models.append(model_info)

            # Sort models by name
            models.sort(key=lambda x: x.id)

            response = ModelListResponse(
                provider='ollama', models=models, total_count=len(models), cached=False
            )

            # Cache the response
            cache_manager.cache_models(response)

            self.log_operation('fetched_ollama_models', count=len(models))

            return response

        except Exception as e:
            self.log_error(e, 'failed_to_fetch_ollama_models')
            # Return fallback from config
            return await super().list_models(use_cache=False)
