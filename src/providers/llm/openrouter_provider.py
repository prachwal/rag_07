"""
OpenRouter provider implementation for LLM operations.
Provides access to multiple LLM models through OpenRouter API.
"""

from typing import Any, Dict, List, Optional

import aiohttp

from src.exceptions import APIError, LLMProviderError
from ..base import LLMProvider


class OpenRouterProvider(LLMProvider):
    """OpenRouter LLM provider implementation."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize OpenRouter provider."""
        super().__init__(config)
        # Initialize type annotations
        self.api_key: str = ""
        self.base_url: str = ""
        self.default_model: str = ""
        self.timeout: int = 30

    async def initialize(self) -> None:
        """Initialize OpenRouter provider."""
        if self.config_manager is None:
            raise LLMProviderError(
                'Config manager not set - ' 'use ProviderFactory to create providers'
            )

        # At this point config_manager is guaranteed to be not None
        assert self.config_manager is not None

        api_key_env = self.config['api_key_env']
        self.api_key = self.config_manager.get_api_key(api_key_env)
        base_url = 'https://openrouter.ai/api/v1'
        self.base_url = self.config.get('base_url', base_url)
        default_model = 'anthropic/claude-3-sonnet'
        self.default_model = self.config.get('default_model', default_model)
        self.timeout = self.config.get('timeout', 30)
        self.max_retries = self.config.get('max_retries', 3)

        self.log_operation(
            'initialized_openrouter_provider',
            model=self.default_model,
            base_url=self.base_url,
        )

    async def cleanup(self) -> None:
        """Cleanup OpenRouter provider resources."""
        self.log_operation('cleaned_up_openrouter_provider')

    async def health_check(self) -> bool:
        """Check OpenRouter provider health."""
        try:
            # Test API connection
            url = f"{self.base_url}/models"
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'HTTP-Referer': 'http://localhost:8000',
                'X-Title': 'RAG_07',
            }

            async with aiohttp.ClientSession() as session:
                timeout = aiohttp.ClientTimeout(total=10)
                async with session.get(
                    url, headers=headers, timeout=timeout
                ) as response:
                    return response.status == 200
        except Exception as e:
            self.log_error(e, 'openrouter_health_check_failed')
            return False

    async def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> str:
        """Generate text using OpenRouter."""
        model_name = model or self.default_model

        # Build request payload (OpenAI-compatible format)
        payload = {
            'model': model_name,
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': max_tokens or 1000,
            'temperature': temperature or 0.7,
        }

        url = f"{self.base_url}/chat/completions"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'HTTP-Referer': 'http://localhost:8000',
            'X-Title': 'RAG_07',
        }

        try:
            async with aiohttp.ClientSession() as session:
                timeout = aiohttp.ClientTimeout(total=self.timeout)
                async with session.post(
                    url, json=payload, headers=headers, timeout=timeout
                ) as response:
                    response_data = await response.json()

                    if response.status != 200:
                        error_msg = response_data.get('error', {})
                        error_msg = error_msg.get('message', 'Unknown error')
                        raise APIError(
                            f'OpenRouter API error: {error_msg}', provider='openrouter'
                        )

                    # Extract generated text
                    choices = response_data.get('choices', [])
                    if not choices:
                        raise LLMProviderError('No choices in OpenRouter response')

                    message = choices[0].get('message', {})
                    generated_text = message.get('content', '')

                    self.log_operation(
                        'generated_text',
                        provider='openrouter',
                        model=model_name,
                        prompt_length=len(prompt),
                        response_length=len(generated_text),
                    )

                    return generated_text

        except aiohttp.ClientError as e:
            error_msg = f'OpenRouter request failed: {e}'
            raise APIError(error_msg, provider='openrouter') from e
        except KeyError as e:
            error_msg = f'Invalid OpenRouter response format: {e}'
            raise LLMProviderError(error_msg) from e

    async def generate_embeddings(
        self, texts: List[str], model: Optional[str] = None
    ) -> List[List[float]]:
        """Generate embeddings using OpenRouter."""
        # OpenRouter may not support embeddings for all models
        # Use OpenAI format for supported models
        embedding_model = 'openai/text-embedding-ada-002'

        embeddings = []

        for text in texts:
            payload = {'model': embedding_model, 'input': text}

            url = f"{self.base_url}/embeddings"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}',
                'HTTP-Referer': 'http://localhost:8000',
                'X-Title': 'RAG_07',
            }

            try:
                async with aiohttp.ClientSession() as session:
                    timeout = aiohttp.ClientTimeout(total=self.timeout)
                    async with session.post(
                        url, json=payload, headers=headers, timeout=timeout
                    ) as response:
                        response_data = await response.json()

                        if response.status != 200:
                            error_msg = response_data.get('error', {})
                            error_msg = error_msg.get('message', 'Unknown error')
                            raise APIError(
                                f'OpenRouter embedding error: {error_msg}',
                                provider='openrouter',
                            )

                        data = response_data.get('data', [])
                        if not data:
                            raise LLMProviderError(
                                'No embedding data in OpenRouter response'
                            )

                        embedding = data[0].get('embedding', [])
                        embeddings.append(embedding)

            except aiohttp.ClientError as e:
                error_msg = f'OpenRouter embedding request failed: {e}'
                raise APIError(error_msg, provider='openrouter') from e
            except KeyError as e:
                error_msg = f'Invalid OpenRouter embedding response: {e}'
                raise LLMProviderError(error_msg) from e

        self.log_operation(
            'generated_embeddings',
            provider='openrouter',
            texts_count=len(texts),
            embedding_dimension=len(embeddings[0]) if embeddings else 0,
        )

        return embeddings
