"""
Tests for configuration manager.
"""

import json
import tempfile
from pathlib import Path

import pytest

from src.config.config_manager import AppConfig, ConfigManager
from src.exceptions import ConfigurationError


class TestConfigManager:
    """Test configuration manager functionality."""

    def test_default_config_creation(self):
        """Test creation of default configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / 'test_config.json'
            config_manager = ConfigManager(config_file)

            assert config_file.exists()
            assert config_manager.config.app_name == 'rag_07'
            assert len(config_manager.config.llm_providers) > 0
            assert len(config_manager.config.vector_providers) > 0

    def test_config_loading_from_file(self):
        """Test loading configuration from existing file."""
        test_config = {
            'app_name': 'test_app',
            'debug': True,
            'log_level': 'DEBUG',
            'default_llm_provider': 'test_llm',
            'default_vector_provider': 'test_vector',
            'llm_providers': [],
            'vector_providers': [],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / 'test_config.json'
            with open(config_file, 'w') as f:
                json.dump(test_config, f)

            config_manager = ConfigManager(config_file)
            assert config_manager.config.app_name == 'test_app'
            assert config_manager.config.debug is True

    def test_invalid_config_raises_error(self):
        """Test that invalid configuration raises error."""
        invalid_config = {
            'app_name': 123,  # Should be string
            'llm_providers': 'invalid',  # Should be list
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / 'invalid_config.json'
            with open(config_file, 'w') as f:
                json.dump(invalid_config, f)

            # Just check that ConfigurationError is raised
            with pytest.raises(ConfigurationError) as exc_info:
                ConfigManager(config_file)
            # Verify it's actually a config error, not something else
            assert "Invalid configuration" in str(exc_info.value)

    def test_get_available_providers(self):
        """Test getting available providers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / 'test_config.json'
            config_manager = ConfigManager(config_file)

            llm_providers = config_manager.get_available_llm_providers()
            vector_providers = config_manager.get_available_vector_providers()

            assert isinstance(llm_providers, list)
            assert isinstance(vector_providers, list)
            assert 'openai' in llm_providers
            assert 'faiss' in vector_providers

    def test_get_status(self):
        """Test getting configuration status."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / 'test_config.json'
            config_manager = ConfigManager(config_file)

            status = config_manager.get_status()

            assert 'config_file' in status
            assert 'llm_providers' in status
            assert 'vector_providers' in status
            assert 'default_llm_provider' in status
