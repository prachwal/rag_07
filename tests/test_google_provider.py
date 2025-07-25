"""
Tests for Google provider.
"""

from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from src.exceptions import APIError
from src.providers.llm.google_provider import GoogleProvider


class TestGoogleProvider:
    """Test Google provider functionality."""

    @pytest.fixture
    def google_config(self):
        """Sample Google provider configuration."""
        return {
            'name': 'google',
            'api_key_env': 'GOOGLE_API_KEY',
            'base_url': 'https://generativelanguage.googleapis.com/v1beta',
            'default_model': 'gemini-pro',
            'timeout': 30,
            'max_retries': 3,
        }

    @pytest.fixture
    def mock_config_manager(self):
        """Mock configuration manager."""
        config_manager = AsyncMock()
        config_manager.get_api_key = lambda x: 'test-api-key'  # Sync method
        return config_manager

    @pytest_asyncio.fixture
    async def google_provider(self, google_config, mock_config_manager):
        """Create Google provider instance."""
        provider = GoogleProvider(google_config)
        provider.config_manager = mock_config_manager
        await provider.initialize()
        return provider

    @pytest.mark.asyncio
    async def test_initialization(self, google_provider):
        """Test Google provider initialization."""
        assert google_provider.api_key == 'test-api-key'
        assert 'generativelanguage.googleapis.com' in google_provider.base_url
        assert google_provider.default_model == 'gemini-pro'

    @pytest.mark.asyncio
    async def test_health_check_success(self, google_provider):
        """Test successful health check."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_get.return_value.__aenter__.return_value = mock_response

            result = await google_provider.health_check()
            assert result is True

    @pytest.mark.asyncio
    async def test_health_check_failure(self, google_provider):
        """Test failed health check."""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 401
            mock_get.return_value.__aenter__.return_value = mock_response

            result = await google_provider.health_check()
            assert result is False

    @pytest.mark.asyncio
    async def test_generate_text_success(self, google_provider):
        """Test successful text generation."""
        mock_response_data = {
            'candidates': [{'content': {'parts': [{'text': 'Generated response'}]}}]
        }

        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_response_data
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await google_provider.generate_text('Test prompt')
            assert result == 'Generated response'

    @pytest.mark.asyncio
    async def test_generate_text_api_error(self, google_provider):
        """Test API error during text generation."""
        mock_response_data = {'error': {'message': 'API quota exceeded'}}

        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 429
            mock_response.json.return_value = mock_response_data
            mock_post.return_value.__aenter__.return_value = mock_response

            with pytest.raises(APIError) as exc_info:
                await google_provider.generate_text('Test prompt')
            assert 'API quota exceeded' in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_generate_embeddings_success(self, google_provider):
        """Test successful embedding generation."""
        mock_response_data = {'embedding': {'values': [0.1, 0.2, 0.3]}}

        with patch('aiohttp.ClientSession.post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = mock_response_data
            mock_post.return_value.__aenter__.return_value = mock_response

            result = await google_provider.generate_embeddings(['test text'])
            assert len(result) == 1
            assert result[0] == [0.1, 0.2, 0.3]
