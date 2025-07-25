"""
FastAPI backend for RAG_07.
Provides RESTful API endpoints for RAG operations and model management.
"""

import asyncio
import time
from typing import Dict, List

import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.config.config_manager import ConfigManager
from src.exceptions import ValidationError
from src.services.application_service import ApplicationService
from src.utils.logger import LoggerMixin
from src.web.models import (
    AddTextRequest,
    AddTextResponse,
    ErrorResponse,
    HealthResponse,
    ModelsResponse,
    QueryRequest,
    QueryResponse,
    SearchVectorRequest,
    SearchVectorResponse,
    SimpleQueryRequest,
    SimpleQueryResponse,
)


class RAGAPIServer(LoggerMixin):
    """FastAPI server for RAG_07 operations."""

    def __init__(self):
        """Initialize the API server."""
        self.app = FastAPI(
            title="RAG_07 API",
            description="Multi-provider LLM and RAG system API",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc",
        )

        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure properly for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self.config_manager: ConfigManager = None
        self.application_service: ApplicationService = None

        # Register routes
        self._register_routes()

        # Register startup and shutdown events
        self.app.add_event_handler("startup", self._startup_event)
        self.app.add_event_handler("shutdown", self._shutdown_event)

    def _register_routes(self):
        """Register API routes."""

        @self.app.exception_handler(ValidationError)
        async def validation_exception_handler(request, exc):
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=ErrorResponse(error="ValidationError", message=str(exc)).dict(),
            )

        @self.app.exception_handler(Exception)
        async def general_exception_handler(request, exc):
            self.logger.error(f"Unhandled exception: {exc}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=ErrorResponse(
                    error="InternalServerError",
                    message="An unexpected error occurred",
                ).dict(),
            )

        @self.app.get("/api/health", response_model=HealthResponse)
        async def health_check():
            """Health check endpoint."""
            try:
                providers_status = {}
                if self.config_manager:
                    config = self.config_manager.config
                    providers_status = {
                        "llm_provider": config.default_llm_provider,
                        "vector_provider": config.default_vector_provider,
                    }

                return HealthResponse(
                    status="healthy",
                    service="RAG_07 API",
                    version="1.0.0",
                    providers_status=providers_status,
                )
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Health check failed: {str(e)}"
                )

        @self.app.get("/api/models", response_model=ModelsResponse)
        async def get_available_models():
            """Get available models from all providers."""
            try:
                # Use cached models from ModelCacheManager
                from src.utils.model_cache import ModelCacheManager

                cache_manager = ModelCacheManager()
                providers = cache_manager.get_all_cached_models()

                # Only use fallback for providers that actually exist in cache
                # but have no compatible models
                cached_providers = cache_manager.list_cached_providers()

                # Add fallback only for cached providers with no compatible models
                for provider in cached_providers:
                    if provider not in providers:
                        # Provider exists but no compatible models found
                        # Add a minimal fallback
                        if provider == "openai":
                            providers[provider] = ["gpt-3.5-turbo", "gpt-4"]
                        elif provider == "anthropic":
                            providers[provider] = [
                                "claude-3-5-sonnet",
                                "claude-3-haiku",
                            ]
                        elif provider == "google":
                            providers[provider] = ["gemini-1.5-flash", "gemini-1.5-pro"]
                        elif provider == "ollama":
                            providers[provider] = ["llama2", "mistral"]
                        elif provider == "openrouter":
                            providers[provider] = [
                                "openai/gpt-4",
                                "anthropic/claude-3.5-sonnet",
                            ]

                default_providers = {}
                if self.config_manager:
                    config = self.config_manager.config
                    default_providers = {
                        "llm": config.default_llm_provider,
                        "vector": config.default_vector_provider,
                    }

                return ModelsResponse(
                    providers=providers, default_providers=default_providers
                )
            except Exception as e:
                raise HTTPException(
                    status_code=500, detail=f"Failed to get models: {str(e)}"
                )

        @self.app.post("/api/query/simple", response_model=SimpleQueryResponse)
        async def simple_query(request: SimpleQueryRequest):
            """Process a simple LLM query without RAG."""
            try:
                start_time = time.time()

                result = await self.application_service.process_query(
                    query=request.query,
                    provider=request.provider,
                    model=request.model,
                )

                processing_time = time.time() - start_time
                provider_used = (
                    request.provider or self.config_manager.config.default_llm_provider
                )

                return SimpleQueryResponse(
                    result=result,
                    processing_time=processing_time,
                    provider_used=provider_used,
                    model_used=request.model,
                )
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                self.logger.error(f"Simple query failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/query/rag", response_model=QueryResponse)
        async def rag_query(request: QueryRequest):
            """Process a RAG query with context retrieval."""
            try:
                start_time = time.time()

                result = await self.application_service.advanced_rag_query(
                    question=request.question,
                    llm_provider=request.llm_provider,
                    llm_model=request.llm_model,
                    vector_provider=request.vector_provider,
                    collection=request.collection,
                    use_function_calling=request.use_function_calling,
                    max_iterations=request.max_iterations,
                )

                processing_time = time.time() - start_time

                return QueryResponse(
                    answer=result["answer"],
                    sources_used=result.get("sources_used", []),
                    function_calls=result.get("function_calls", []),
                    processing_time=processing_time,
                    iterations_used=result.get("iterations_used", 1),
                    metadata=result.get("metadata", {}),
                )
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                self.logger.error(f"RAG query failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/vectors/add", response_model=AddTextResponse)
        async def add_text_to_vectors(request: AddTextRequest):
            """Add text to vector database."""
            try:
                start_time = time.time()

                document_id = await self.application_service.add_to_vector_store(
                    text=request.text,
                    provider=request.provider,
                    collection=request.collection,
                )

                processing_time = time.time() - start_time
                collection = request.collection or "default"

                return AddTextResponse(
                    document_id=document_id,
                    collection=collection,
                    processing_time=processing_time,
                )
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                self.logger.error(f"Add text failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/api/vectors/search", response_model=SearchVectorResponse)
        async def search_vectors(request: SearchVectorRequest):
            """Search in vector database."""
            try:
                start_time = time.time()

                results = await self.application_service.search_vector_store(
                    query=request.query,
                    provider=request.provider,
                    collection=request.collection,
                    limit=request.limit,
                )

                processing_time = time.time() - start_time
                collection = request.collection or "default"

                return SearchVectorResponse(
                    results=results,
                    processing_time=processing_time,
                    collection=collection,
                )
            except ValidationError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                self.logger.error(f"Vector search failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    async def _startup_event(self):
        """Initialize services on startup."""
        try:
            self.logger.info("🚀 Starting RAG_07 API Server...")

            # Initialize configuration
            self.config_manager = ConfigManager()

            # Initialize application service
            self.application_service = ApplicationService(self.config_manager)

            self.logger.info("✅ RAG_07 API Server initialized successfully")
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize API server: {e}")
            raise

    async def _shutdown_event(self):
        """Cleanup on shutdown."""
        try:
            self.logger.info("🛑 Shutting down RAG_07 API Server...")
            # Add any cleanup logic here
            self.logger.info("✅ API Server shutdown completed")
        except Exception as e:
            self.logger.error(f"❌ Error during shutdown: {e}")

    def run(self, host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
        """Run the FastAPI server."""
        uvicorn.run(
            "src.web.api_server:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info",
        )


# Create FastAPI app instance
api_server = RAGAPIServer()
app = api_server.app

if __name__ == "__main__":
    # For development - use reload
    api_server.run(reload=True)
