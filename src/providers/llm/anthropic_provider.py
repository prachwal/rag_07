"""
Anthropic provider implementation for LLM operations.
Provides access to Claude models through Anthropic API.
"""

from typing import Any, Dict, List, Optional

import aiohttp

from src.exceptions import APIError, LLMProviderError

from ..base import LLMProvider


class AnthropicProvider(LLMProvider):
    """Anthropic Claude implementation of LLM provider."""

    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize Anthropic provider."""
        super().__init__(config)
        # Initialize type annotations
        self.base_url: str = ""
        self.api_key: str = ""
        self.default_model: str = ""
        self.timeout: int = 30

    async def initialize(self) -> None:
        """Initialize Anthropic provider."""
        if self.config_manager is None:
            raise LLMProviderError(
                'Config manager not set - ' 'use ProviderFactory to create providers'
            )

        # At this point config_manager is guaranteed to be not None
        assert self.config_manager is not None

        api_key_env = self.config['api_key_env']
        self.api_key = self.config_manager.get_api_key(api_key_env)
        self.base_url = self.config.get('base_url', 'https://api.anthropic.com')
        default_model = 'claude-3-haiku-20240307'
        self.default_model = self.config.get('default_model', default_model)
        self.timeout = self.config.get('timeout', 30)

    async def cleanup(self) -> None:
        """Cleanup resources."""
        pass

    async def health_check(self) -> bool:
        """Check Anthropic provider health."""
        try:
            # Test API connection with a minimal request
            headers = {
                'x-api-key': self.api_key,
                'content-type': 'application/json',
                'anthropic-version': '2023-06-01',
            }

            payload = {
                'model': self.default_model,
                'max_tokens': 1,
                'messages': [{'role': 'user', 'content': 'Hi'}],
            }

            timeout = aiohttp.ClientTimeout(total=10)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                url = f"{self.base_url}/v1/messages"
                async with session.post(url, json=payload, headers=headers) as response:
                    return response.status == 200

        except Exception:
            return False

    async def generate_text(
        self, prompt: str, model: Optional[str] = None, **kwargs: Any
    ) -> str:
        """Generate text using Anthropic API."""
        model_name = model or self.default_model

        headers = {
            'x-api-key': self.api_key,
            'content-type': 'application/json',
            'anthropic-version': '2023-06-01',
        }

        payload = {
            'model': model_name,
            'max_tokens': kwargs.get('max_tokens', 1000),
            'messages': [{'role': 'user', 'content': prompt}],
        }

        try:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                url = f"{self.base_url}/v1/messages"
                async with session.post(url, json=payload, headers=headers) as response:
                    response_data = await response.json()

                    if response.status != 200:
                        error_msg = response_data.get('error', {})
                        error_msg = error_msg.get('message', 'Unknown error')
                        raise APIError(
                            f'Anthropic API error: {error_msg}',
                            provider='anthropic',
                        )

                    # Extract generated text
                    content = response_data.get('content', [])
                    if not content or not content[0].get('text'):
                        raise LLMProviderError('No content in Anthropic response')

                    return content[0]['text']

        except aiohttp.ClientError as e:
            raise APIError(
                f'Anthropic request failed: {e}', provider='anthropic'
            ) from e
        except KeyError as e:
            raise LLMProviderError(f'Invalid Anthropic response format: {e}') from e

    async def generate_embeddings(
        self, texts: List[str], model: Optional[str] = None
    ) -> List[List[float]]:
        """Generate embeddings (not supported by Anthropic)."""
        raise NotImplementedError(
            'Anthropic does not support embeddings. '
            'Use OpenAI or Google providers for embeddings.'
        )

    async def generate_embedding(
        self, text: str, model: Optional[str] = None
    ) -> List[float]:
        """Generate embedding (not supported by Anthropic)."""
        raise NotImplementedError(
            'Anthropic does not support embeddings. '
            'Use OpenAI or Google providers for embeddings.'
        )
