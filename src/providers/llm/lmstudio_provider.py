"""
LM Studio provider implementation for local LLM operations.
Handles text generation using LM Studio local server.
"""

from typing import Any, List, Optional

import aiohttp

from src.exceptions import APIError, LLMProviderError
from ..base import LLMProvider


class LMStudioProvider(LLMProvider):
    """LM Studio implementation of LLM provider."""

    async def initialize(self) -> None:
        """Initialize LM Studio provider."""
        # LM Studio uses OpenAI-compatible API
        default_url = 'http://192.168.1.11:1234/v1'
        self.base_url = self.config.get('base_url', default_url)
        self.default_model = self.config.get('default_model', 'local-model')
        self.timeout = self.config.get('timeout', 60)  # Longer timeout
        self.max_retries = self.config.get('max_retries', 3)

        self.log_operation(
            'initialized_lmstudio_provider',
            model=self.default_model,
            base_url=self.base_url,
        )

    async def cleanup(self) -> None:
        """Cleanup LM Studio provider resources."""
        self.log_operation('cleaned_up_lmstudio_provider')

    async def health_check(self) -> bool:
        """Check LM Studio provider health."""
        try:
            # Test LM Studio server connection
            url = f"{self.base_url}/models"

            async with aiohttp.ClientSession() as session:
                timeout = aiohttp.ClientTimeout(total=10)
                async with session.get(url, timeout=timeout) as response:
                    return response.status == 200
        except Exception as e:
            self.log_error(e, 'lmstudio_health_check_failed')
            return False

    async def generate_text(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs: Any,
    ) -> str:
        """Generate text using LM Studio."""
        model_name = model or self.default_model

        # Build OpenAI-compatible request payload
        payload = {
            'model': model_name,
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': max_tokens or 1000,
            'temperature': temperature or 0.7,
            'stream': False,
        }

        url = f"{self.base_url}/chat/completions"
        headers = {'Content-Type': 'application/json'}

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
                            f'LM Studio API error: {error_msg}', provider='lmstudio'
                        )

                    # Extract generated text (OpenAI format)
                    choices = response_data.get('choices', [])
                    if not choices:
                        raise LLMProviderError('No choices in LM Studio response')

                    message = choices[0].get('message', {})
                    generated_text = message.get('content', '')

                    self.log_operation(
                        'generated_text',
                        provider='lmstudio',
                        model=model_name,
                        prompt_length=len(prompt),
                        response_length=len(generated_text),
                    )

                    return generated_text

        except aiohttp.ClientError as e:
            error_msg = f'LM Studio request failed: {e}'
            raise APIError(error_msg, provider='lmstudio') from e
        except KeyError as e:
            error_msg = f'Invalid LM Studio response format: {e}'
            raise LLMProviderError(error_msg) from e

    async def generate_embeddings(
        self, texts: List[str], model: Optional[str] = None
    ) -> List[List[float]]:
        """Generate embeddings using LM Studio."""
        # LM Studio may support embeddings endpoint
        embedding_model = model or 'text-embedding-ada-002'

        embeddings = []

        for text in texts:
            payload = {'model': embedding_model, 'input': text}

            url = f"{self.base_url}/embeddings"
            headers = {'Content-Type': 'application/json'}

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
                                f'LM Studio embedding error: {error_msg}',
                                provider='lmstudio',
                            )

                        data = response_data.get('data', [])
                        if not data:
                            raise LLMProviderError(
                                'No embedding data in LM Studio response'
                            )

                        embedding = data[0].get('embedding', [])
                        embeddings.append(embedding)

            except aiohttp.ClientError as e:
                error_msg = f'LM Studio embedding request failed: {e}'
                raise APIError(error_msg, provider='lmstudio') from e
            except KeyError as e:
                error_msg = f'Invalid LM Studio embedding response: {e}'
                raise LLMProviderError(error_msg) from e

        self.log_operation(
            'generated_embeddings',
            provider='lmstudio',
            texts_count=len(texts),
            embedding_dimension=len(embeddings[0]) if embeddings else 0,
        )

        return embeddings
