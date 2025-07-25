"""
Custom exceptions for RAG_07 application.
Defines application-specific exception hierarchy.
"""


class RAGApplicationError(Exception):
    """Base exception for RAG application errors."""

    pass


class ConfigurationError(RAGApplicationError):
    """Raised when configuration is invalid or missing."""

    pass


class ProviderError(RAGApplicationError):
    """Base exception for provider-related errors."""

    pass


class LLMProviderError(ProviderError):
    """Raised when LLM provider operations fail."""

    pass


class VectorDBError(ProviderError):
    """Raised when vector database operations fail."""

    pass


class TextProcessorError(ProviderError):
    """Raised when text processing operations fail."""

    pass


class APIError(RAGApplicationError):
    """Raised when external API calls fail."""

    def __init__(self, message: str, status_code: int = None, provider: str = None):
        super().__init__(message)
        self.status_code = status_code
        self.provider = provider


class ValidationError(RAGApplicationError):
    """Raised when input validation fails."""

    pass


class RetryExhaustedError(RAGApplicationError):
    """Raised when retry attempts are exhausted."""

    def __init__(self, message: str, attempts: int = None):
        super().__init__(message)
        self.attempts = attempts
