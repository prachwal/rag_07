"""
OpenAI provider implementation for LLM operations.
Handles text generation and embedding using OpenAI API.
"""

from typing import Any, Dict, List, Optional

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


class OpenAIProvider(LLMProvider):
    """OpenAI implementation of LLM provider."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize OpenAI provider."""
        super().__init__(config)
        # Initialize type annotations
        self.session: Any = None
        self.base_url: str = ""
        self.default_model: str = ""

    async def initialize(self) -> None:
        """Initialize OpenAI provider."""
        if self.config_manager is None:
            raise LLMProviderError(
                'Config manager not set - ' 'use ProviderFactory to create providers'
            )

        # At this point config_manager is guaranteed to be not None
        assert self.config_manager is not None

        api_key_env = self.config['api_key_env']
        self.api_key = self.config_manager.get_api_key(api_key_env)
        self.base_url = self.config.get('base_url', 'https://api.openai.com/v1')
        self.default_model = self.config.get('default_model', 'gpt-3.5-turbo')
        self.timeout = self.config.get('timeout', 30)

        if not self.api_key:
            raise LLMProviderError('OpenAI API key is required')

        self.session = aiohttp.ClientSession(
            headers={'Authorization': f'Bearer {self.api_key}'},
            timeout=aiohttp.ClientTimeout(total=self.timeout),
        )

        self.log_operation('initialized_openai_provider')

    async def cleanup(self) -> None:
        """Cleanup OpenAI provider resources."""
        if hasattr(self, 'session'):
            await self.session.close()
        self.log_operation('cleaned_up_openai_provider')

    async def health_check(self) -> bool:
        """Check OpenAI API health."""
        try:
            url = f'{self.base_url}/models'
            async with self.session.get(url) as response:
                return response.status == 200
        except Exception as e:
            self.log_error(e, 'health_check_failed')
            return False

    async def generate_text(
        self, prompt: str, model: Optional[str] = None, **kwargs: Any
    ) -> str:
        """Generate text using OpenAI API."""
        model = model or self.default_model

        payload = {
            'model': model,
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': kwargs.get('max_tokens', 1000),
            'temperature': kwargs.get('temperature', 0.7),
        }

        try:
            url = f'{self.base_url}/chat/completions'
            async with self.session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise APIError(
                        f'OpenAI API error: {error_text}',
                        status_code=response.status,
                        provider='openai',
                    )

                data = await response.json()
                content = data['choices'][0]['message']['content']

                self.log_operation(
                    'generated_text',
                    model=model,
                    prompt_length=len(prompt),
                    response_length=len(content),
                )

                return content

        except aiohttp.ClientError as e:
            raise APIError(f'OpenAI request failed: {e}', provider='openai') from e
        except KeyError as e:
            raise LLMProviderError(f'Invalid OpenAI response format: {e}') from e

    async def generate_embedding(
        self, text: str, model: Optional[str] = None
    ) -> List[float]:
        """Generate embedding using OpenAI API."""
        model = model or 'text-embedding-ada-002'

        payload = {'model': model, 'input': text}

        try:
            url = f'{self.base_url}/embeddings'
            async with self.session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise APIError(
                        f'OpenAI embedding error: {error_text}',
                        status_code=response.status,
                        provider='openai',
                    )

                data = await response.json()
                embedding = data['data'][0]['embedding']

                self.log_operation(
                    'generated_embedding',
                    model=model,
                    text_length=len(text),
                    embedding_dimension=len(embedding),
                )

                return embedding

        except aiohttp.ClientError as e:
            raise APIError(
                f'OpenAI embedding request failed: {e}', provider='openai'
            ) from e
        except KeyError as e:
            raise LLMProviderError(f'Invalid OpenAI embedding response: {e}') from e

    async def generate_embeddings(
        self, texts: List[str], model: Optional[str] = None
    ) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        embeddings = []
        for text in texts:
            embedding = await self.generate_embedding(text, model)
            embeddings.append(embedding)
        return embeddings

    async def list_models(self, use_cache: bool = True) -> ModelListResponse:
        """List available OpenAI models with detailed information."""
        cache_manager = ModelCacheManager()

        # Try to get from cache first
        if use_cache:
            cached_response = cache_manager.get_cached_models('openai')
            if cached_response:
                return cached_response

        try:
            # Fetch models from OpenAI API
            url = f"{self.base_url}/models"
            headers = {'Authorization': f'Bearer {self.api_key}'}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        error_data = await response.json()
                        error_msg = error_data.get('error', {}).get(
                            'message', 'Unknown error'
                        )
                        raise APIError(f'OpenAI API error: {error_msg}')

                    data = await response.json()

            # Process model data
            models = []
            for model_data in data.get('data', []):
                model_id = model_data.get('id', '')

                # Skip if not a valid model
                if not model_id or 'ft:' in model_id:
                    continue

                # Determine capabilities based on model name
                capabilities = [ModelCapabilities.TEXT_GENERATION]
                supports_tools = False
                multimodal = False
                max_tokens = None
                pricing = None

                # Set model-specific attributes
                if any(x in model_id for x in ['gpt-4', 'gpt-3.5']):
                    supports_tools = True
                    if 'gpt-4' in model_id:
                        if 'vision' in model_id or 'gpt-4o' in model_id:
                            multimodal = True
                            capabilities.append(ModelCapabilities.VISION)
                        if 'turbo' in model_id:
                            max_tokens = 128000
                        else:
                            max_tokens = 8192
                        # GPT-4 pricing (approximate)
                        if 'gpt-4o' in model_id:
                            pricing = ModelPricing(
                                input_price_per_million=5.0,
                                output_price_per_million=15.0,
                            )
                        else:
                            pricing = ModelPricing(
                                input_price_per_million=30.0,
                                output_price_per_million=60.0,
                            )
                    else:  # gpt-3.5
                        max_tokens = 16385
                        pricing = ModelPricing(
                            input_price_per_million=0.5, output_price_per_million=1.5
                        )

                    capabilities.append(ModelCapabilities.TOOLS)
                    capabilities.append(ModelCapabilities.FUNCTION_CALLING)

                elif 'text-embedding' in model_id:
                    capabilities = [ModelCapabilities.EMBEDDINGS]
                    if 'ada-002' in model_id:
                        pricing = ModelPricing(
                            input_price_per_million=0.1, output_price_per_million=0.0
                        )

                model_info = ModelInfo(
                    id=model_id,
                    name=model_data.get('id', model_id),
                    provider='openai',
                    description=f"OpenAI {model_id} model",
                    max_tokens=max_tokens,
                    capabilities=capabilities,
                    pricing=pricing,
                    multimodal=multimodal,
                    supports_tools=supports_tools,
                    supports_streaming=True,
                    created_at=None,
                    updated_at=None,
                    deprecated=False,
                )
                models.append(model_info)

            # Sort models by name for consistency
            models.sort(key=lambda x: x.id)

            response = ModelListResponse(
                provider='openai', models=models, total_count=len(models), cached=False
            )

            # Cache the response
            cache_manager.cache_models(response)

            self.log_operation('fetched_openai_models', count=len(models))

            return response

        except Exception as e:
            self.log_error(e, 'failed_to_fetch_openai_models')
            # Return fallback from config
            return await super().list_models(use_cache=False)
