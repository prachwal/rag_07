"""
Tests for FastAPI web interface.
Tests API endpoints and integration with application services.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.web.api_server import app


@pytest.fixture
def client():
    """Create test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_config_manager():
    """Mock configuration manager."""
    mock_config = MagicMock()
    mock_config.config.default_llm_provider = "openai"
    mock_config.config.default_vector_provider = "faiss"
    return mock_config


@pytest.fixture
def mock_application_service():
    """Mock application service."""
    service = MagicMock()

    # Mock async methods
    service.process_query = AsyncMock(return_value="Test response")
    service.advanced_rag_query = AsyncMock(
        return_value={
            "answer": "Test RAG response",
            "sources_used": ["source1", "source2"],
            "function_calls": [],
            "iterations_used": 1,
            "metadata": {"traditional_rag_used": True},
        }
    )
    service.add_to_vector_store = AsyncMock(return_value="doc_123")
    service.search_vector_store = AsyncMock(return_value=["result1", "result2"])

    return service


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check_success(self, client):
        """Test successful health check."""
        with patch("src.web.api_server.api_server.config_manager") as mock_config:
            mock_config.config.default_llm_provider = "openai"
            mock_config.config.default_vector_provider = "faiss"

            response = client.get("/api/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["service"] == "RAG_07 API"
            assert data["version"] == "1.0.0"

    def test_health_check_no_config(self, client):
        """Test health check without configuration."""
        with patch("src.web.api_server.api_server.config_manager", None):
            response = client.get("/api/health")

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"


class TestModelsEndpoint:
    """Test models listing endpoint."""

    def test_get_available_models(self, client):
        """Test getting available models."""
        with patch("src.web.api_server.api_server.config_manager") as mock_config:
            mock_config.config.default_llm_provider = "openai"
            mock_config.config.default_vector_provider = "faiss"

            response = client.get("/api/models")

            assert response.status_code == 200
            data = response.json()
            assert "providers" in data
            assert "openai" in data["providers"]
            assert "anthropic" in data["providers"]
            assert "default_providers" in data


class TestSimpleQueryEndpoint:
    """Test simple query endpoint."""

    def test_simple_query_success(self, client, mock_application_service):
        """Test successful simple query."""
        with patch(
            "src.web.api_server.api_server.application_service",
            mock_application_service,
        ):
            payload = {"query": "Test question", "provider": "openai"}

            response = client.post("/api/query/simple", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["result"] == "Test response"
            assert "processing_time" in data
            assert data["provider_used"] == "openai"

            mock_application_service.process_query.assert_called_once_with(
                query="Test question", provider="openai", model=None
            )

    def test_simple_query_empty(self, client):
        """Test simple query with empty text."""
        payload = {"query": ""}

        response = client.post("/api/query/simple", json=payload)

        assert response.status_code == 400

    def test_simple_query_missing_field(self, client):
        """Test simple query with missing required field."""
        payload = {}

        response = client.post("/api/query/simple", json=payload)

        assert response.status_code == 422  # Validation error


class TestRAGQueryEndpoint:
    """Test RAG query endpoint."""

    def test_rag_query_success(self, client, mock_application_service):
        """Test successful RAG query."""
        with patch(
            "src.web.api_server.api_server.application_service",
            mock_application_service,
        ):
            payload = {
                "question": "What is RAG?",
                "llm_provider": "openai",
                "vector_provider": "faiss",
                "collection": "default",
                "max_results": 5,
                "use_function_calling": True,
                "max_iterations": 3,
            }

            response = client.post("/api/query/rag", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["answer"] == "Test RAG response"
            assert data["sources_used"] == ["source1", "source2"]
            assert "processing_time" in data
            assert data["iterations_used"] == 1

            mock_application_service.advanced_rag_query.assert_called_once_with(
                question="What is RAG?",
                llm_provider="openai",
                vector_provider="faiss",
                collection="default",
                use_function_calling=True,
                max_iterations=3,
            )

    def test_rag_query_minimal(self, client, mock_application_service):
        """Test RAG query with minimal payload."""
        with patch(
            "src.web.api_server.api_server.application_service",
            mock_application_service,
        ):
            payload = {"question": "Test question"}

            response = client.post("/api/query/rag", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["answer"] == "Test RAG response"


class TestVectorEndpoints:
    """Test vector database endpoints."""

    def test_add_text_success(self, client, mock_application_service):
        """Test successful text addition."""
        with patch(
            "src.web.api_server.api_server.application_service",
            mock_application_service,
        ):
            payload = {"text": "Test document content", "collection": "test_collection"}

            response = client.post("/api/vectors/add", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["document_id"] == "doc_123"
            assert data["collection"] == "test_collection"
            assert "processing_time" in data

            mock_application_service.add_to_vector_store.assert_called_once_with(
                text="Test document content",
                provider=None,
                collection="test_collection",
            )

    def test_search_vectors_success(self, client, mock_application_service):
        """Test successful vector search."""
        with patch(
            "src.web.api_server.api_server.application_service",
            mock_application_service,
        ):
            payload = {
                "query": "search query",
                "collection": "test_collection",
                "limit": 3,
            }

            response = client.post("/api/vectors/search", json=payload)

            assert response.status_code == 200
            data = response.json()
            assert data["results"] == ["result1", "result2"]
            assert data["collection"] == "test_collection"
            assert "processing_time" in data

            mock_application_service.search_vector_store.assert_called_once_with(
                query="search query",
                provider=None,
                collection="test_collection",
                limit=3,
            )


class TestErrorHandling:
    """Test error handling."""

    def test_validation_error_handling(self, client):
        """Test validation error handling."""
        with patch("src.web.api_server.api_server.application_service") as mock_service:
            from src.exceptions import ValidationError

            mock_service.process_query.side_effect = ValidationError("Invalid input")

            payload = {"query": "test"}
            response = client.post("/api/query/simple", json=payload)

            assert response.status_code == 400
            data = response.json()
            assert data["error"] == "ValidationError"
            assert data["message"] == "Invalid input"

    def test_internal_error_handling(self, client):
        """Test internal error handling."""
        with patch("src.web.api_server.api_server.application_service") as mock_service:
            mock_service.process_query.side_effect = Exception("Internal error")

            payload = {"query": "test"}
            response = client.post("/api/query/simple", json=payload)

            assert response.status_code == 500


@pytest.mark.asyncio
class TestStartupShutdown:
    """Test application startup and shutdown events."""

    async def test_startup_event(self):
        """Test startup event initialization."""
        from src.web.api_server import api_server

        with patch("src.config.config_manager.ConfigManager") as mock_config_class:
            with patch(
                "src.services.application_service.ApplicationService"
            ) as mock_service_class:
                mock_config = MagicMock()
                mock_config.initialize = AsyncMock()
                mock_config_class.return_value = mock_config

                await api_server._startup_event()

                assert api_server.config_manager is not None
                assert api_server.application_service is not None
                mock_config.initialize.assert_called_once()

    async def test_shutdown_event(self):
        """Test shutdown event cleanup."""
        from src.web.api_server import api_server

        # Should not raise any exceptions
        await api_server._shutdown_event()


class TestIntegration:
    """Integration tests."""

    def test_full_workflow(self, client):
        """Test complete workflow: health -> models -> query."""
        # Health check
        response = client.get("/api/health")
        assert response.status_code == 200

        # Get models
        response = client.get("/api/models")
        assert response.status_code == 200

        # Simple query (will fail without proper mocking, but tests routing)
        payload = {"query": "test"}
        response = client.post("/api/query/simple", json=payload)
        # We expect this to fail in test environment, which is fine
        assert response.status_code in [500, 400]  # Either server error or validation


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
