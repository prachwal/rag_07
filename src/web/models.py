"""
Pydantic models for FastAPI endpoints.
Defines request/response schemas for RAG_07 API.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request model for RAG query."""

    question: str = Field(..., description="User question to be answered")
    llm_provider: Optional[str] = Field(None, description="LLM provider to use")
    llm_model: Optional[str] = Field(None, description="Specific LLM model to use")
    vector_provider: Optional[str] = Field(
        None, description="Vector DB provider to use"
    )
    collection: Optional[str] = Field("default", description="Collection name")
    max_results: int = Field(
        5, ge=1, le=20, description="Maximum number of context results"
    )
    use_function_calling: bool = Field(
        True, description="Whether to use function calling"
    )
    max_iterations: int = Field(
        5, ge=1, le=10, description="Maximum function calling iterations"
    )


class QueryResponse(BaseModel):
    """Response model for RAG query."""

    answer: str = Field(..., description="Generated answer")
    sources_used: List[str] = Field(
        default_factory=list, description="Sources used in context"
    )
    function_calls: List[Dict[str, Any]] = Field(
        default_factory=list, description="Function calls made"
    )
    processing_time: float = Field(..., description="Processing time in seconds")
    iterations_used: int = Field(..., description="Number of iterations used")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class SimpleQueryRequest(BaseModel):
    """Request model for simple LLM query."""

    query: str = Field(..., description="Query text")
    provider: Optional[str] = Field(None, description="LLM provider to use")
    model: Optional[str] = Field(None, description="Specific model to use")


class SimpleQueryResponse(BaseModel):
    """Response model for simple LLM query."""

    result: str = Field(..., description="Generated text")
    processing_time: float = Field(..., description="Processing time in seconds")
    provider_used: str = Field(..., description="Provider used for generation")
    model_used: Optional[str] = Field(None, description="Model used for generation")


class AddTextRequest(BaseModel):
    """Request model for adding text to vector store."""

    text: str = Field(..., description="Text to add to vector store")
    provider: Optional[str] = Field(None, description="Vector DB provider to use")
    collection: Optional[str] = Field("default", description="Collection name")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Optional metadata")


class AddTextResponse(BaseModel):
    """Response model for adding text to vector store."""

    document_id: str = Field(..., description="ID of added document")
    collection: str = Field(..., description="Collection name where text was added")
    processing_time: float = Field(..., description="Processing time in seconds")


class SearchVectorRequest(BaseModel):
    """Request model for vector search."""

    query: str = Field(..., description="Search query")
    provider: Optional[str] = Field(None, description="Vector DB provider to use")
    collection: Optional[str] = Field("default", description="Collection name")
    limit: int = Field(5, ge=1, le=20, description="Maximum number of results")


class SearchVectorResponse(BaseModel):
    """Response model for vector search."""

    results: List[str] = Field(..., description="Search results")
    processing_time: float = Field(..., description="Processing time in seconds")
    collection: str = Field(..., description="Collection searched")


class ModelsResponse(BaseModel):
    """Response model for available models."""

    providers: Dict[str, List[str]] = Field(
        ..., description="Available models by provider"
    )
    default_providers: Dict[str, str] = Field(
        ..., description="Default providers configuration"
    )


class HealthResponse(BaseModel):
    """Response model for health check."""

    status: str = Field(..., description="Service status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    providers_status: Dict[str, str] = Field(
        default_factory=dict, description="Provider statuses"
    )


class ErrorResponse(BaseModel):
    """Response model for errors."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )
