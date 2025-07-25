"""
Chroma provider implementation for vector database operations.
Handles vector storage and similarity search using ChromaDB.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from src.exceptions import VectorDBError

from ..base import VectorDBProvider


class ChromaProvider(VectorDBProvider):
    """Chroma implementation of vector database provider."""

    async def initialize(self) -> None:
        """Initialize Chroma provider."""
        try:
            import chromadb

            self.chromadb = chromadb
        except ImportError:
            raise VectorDBError(
                'ChromaDB library not installed. Install with: pip install chromadb'
            )

        self.storage_path = Path(self.config.get('storage_path', 'databases/chroma_db'))
        self.dimension = self.config.get('dimension', 1536)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Initialize Chroma client
        self.client = self.chromadb.PersistentClient(path=str(self.storage_path))

        self.log_operation(
            'initialized_chroma_provider', storage_path=str(self.storage_path)
        )

    async def cleanup(self) -> None:
        """Cleanup Chroma provider resources."""
        # Chroma handles cleanup automatically
        self.log_operation('cleaned_up_chroma_provider')

    async def health_check(self) -> bool:
        """Check Chroma provider health."""
        try:
            # Test basic Chroma functionality
            _ = self.client.get_or_create_collection(name="health_check_test")
            # Delete the test collection
            self.client.delete_collection(name="health_check_test")
            return True
        except Exception as e:
            self.log_error(e, 'chroma_health_check_failed')
            return False

    async def create_collection(self, collection_name: str) -> None:
        """Create a new collection."""
        try:
            self.client.create_collection(name=collection_name)
            self.log_operation('created_collection', collection=collection_name)
        except Exception as e:
            if "already exists" in str(e):
                self.log_operation(
                    'collection_already_exists', collection=collection_name
                )
            else:
                raise VectorDBError(f'Failed to create collection: {e}')

    async def add_vectors(
        self,
        collection_name: str,
        vectors: List[List[float]],
        texts: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        """Add vectors to collection."""
        try:
            collection = self.client.get_collection(name=collection_name)
        except Exception:
            # Collection doesn't exist, create it
            await self.create_collection(collection_name)
            collection = self.client.get_collection(name=collection_name)

        # Generate IDs
        existing_count = collection.count()
        ids = [f'{collection_name}_{existing_count + i}' for i in range(len(vectors))]

        # Prepare metadata
        if metadata is None:
            metadata = [{'id': i} for i in range(len(texts))]
        else:
            # Ensure each metadata dict has at least one key
            for i, meta in enumerate(metadata):
                if not meta or len(meta) == 0:
                    metadata[i] = {'id': i}

        # Add to collection
        collection.add(  # type: ignore
            embeddings=vectors, documents=texts, metadatas=metadata, ids=ids
        )

        self.log_operation(
            'added_vectors',
            collection=collection_name,
            count=len(vectors),
            total_vectors=collection.count(),
        )

        return ids

    async def search_vectors(
        self, collection_name: str, query_vector: List[float], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        try:
            collection = self.client.get_collection(name=collection_name)
        except Exception:
            raise VectorDBError(f'Collection {collection_name} does not exist')

        # Perform search
        results = collection.query(  # type: ignore
            query_embeddings=[query_vector], n_results=limit
        )

        # Format results
        formatted_results = []
        if results['ids'] and results['ids'][0]:
            for i, doc_id in enumerate(results['ids'][0]):
                result = {
                    'id': doc_id,
                    'text': results['documents'][0][i] if results['documents'] else '',
                    'distance': (
                        results['distances'][0][i] if results['distances'] else 0.0
                    ),
                    'metadata': (
                        results['metadatas'][0][i] if results['metadatas'] else {}
                    ),
                }
                formatted_results.append(result)

        self.log_operation(
            'searched_vectors',
            collection=collection_name,
            query_length=len(query_vector),
            results_count=len(formatted_results),
        )

        return formatted_results

    async def delete_collection(self, collection_name: str) -> None:
        """Delete a collection."""
        try:
            self.client.delete_collection(name=collection_name)
            self.log_operation('deleted_collection', collection=collection_name)
        except Exception as e:
            raise VectorDBError(f'Failed to delete collection: {e}')

    async def list_collections(self) -> List[str]:
        """List all collections."""
        try:
            collections = self.client.list_collections()
            return [collection.name for collection in collections]
        except Exception as e:
            raise VectorDBError(f'Failed to list collections: {e}')

    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get information about a collection."""
        try:
            collection = self.client.get_collection(name=collection_name)
            count = collection.count()

            # Get dimension from configuration or first vector
            dimension = self.dimension
            if count > 0:
                # Try to get actual dimension from first vector
                try:
                    result = collection.get(limit=1, include=['embeddings'])
                    if result['embeddings'] and len(result['embeddings']) > 0:
                        dimension = len(result['embeddings'][0])
                except Exception:
                    # Fallback to config dimension
                    pass

            return {
                'name': collection_name,
                'count': count,
                'dimension': dimension,
                'metadata': collection.metadata,
            }
        except Exception as e:
            raise VectorDBError(f'Failed to get collection info: {e}')

    async def browse_vectors(
        self, collection_name: str, offset: int = 0, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Browse vectors in a collection."""
        try:
            collection = self.client.get_collection(name=collection_name)
        except Exception:
            raise VectorDBError(f'Collection {collection_name} does not exist')

        # Get total count
        total_count = collection.count()

        if offset >= total_count:
            return []

        # ChromaDB doesn't have direct pagination, so we get all and slice
        # For large collections, this could be optimized
        results = collection.get(include=['documents', 'metadatas', 'embeddings'])

        if not results['ids']:
            return []

        # Apply pagination
        end_idx = min(offset + limit, len(results['ids']))
        formatted_results = []

        for i in range(offset, end_idx):
            if i < len(results['ids']):
                result = {
                    'id': results['ids'][i],
                    'text': (results['documents'][i] if results['documents'] else ''),
                    'metadata': (
                        results['metadatas'][i] if results['metadatas'] else {}
                    ),
                    'index': i,
                }
                formatted_results.append(result)

        self.log_operation(
            'browsed_vectors',
            collection=collection_name,
            offset=offset,
            limit=limit,
            results_count=len(formatted_results),
            total_count=total_count,
        )

        return formatted_results

    async def get_document_by_id(
        self, document_id: str, collection_name: str = "default"
    ) -> Optional[Dict[str, Any]]:
        """Get document by ID from Chroma collection.

        Args:
            document_id: The document identifier to retrieve
            collection_name: Name of the collection to search in

        Returns:
            Document data including text and metadata, or None if not found
        """
        try:
            # Get or create collection
            collection = self.client.get_collection(name=collection_name)

            # Get document by ID
            results = collection.get(
                ids=[document_id], include=['documents', 'metadatas']
            )

            if not results['ids'] or len(results['ids']) == 0:
                self.log_operation(
                    "get_document_by_id_not_found",
                    document_id=document_id,
                    collection=collection_name,
                )
                return None

            # Format result
            result = {
                "id": document_id,
                "text": results['documents'][0] if results['documents'] else "",
                "metadata": results['metadatas'][0] if results['metadatas'] else {},
                "collection": collection_name,
            }

            self.log_operation(
                "get_document_by_id_success",
                document_id=document_id,
                collection=collection_name,
                text_length=len(result["text"]),
            )

            return result

        except Exception as e:
            error_msg = f"Document retrieval error: {str(e)}"
            self.log_operation(
                "get_document_by_id_error",
                document_id=document_id,
                collection=collection_name,
                error=error_msg,
            )
            return None
