"""
Anthropic provider implementation for LLM operations.
Provides access to Claude models through Anthropic API.
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

    async def chat_completion_with_functions(
        self,
        messages: List[Dict[str, Any]],
        functions: List[Dict[str, Any]],
        function_call: str = "auto",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Generate chat completion with function calling support.

        Note: Anthropic uses "tools" instead of "functions".
        This method converts OpenAI-style functions to Anthropic tools.
        """
        if not await self.health_check():
            raise LLMProviderError('Anthropic provider is not healthy')

        model = kwargs.get('model', self.default_model)

        # Convert OpenAI-style functions to Anthropic tools
        tools = []
        for func in functions:
            tool = {
                "name": func["name"],
                "description": func["description"],
                "input_schema": func["parameters"],
            }
            tools.append(tool)

        # Convert messages format
        anthropic_messages = []
        system_message = None

        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            elif msg["role"] == "function":
                # Convert function result to tool result
                anthropic_messages.append(
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": msg.get("name", "unknown"),
                                "content": msg["content"],
                            }
                        ],
                    }
                )
            else:
                anthropic_messages.append(
                    {"role": msg["role"], "content": msg["content"]}
                )

        # Build payload
        payload = {
            "model": model,
            "messages": anthropic_messages,
            "tools": tools,
            "max_tokens": kwargs.get('max_tokens', 2000),
            "temperature": kwargs.get('temperature', 0.1),
        }

        if system_message:
            payload["system"] = system_message

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
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

                    # Convert Anthropic response to OpenAI format
                    content = response_data.get('content', [])
                    if not content:
                        raise LLMProviderError('No content in Anthropic response')

                    # Build OpenAI-compatible response
                    message = {"role": "assistant", "content": None}

                    # Handle text content
                    text_content = []
                    tool_calls = []

                    for item in content:
                        if item.get('type') == 'text':
                            text_content.append(item.get('text', ''))
                        elif item.get('type') == 'tool_use':
                            # Convert to OpenAI function call format
                            tool_calls.append(
                                {
                                    "name": item.get('name'),
                                    "arguments": item.get('input', {}),
                                }
                            )

                    if text_content:
                        message["content"] = '\n'.join(text_content)

                    if tool_calls and len(tool_calls) > 0:
                        # Use first tool call (Anthropic can return multiple)
                        message["function_call"] = tool_calls[0]

                    self.log_operation(
                        'chat_completion_with_functions',
                        model=model,
                        messages_count=len(messages),
                        tools_count=len(tools),
                    )

                    return {"choices": [{"message": message}]}

        except aiohttp.ClientError as e:
            raise APIError(
                f'Anthropic request failed: {e}', provider='anthropic'
            ) from e
        except KeyError as e:
            raise LLMProviderError(f'Invalid Anthropic response format: {e}') from e

    def supports_function_calling(self) -> bool:
        """Check if provider supports function calling."""
        # Claude 3 models support tool use (function calling)
        claude_3_models = [
            'claude-3-opus',
            'claude-3-sonnet',
            'claude-3-haiku',
            'claude-3-5-sonnet',
        ]
        return any(model in self.default_model for model in claude_3_models)

    async def list_models(self, use_cache: bool = True) -> ModelListResponse:
        """List available models from Anthropic API."""
        cache_manager = ModelCacheManager()

        # Try to get cached models first if use_cache is True
        if use_cache:
            cached_response = cache_manager.get_cached_models('anthropic')
            if cached_response:
                return cached_response

        try:
            headers = {
                'x-api-key': self.api_key,
                'content-type': 'application/json',
                'anthropic-version': '2023-06-01',
            }

            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                url = f"{self.base_url}/v1/models"
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise APIError(
                            f'Anthropic API error: {error_text}', provider='anthropic'
                        )

                    data = await response.json()
                    models = []

                    for model_data in data.get('data', []):
                        model_id = model_data.get('id', '')
                        display_name = model_data.get('display_name', model_id)

                        # Determine capabilities based on model name
                        capabilities = [ModelCapabilities.TEXT_GENERATION]
                        multimodal = False
                        supports_tools = True  # Most Claude models support

                        if 'vision' in model_id.lower():
                            capabilities.append(ModelCapabilities.VISION)
                            multimodal = True

                        if supports_tools:
                            capabilities.extend(
                                [
                                    ModelCapabilities.TOOLS,
                                    ModelCapabilities.FUNCTION_CALLING,
                                ]
                            )

                        # Estimate context length based on model name
                        max_tokens = None
                        if 'claude-3' in model_id:
                            max_tokens = 200000  # 200k context
                        elif 'claude-2' in model_id:
                            max_tokens = 100000  # 100k context

                        # Add pricing information for known models
                        pricing = None
                        if 'claude-3-haiku' in model_id:
                            pricing = ModelPricing(
                                input_price_per_million=0.25,
                                output_price_per_million=1.25,
                                currency="USD",
                            )
                        elif (
                            'claude-3.5-sonnet' in model_id
                            or 'claude-3-sonnet' in model_id
                        ):
                            pricing = ModelPricing(
                                input_price_per_million=3.0,
                                output_price_per_million=15.0,
                                currency="USD",
                            )
                        elif 'claude-3-opus' in model_id:
                            pricing = ModelPricing(
                                input_price_per_million=15.0,
                                output_price_per_million=75.0,
                                currency="USD",
                            )

                        model_info = ModelInfo(
                            id=model_id,
                            name=display_name,
                            provider='anthropic',
                            description=f"Anthropic {display_name} model",
                            max_tokens=max_tokens,
                            capabilities=capabilities,
                            multimodal=multimodal,
                            supports_tools=supports_tools,
                            supports_streaming=True,
                            created_at=model_data.get('created_at'),
                            updated_at=None,
                            deprecated=False,
                            pricing=pricing,
                        )
                        models.append(model_info)

                    response_obj = ModelListResponse(
                        provider='anthropic', models=models, total_count=len(models)
                    )

                    # Cache the response
                    cache_manager.cache_models(response_obj)

                    self.logger.info(
                        "Fetched Anthropic models",
                        extra={
                            "operation": "fetched_anthropic_models",
                            "count": len(models),
                        },
                    )

                    return response_obj

        except aiohttp.ClientError as e:
            raise APIError(
                f'Anthropic request failed: {e}', provider='anthropic'
            ) from e
        except Exception as e:
            raise LLMProviderError(f'Failed to list Anthropic models: {e}') from e
