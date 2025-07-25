"""
OpenAI provider implementation for LLM operations.
Handles text generation and embedding using OpenAI API.
"""

from typing import Any, Dict, List, Optional

import aiohttp

from src.exceptions import APIError, LLMProviderError
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
