"""
Tests for Streamlit web interface.
Tests client functionality and API integration.
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from src.web.streamlit_app import RAGAPIClient


class TestRAGAPIClient:
    """Test RAG API client functionality."""

    def setup_method(self):
        """Set up test client."""
        self.client = RAGAPIClient("http://test-api:8000")

    @patch('requests.get')
    def test_health_check_success(self, mock_get):
        """Test successful health check."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "healthy"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.client.health_check()

        assert result == {"status": "healthy"}
        mock_get.assert_called_once_with("http://test-api:8000/api/health", timeout=5)

    @patch('requests.get')
    def test_health_check_failure(self, mock_get):
        """Test health check failure."""
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        result = self.client.health_check()

        assert result is None

    @patch('requests.get')
    def test_get_available_models_success(self, mock_get):
        """Test successful model retrieval."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "providers": {"openai": ["gpt-4"]},
            "default_providers": {"llm": "openai"},
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = self.client.get_available_models()

        assert "providers" in result
        assert "openai" in result["providers"]

    @patch('requests.post')
    def test_simple_query_success(self, mock_post):
        """Test successful simple query."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "result": "Test response",
            "processing_time": 1.5,
            "provider_used": "openai",
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = self.client.simple_query("Test question", "openai")

        assert result["result"] == "Test response"
        assert result["provider_used"] == "openai"

        mock_post.assert_called_once_with(
            "http://test-api:8000/api/query/simple",
            json={"query": "Test question", "provider": "openai"},
            timeout=60,
        )

    @patch('requests.post')
    def test_rag_query_success(self, mock_post):
        """Test successful RAG query."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "answer": "RAG response",
            "sources_used": ["source1"],
            "function_calls": [],
            "processing_time": 2.0,
            "iterations_used": 1,
            "metadata": {},
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = self.client.rag_query(
            question="What is RAG?", llm_provider="openai", collection="test"
        )

        assert result["answer"] == "RAG response"
        assert result["sources_used"] == ["source1"]

        expected_payload = {
            "question": "What is RAG?",
            "collection": "test",
            "max_results": 5,
            "use_function_calling": True,
            "max_iterations": 5,
            "llm_provider": "openai",
        }

        mock_post.assert_called_once_with(
            "http://test-api:8000/api/query/rag", json=expected_payload, timeout=120
        )

    @patch('requests.post')
    def test_add_text_success(self, mock_post):
        """Test successful text addition."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "document_id": "doc_123",
            "collection": "test",
            "processing_time": 0.5,
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = self.client.add_text("Test content", collection="test")

        assert result["document_id"] == "doc_123"
        assert result["collection"] == "test"

        mock_post.assert_called_once_with(
            "http://test-api:8000/api/vectors/add",
            json={"text": "Test content", "collection": "test"},
            timeout=60,
        )

    @patch('requests.post')
    def test_search_vectors_success(self, mock_post):
        """Test successful vector search."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": ["result1", "result2"],
            "collection": "test",
            "processing_time": 0.3,
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        result = self.client.search_vectors("search query", collection="test")

        assert result["results"] == ["result1", "result2"]
        assert result["collection"] == "test"

        mock_post.assert_called_once_with(
            "http://test-api:8000/api/vectors/search",
            json={"query": "search query", "collection": "test", "limit": 5},
            timeout=30,
        )

    @patch('requests.post')
    def test_api_error_handling(self, mock_post):
        """Test API error handling."""
        mock_post.side_effect = requests.exceptions.RequestException("API Error")

        with patch('streamlit.error') as mock_st_error:
            result = self.client.simple_query("Test")

            assert result is None
            # Streamlit error should be called (if streamlit is available)


class TestStreamlitHelperFunctions:
    """Test helper functions for Streamlit app."""

    def test_session_state_initialization(self):
        """Test session state initialization logic."""
        # This would require mocking streamlit.session_state
        # For now, we'll test the logic conceptually
        from src.web.streamlit_app import initialize_session_state

        # Mock streamlit
        with patch('streamlit.session_state', {}) as mock_session_state:
            with patch('src.web.streamlit_app.RAGAPIClient') as mock_client:
                initialize_session_state()

                # Should initialize required session state variables
                assert 'api_client' in mock_session_state
                assert 'query_count' in mock_session_state
                assert 'conversation_history' in mock_session_state


class TestErrorHandling:
    """Test error handling in Streamlit app."""

    def test_api_connection_failure(self):
        """Test handling of API connection failures."""
        client = RAGAPIClient("http://invalid-url:8000")

        # All methods should return None on connection failure
        assert client.health_check() is None
        assert client.get_available_models() is None
        assert client.simple_query("test") is None
        assert client.rag_query("test") is None
        assert client.add_text("test") is None
        assert client.search_vectors("test") is None


class TestConfiguration:
    """Test configuration handling."""

    def test_api_base_url_configuration(self):
        """Test API base URL configuration."""
        custom_url = "http://custom-api:9000"
        client = RAGAPIClient(custom_url)

        assert client.base_url == custom_url

    def test_default_api_url(self):
        """Test default API URL."""
        client = RAGAPIClient()

        assert client.base_url == "http://localhost:8000"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
