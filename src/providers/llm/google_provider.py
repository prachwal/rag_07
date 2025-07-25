"""
Google Gemini provider implementation for LLM operations.
Handles text generation using Google Generative AI API.
"""

from typing import Any, Dict, List, Optional

import aiohttp

from src.exceptions import APIError, LLMProviderError
from ..base import LLMProvider


class GoogleProvider(LLMProvider):
    """Google Gemini implementation of LLM provider."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize Google provider."""
        super().__init__(config)
        # Initialize type annotations
        self.base_url: str = ""
        self.api_key: str = ""
        self.default_model: str = ""
        self.timeout: int = 30

    async def initialize(self) -> None:
        """Initialize Google provider."""
        if self.config_manager is None:
            raise LLMProviderError(
                'Config manager not set - use ProviderFactory to create providers'
            )

        # At this point config_manager is guaranteed to be not None
        assert self.config_manager is not None

        self.api_key = self.config_manager.get_api_key(self.config['api_key_env'])
        self.base_url = self.config.get(
            'base_url', 'https://generativelanguage.googleapis.com/v1beta'
        )
        self.default_model = self.config.get('default_model', 'gemini-pro')
        self.timeout = self.config.get('timeout', 30)
        self.max_retries = self.config.get('max_retries', 3)

        self.log_operation(
            'initialized_google_provider',
            model=self.default_model,
            base_url=self.base_url,
        )

    async def cleanup(self) -> None:
        """Cleanup Google provider resources."""
        self.log_operation('cleaned_up_google_provider')

    async def health_check(self) -> bool:
        """Check Google provider health."""
        try:
            # Test API connection with a simple model list request
            url = f"{self.base_url}/models"
            headers = {'x-goog-api-key': self.api_key}

            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=10) as response:
                    return response.status == 200
        except Exception as e:
            self.log_error(e, 'google_health_check_failed')
            return False

    async def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> str:
        """Generate text using Google Gemini."""
        model_name = model or self.default_model

        # Build request payload
        payload = {
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {
                'maxOutputTokens': max_tokens or 1000,
                'temperature': temperature or 0.7,
            },
        }

        url = f"{self.base_url}/models/{model_name}:generateContent"
        headers = {'Content-Type': 'application/json', 'x-goog-api-key': self.api_key}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, headers=headers, timeout=self.timeout
                ) as response:
                    response_data = await response.json()

                    if response.status != 200:
                        error_msg = response_data.get('error', {}).get(
                            'message', 'Unknown error'
                        )
                        raise APIError(
                            f'Google API error: {error_msg}', provider='google'
                        )

                    # Extract generated text
                    candidates = response_data.get('candidates', [])
                    if not candidates:
                        raise LLMProviderError('No candidates in Google response')

                    content = candidates[0].get('content', {})
                    parts = content.get('parts', [])
                    if not parts:
                        raise LLMProviderError('No parts in Google response')

                    generated_text = parts[0].get('text', '')

                    self.log_operation(
                        'generated_text',
                        provider='google',
                        model=model_name,
                        prompt_length=len(prompt),
                        response_length=len(generated_text),
                    )

                    return generated_text

        except aiohttp.ClientError as e:
            raise APIError(f'Google request failed: {e}', provider='google') from e
        except KeyError as e:
            raise LLMProviderError(f'Invalid Google response format: {e}') from e

    async def generate_embeddings(
        self, texts: List[str], model: Optional[str] = None
    ) -> List[List[float]]:
        """Generate embeddings using Google API."""
        # Google uses text-embedding-004 for embeddings
        embedding_model = 'text-embedding-004'

        embeddings = []

        for text in texts:
            payload = {
                'model': f'models/{embedding_model}',
                'content': {'parts': [{'text': text}]},
            }

            url = f"{self.base_url}/models/{embedding_model}:embedContent"
            headers = {
                'Content-Type': 'application/json',
                'x-goog-api-key': self.api_key,
            }

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url, json=payload, headers=headers, timeout=self.timeout
                    ) as response:
                        response_data = await response.json()

                        if response.status != 200:
                            error_msg = response_data.get('error', {}).get(
                                'message', 'Unknown error'
                            )
                            raise APIError(
                                f'Google embedding error: {error_msg}',
                                provider='google',
                            )

                        embedding = response_data.get('embedding', {}).get('values', [])
                        if not embedding:
                            raise LLMProviderError('No embedding in Google response')

                        embeddings.append(embedding)

            except aiohttp.ClientError as e:
                raise APIError(
                    f'Google embedding request failed: {e}', provider='google'
                ) from e
            except KeyError as e:
                raise LLMProviderError(f'Invalid Google embedding response: {e}') from e

        self.log_operation(
            'generated_embeddings',
            provider='google',
            texts_count=len(texts),
            embedding_dimension=len(embeddings[0]) if embeddings else 0,
        )

        return embeddings
