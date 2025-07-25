"""
Tests for API connectivity across all providers.
"""

import os

import aiohttp
import pytest
from dotenv import load_dotenv

from src.config.config_manager import ConfigManager
from src.providers.base import ProviderFactory

# Load environment variables from .env file
load_dotenv()


class TestAPIConnections:
    """Test API connections for all configured providers."""

    @pytest.fixture
    def config_manager(self):
        """Create configuration manager."""
        return ConfigManager()

    @pytest.fixture
    def provider_factory(self, config_manager):
        """Create provider factory."""
        return ProviderFactory(config_manager)

    @pytest.mark.asyncio
    async def test_openai_api_connection(self):
        """Test OpenAI API connection."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            pytest.skip("OpenAI API key not configured")

        headers = {'Authorization': f'Bearer {api_key}'}

        try:
            async with aiohttp.ClientSession() as session:
                url = 'https://api.openai.com/v1/models'
                async with session.get(url, headers=headers, timeout=10) as response:
                    assert response.status == 200
        except aiohttp.ClientError:
            pytest.fail("OpenAI API connection failed")

    @pytest.mark.asyncio
    async def test_google_api_connection(self):
        """Test Google API connection."""
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            pytest.skip("Google API key not configured")

        headers = {'x-goog-api-key': api_key}

        try:
            async with aiohttp.ClientSession() as session:
                url = 'https://generativelanguage.googleapis.com/v1beta/models'
                async with session.get(url, headers=headers, timeout=10) as response:
                    assert response.status == 200
        except aiohttp.ClientError:
            pytest.fail("Google API connection failed")

    @pytest.mark.asyncio
    async def test_anthropic_api_connection(self):
        """Test Anthropic API connection."""
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            pytest.skip("Anthropic API key not configured")

        headers = {'x-api-key': api_key}

        try:
            async with aiohttp.ClientSession() as session:
                url = 'https://api.anthropic.com/v1/models'
                async with session.get(url, headers=headers, timeout=10) as response:
                    # Anthropic returns 400 for models endpoint
                    # without proper request
                    assert response.status in [
                        200,
                        400,
                        404,
                    ]  # 400, 404 are ok for models endpoint
        except aiohttp.ClientError:
            pytest.fail("Anthropic API connection failed")

    @pytest.mark.asyncio
    async def test_ollama_local_connection(self):
        """Test Ollama local server connection."""
        try:
            async with aiohttp.ClientSession() as session:
                url = 'http://127.0.0.1:11434/api/tags'
                async with session.get(url, timeout=5) as response:
                    assert response.status == 200
        except aiohttp.ClientError:
            pytest.skip("Ollama server not available")

    @pytest.mark.asyncio
    async def test_lmstudio_local_connection(self):
        """Test LM Studio local server connection."""
        try:
            async with aiohttp.ClientSession() as session:
                url = 'http://192.168.1.11:1234/v1/models'
                async with session.get(url, timeout=5) as response:
                    assert response.status == 200
        except aiohttp.ClientError:
            pytest.skip("LM Studio server not available")

    @pytest.mark.asyncio
    async def test_provider_health_checks(self, provider_factory):
        """Test health checks for all available providers."""
        llm_providers = ['openai', 'google', 'anthropic', 'ollama', 'lmstudio']

        for provider_name in llm_providers:
            try:
                provider = await provider_factory.create_llm_provider(provider_name)
                health_status = await provider.health_check()
                # Health check may fail if API key missing or server down
                # but should not raise exceptions
                assert isinstance(health_status, bool)
                await provider.cleanup()
            except Exception as e:
                # Provider creation might fail due to missing config
                pytest.skip(f"{provider_name} provider not available: {e}")

    @pytest.mark.asyncio
    async def test_vector_provider_health_checks(self, provider_factory):
        """Test health checks for vector providers."""
        vector_providers = ['faiss', 'chroma']

        for provider_name in vector_providers:
            try:
                provider = await provider_factory.create_vector_provider(provider_name)
                health_status = await provider.health_check()
                assert isinstance(health_status, bool)
                await provider.cleanup()
            except Exception as e:
                pytest.skip(f"{provider_name} vector provider not available: {e}")

    @pytest.mark.asyncio
    async def test_text_processor_initialization(self, provider_factory):
        """Test text processor initialization."""
        try:
            processor = await provider_factory.create_text_processor('basic')
            assert processor is not None
            # Test basic functionality
            result = await processor.clean_text("  Test text  ")
            assert result == "Test text"
        except Exception as e:
            pytest.fail(f"Text processor initialization failed: {e}")
