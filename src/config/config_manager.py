"""
Configuration manager for RAG_07 application.
Handles loading and managing configuration from .env and config files.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from src.exceptions import ConfigurationError
from src.utils.logger import LoggerMixin


class LLMProviderConfig(BaseModel):
    """Configuration for LLM provider."""

    name: str
    api_key_env: str
    base_url: Optional[str] = None
    default_model: str
    available_models: List[str] = Field(default_factory=list)
    timeout: int = 30
    max_retries: int = 3


class VectorDBConfig(BaseModel):
    """Configuration for Vector Database provider."""

    name: str
    storage_path: Optional[str] = None
    api_key_env: Optional[str] = None
    base_url: Optional[str] = None
    default_collection: str = 'default'
    dimension: int = 1536


class AppConfig(BaseModel):
    """Main application configuration."""

    app_name: str = 'rag_07'
    debug: bool = False
    log_level: str = 'INFO'
    default_llm_provider: str = 'openai'
    default_vector_provider: str = 'faiss'
    llm_providers: List[LLMProviderConfig] = Field(default_factory=list)
    vector_providers: List[VectorDBConfig] = Field(default_factory=list)


class ConfigManager(LoggerMixin):
    """Manages application configuration from multiple sources."""

    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file or Path('config/app_config.json')
        self.config: AppConfig = self._load_config()

    def _load_config(self) -> AppConfig:
        """Load configuration from file and environment."""
        # Load environment variables
        load_dotenv()

        # Load config file if exists, otherwise create default
        if self.config_file.exists():
            self.log_operation('loading_config', file=str(self.config_file))
            with open(self.config_file, 'r') as f:
                config_data = json.load(f)
        else:
            self.log_operation('creating_default_config', file=str(self.config_file))
            config_data = self._get_default_config()
            self._save_default_config(config_data)

        try:
            return AppConfig(**config_data)
        except Exception as e:
            raise ConfigurationError(f'Invalid configuration: {e}') from e

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration structure."""
        return {
            'app_name': 'rag_07',
            'debug': False,
            'log_level': 'INFO',
            'default_llm_provider': 'openai',
            'default_vector_provider': 'faiss',
            'llm_providers': [
                {
                    'name': 'openai',
                    'api_key_env': 'OPENAI_API_KEY',
                    'base_url': 'https://api.openai.com/v1',
                    'default_model': 'gpt-3.5-turbo',
                    'available_models': ['gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo'],
                    'timeout': 30,
                    'max_retries': 3,
                },
                {
                    'name': 'anthropic',
                    'api_key_env': 'ANTHROPIC_API_KEY',
                    'base_url': 'https://api.anthropic.com',
                    'default_model': 'claude-3-sonnet-20240229',
                    'available_models': [
                        'claude-3-haiku-20240307',
                        'claude-3-sonnet-20240229',
                        'claude-3-opus-20240229',
                    ],
                    'timeout': 30,
                    'max_retries': 3,
                },
            ],
            'vector_providers': [
                {
                    'name': 'faiss',
                    'storage_path': 'databases/faiss_index',
                    'default_collection': 'default',
                    'dimension': 1536,
                },
                {
                    'name': 'chroma',
                    'storage_path': 'databases/chroma_db',
                    'default_collection': 'default',
                    'dimension': 1536,
                },
            ],
        }

    def _save_default_config(self, config_data: Dict[str, Any]) -> None:
        """Save default configuration to file."""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            json.dump(config_data, f, indent=2)

    def get_llm_provider_config(self, provider_name: str) -> LLMProviderConfig:
        """Get configuration for specific LLM provider."""
        for provider in self.config.llm_providers:
            if provider.name == provider_name:
                return provider
        raise ConfigurationError(f'LLM provider {provider_name} not configured')

    def get_vector_provider_config(self, provider_name: str) -> VectorDBConfig:
        """Get configuration for specific vector DB provider."""
        for provider in self.config.vector_providers:
            if provider.name == provider_name:
                return provider
        raise ConfigurationError(f'Vector provider {provider_name} not configured')

    def get_api_key(self, env_var_name: str) -> str:
        """Get API key from environment variables."""
        api_key = os.getenv(env_var_name)
        if not api_key:
            raise ConfigurationError(f'API key {env_var_name} not found in environment')
        return api_key

    def get_available_llm_providers(self) -> List[str]:
        """Get list of available LLM providers."""
        return [provider.name for provider in self.config.llm_providers]

    def get_available_vector_providers(self) -> List[str]:
        """Get list of available vector DB providers."""
        return [provider.name for provider in self.config.vector_providers]

    def get_status(self) -> Dict[str, Any]:
        """Get configuration status information."""
        return {
            'config_file': str(self.config_file),
            'llm_providers': self.get_available_llm_providers(),
            'vector_providers': self.get_available_vector_providers(),
            'default_llm_provider': self.config.default_llm_provider,
            'default_vector_provider': self.config.default_vector_provider,
            'debug': self.config.debug,
            'log_level': self.config.log_level,
        }
