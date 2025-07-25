"""
Vector search tools for function calling.
Provides search functions that can be called by LLM.
"""

from typing import Any, Dict, List, Optional

from src.providers.base import LLMProvider, VectorDBProvider
from src.utils.logger import LoggerMixin


class VectorSearchTools(LoggerMixin):
    """Tools for vector-based document search and retrieval."""

    def __init__(self, vector_provider: VectorDBProvider, llm_provider: LLMProvider):
        """Initialize vector search tools.

        Args:
            vector_provider: Vector database provider instance
            llm_provider: LLM provider for embedding generation
        """
        self.vector_provider = vector_provider
        self.llm_provider = llm_provider

    def get_function_definitions(self) -> List[Dict[str, Any]]:
        """Return OpenAI-compatible function definitions."""
        return [
            {
                "name": "search_documents",
                "description": (
                    "Search for relevant documents in the knowledge base. "
                    "Use this function to find information related to the "
                    "user's question."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": (
                                "Search query for finding relevant documents. "
                                "Should be descriptive and specific."
                            ),
                        },
                        "max_results": {
                            "type": "integer",
                            "description": (
                                "Maximum number of results to return "
                                "(default: 5, max: 20)"
                            ),
                            "default": 5,
                            "minimum": 1,
                            "maximum": 20,
                        },
                        "collection": {
                            "type": "string",
                            "description": (
                                "Collection name to search in. "
                                "Leave empty for default collection."
                            ),
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "get_document_details",
                "description": (
                    "Get detailed information about a specific document "
                    "by its ID. Use this to get more context about a "
                    "document found in search results."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "document_id": {
                            "type": "string",
                            "description": "Document ID to get details for",
                        },
                        "include_metadata": {
                            "type": "boolean",
                            "description": (
                                "Whether to include document metadata "
                                "(default: true)"
                            ),
                            "default": True,
                        },
                    },
                    "required": ["document_id"],
                },
            },
        ]

    async def search_documents(
        self, query: str, max_results: int = 5, collection: Optional[str] = None
    ) -> Dict[str, Any]:
        """Execute document search in vector database.

        Args:
            query: Search query string
            max_results: Maximum number of results to return
            collection: Collection name (optional)

        Returns:
            Dictionary with search results or error information
        """
        try:
            # Validate inputs
            if not query.strip():
                return {"status": "error", "message": "Query cannot be empty"}

            if max_results < 1 or max_results > 20:
                max_results = min(max(max_results, 1), 20)

            # Generate embedding for query
            self.log_operation(
                "search_documents_started",
                query_length=len(query),
                max_results=max_results,
                collection=collection,
            )

            query_embedding = await self.llm_provider.generate_embedding(query)

            # Search vectors
            collection_name = collection or "default"
            results = await self.vector_provider.search_vectors(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=max_results,
            )

            # Format results for LLM consumption
            formatted_results = []
            for i, result in enumerate(results):
                formatted_result = {
                    "rank": i + 1,
                    "content": result.get("text", ""),
                    "relevance_score": round(result.get("score", 0.0), 4),
                    "document_id": result.get("id", f"doc_{i}"),
                    "source": result.get("metadata", {}).get("source", "unknown"),
                }

                # Include snippet of content for preview
                content = formatted_result["content"]
                if len(content) > 200:
                    formatted_result["content_preview"] = content[:200] + "..."
                    formatted_result["full_content"] = content
                else:
                    formatted_result["content_preview"] = content

                formatted_results.append(formatted_result)

            self.log_operation(
                "search_documents_completed",
                query=query,
                results_found=len(formatted_results),
                collection=collection_name,
            )

            return {
                "status": "success",
                "query": query,
                "results": formatted_results,
                "total_found": len(formatted_results),
                "collection": collection_name,
                "search_metadata": {
                    "embedding_model": "default",
                    "search_type": "vector_similarity",
                },
            }

        except Exception as e:
            error_msg = f"Search error: {str(e)}"
            self.log_operation("search_documents_error", query=query, error=error_msg)

            return {"status": "error", "message": error_msg, "query": query}

    async def get_document_details(
        self, document_id: str, include_metadata: bool = True
    ) -> Dict[str, Any]:
        """Get detailed information about a specific document.

        Args:
            document_id: ID of the document to retrieve
            include_metadata: Whether to include metadata

        Returns:
            Dictionary with document details or error information
        """
        try:
            if not document_id.strip():
                return {"status": "error", "message": "Document ID cannot be empty"}

            self.log_operation(
                "get_document_details_started",
                document_id=document_id,
                include_metadata=include_metadata,
            )

            # Try to get document details from vector provider
            # Note: This assumes vector provider has a method to get by ID
            # Implementation depends on specific vector provider capabilities

            if hasattr(self.vector_provider, 'get_document_by_id'):
                document = await self.vector_provider.get_document_by_id(document_id)

                if not document:
                    return {
                        "status": "error",
                        "message": f"Document not found: {document_id}",
                    }

                result = {
                    "status": "success",
                    "document_id": document_id,
                    "content": document.get("text", ""),
                    "found": True,
                }

                if include_metadata and "metadata" in document:
                    result["metadata"] = document["metadata"]

                self.log_operation(
                    "get_document_details_completed", document_id=document_id
                )

                return result
            else:
                # Fallback: search for document by ID in metadata
                return {
                    "status": "error",
                    "message": (
                        "Document details retrieval not supported "
                        "by current vector provider"
                    ),
                }

        except Exception as e:
            error_msg = f"Document retrieval error: {str(e)}"
            self.log_operation(
                "get_document_details_error", document_id=document_id, error=error_msg
            )

            return {"status": "error", "message": error_msg, "document_id": document_id}
