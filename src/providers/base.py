"""
Base provider interface and factory for creating providers.
Implements Factory pattern for provider instantiation.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type, TypeVar

from src.config.config_manager import ConfigManager
from src.exceptions import ProviderError
from src.utils.logger import LoggerMixin

T = TypeVar('T', bound='BaseProvider')


class BaseProvider(ABC, LoggerMixin):
    """Base interface for all providers."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get('name', 'unknown')
        # Will be set by factory
        self.config_manager: Optional[ConfigManager] = None

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider."""
        pass

    @abstractmethod
    async def cleanup(self) -> None:
        """Cleanup resources used by the provider."""
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is healthy and available."""
        pass


class LLMProvider(BaseProvider):
    """Base interface for LLM providers."""

    @abstractmethod
    async def generate_text(
        self, prompt: str, model: Optional[str] = None, **kwargs: Any
    ) -> str:
        """Generate text response from prompt."""
        pass

    @abstractmethod
    async def generate_embeddings(
        self, texts: List[str], model: Optional[str] = None
    ) -> List[List[float]]:
        """Generate embedding vectors for texts."""
        pass

    async def generate_embedding(
        self, text: str, model: Optional[str] = None
    ) -> List[float]:
        """Generate embedding vector for single text."""
        results = await self.generate_embeddings([text], model)
        return results[0] if results else []


class VectorDBProvider(BaseProvider):
    """Base interface for vector database providers."""

    @abstractmethod
    async def create_collection(self, collection_name: str) -> None:
        """Create a new collection."""
        pass

    @abstractmethod
    async def add_vectors(
        self,
        collection_name: str,
        vectors: List[List[float]],
        texts: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        """Add vectors to collection."""
        pass

    @abstractmethod
    async def search_vectors(
        self, collection_name: str, query_vector: List[float], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        pass

    @abstractmethod
    async def delete_collection(self, collection_name: str) -> None:
        """Delete a collection."""
        pass


class TextProcessor(BaseProvider):
    """Base interface for text processors."""

    @abstractmethod
    async def chunk_text(
        self, text: str, chunk_size: int = 1000, overlap: int = 200
    ) -> List[str]:
        """Split text into chunks."""
        pass

    @abstractmethod
    async def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        pass


class ProviderFactory(LoggerMixin):
    """Factory for creating provider instances."""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self._llm_providers: Dict[str, Type[LLMProvider]] = {}
        self._vector_providers: Dict[str, Type[VectorDBProvider]] = {}
        self._text_processors: Dict[str, Type[TextProcessor]] = {}
        self._register_default_providers()

    def _register_default_providers(self) -> None:
        """Register default provider implementations."""
        # Import here to avoid circular imports
        try:
            from .llm.openai_provider import OpenAIProvider

            self._llm_providers['openai'] = OpenAIProvider
        except ImportError:
            self.logger.warning('OpenAI provider not available')

        try:
            from .llm.anthropic_provider import AnthropicProvider

            # type: ignore
            self._llm_providers['anthropic'] = AnthropicProvider
        except ImportError:
            self.logger.warning('Anthropic provider not available')

        try:
            from .llm.google_provider import GoogleProvider

            self._llm_providers['google'] = GoogleProvider
        except ImportError:
            self.logger.warning('Google provider not available')

        try:
            from .llm.openrouter_provider import OpenRouterProvider

            self._llm_providers['openrouter'] = OpenRouterProvider
        except ImportError:
            self.logger.warning('OpenRouter provider not available')

        try:
            from .llm.ollama_provider import OllamaProvider

            self._llm_providers['ollama'] = OllamaProvider
        except ImportError:
            self.logger.warning('Ollama provider not available')

        try:
            from .llm.lmstudio_provider import LMStudioProvider

            self._llm_providers['lmstudio'] = LMStudioProvider
        except ImportError:
            self.logger.warning('LM Studio provider not available')

        try:
            from .vector.faiss_provider import FAISSProvider

            self._vector_providers['faiss'] = FAISSProvider
        except ImportError:
            self.logger.warning('FAISS provider not available')

        try:
            from .vector.chroma_provider import ChromaProvider

            self._vector_providers['chroma'] = ChromaProvider
        except ImportError:
            self.logger.warning('Chroma provider not available')

        try:
            from .text.basic_processor import BasicTextProcessor

            self._text_processors['basic'] = BasicTextProcessor
        except ImportError:
            self.logger.warning('Basic text processor not available')

    def register_llm_provider(
        self, name: str, provider_class: Type[LLMProvider]
    ) -> None:
        """Register a new LLM provider."""
        self._llm_providers[name] = provider_class
        self.log_operation('registered_llm_provider', provider=name)

    def register_vector_provider(
        self, name: str, provider_class: Type[VectorDBProvider]
    ) -> None:
        """Register a new vector database provider."""
        self._vector_providers[name] = provider_class
        self.log_operation('registered_vector_provider', provider=name)

    def register_text_processor(
        self, name: str, processor_class: Type[TextProcessor]
    ) -> None:
        """Register a new text processor."""
        self._text_processors[name] = processor_class
        self.log_operation('registered_text_processor', processor=name)

    async def create_llm_provider(self, name: str) -> LLMProvider:
        """Create LLM provider instance."""
        if name not in self._llm_providers:
            raise ProviderError(f'LLM provider {name} not registered')

        config = self.config_manager.get_llm_provider_config(name)
        provider_class = self._llm_providers[name]
        provider = provider_class(config.model_dump())
        provider.config_manager = self.config_manager
        await provider.initialize()

        self.log_operation('created_llm_provider', provider=name)
        return provider

    async def create_vector_provider(self, name: str) -> VectorDBProvider:
        """Create vector database provider instance."""
        if name not in self._vector_providers:
            raise ProviderError(f'Vector provider {name} not registered')

        config = self.config_manager.get_vector_provider_config(name)
        provider_class = self._vector_providers[name]
        provider = provider_class(config.model_dump())
        provider.config_manager = self.config_manager
        await provider.initialize()

        self.log_operation('created_vector_provider', provider=name)
        return provider

    async def create_text_processor(self, name: str = 'basic') -> TextProcessor:
        """Create text processor instance."""
        if name not in self._text_processors:
            raise ProviderError(f'Text processor {name} not registered')

        processor_class = self._text_processors[name]
        processor = processor_class({'name': name})
        await processor.initialize()

        self.log_operation('created_text_processor', processor=name)
        return processor
