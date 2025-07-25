"""
Tests for Anthropic provider.
"""

from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from src.exceptions import APIError
from src.providers.llm.anthropic_provider import AnthropicProvider


class TestAnthropicProvider:
    """Test Anthropic provider functionality."""

    @pytest.fixture
    def anthropic_config(self):
        """Sample Anthropic provider configuration."""
        return {
            'name': 'anthropic',
            'api_key_env': 'ANTHROPIC_API_KEY',
            'base_url': 'https://api.anthropic.com',
            'default_model': 'claude-3-sonnet-20240229',
            'timeout': 30,
            'max_retries': 3,
        }

    @pytest.fixture
    def mock_config_manager(self):
        """Mock configuration manager."""
        config_manager = AsyncMock()
        config_manager.get_api_key = lambda x: 'test-api-key'
        return config_manager

    @pytest_asyncio.fixture
    async def anthropic_provider(self, anthropic_config, mock_config_manager):
        """Create Anthropic provider instance."""
        provider = AnthropicProvider(anthropic_config)
        provider.config_manager = mock_config_manager
        await provider.initialize()
        return provider

    @pytest.mark.asyncio
    async def test_initialization(self, anthropic_provider):
        """Test Anthropic provider initialization."""
        assert anthropic_provider.api_key == 'test-api-key'
        assert 'api.anthropic.com' in anthropic_provider.base_url
        assert anthropic_provider.default_model == 'claude-3-sonnet-20240229'

    @pytest.mark.asyncio
    async def test_health_check_success(self, anthropic_provider):
        """Test successful health check."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await anthropic_provider.health_check()
            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, anthropic_provider):
        """Test failed health check."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 401
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await anthropic_provider.health_check()
            assert result is False

    @pytest.mark.asyncio
    async def test_generate_text_success(self, anthropic_provider):
        """Test successful text generation."""
        mock_response_data = {'content': [{'text': 'Generated response'}]}

        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_response_data
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await anthropic_provider.generate_text('Test prompt')
            assert result == 'Generated response'

    @pytest.mark.asyncio
    async def test_generate_text_api_error(self, anthropic_provider):
        """Test API error during text generation."""
        mock_response_data = {'error': {'message': 'API quota exceeded'}}

        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 429
            mock_response.json.return_value = mock_response_data
            mock_post.return_value.__aenter__.return_value = mock_response

            with pytest.raises(APIError) as exc_info:
                await anthropic_provider.generate_text('Test prompt')
            assert 'API quota exceeded' in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_embeddings(self, anthropic_provider):
        """Test embedding generation (should raise NotImplementedError)."""
        with pytest.raises(NotImplementedError) as exc_info:
            await anthropic_provider.generate_embeddings(['test text'])
        assert 'Anthropic does not support embeddings' in str(exc_info.value)
