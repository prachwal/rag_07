"""
FAISS provider implementation for vector database operations.
Handles vector storage and similarity search using Facebook's FAISS library.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from src.exceptions import VectorDBError
from ..base import VectorDBProvider


class FAISSProvider(VectorDBProvider):
    """FAISS implementation of vector database provider."""

    async def initialize(self) -> None:
        """Initialize FAISS provider."""
        try:
            import faiss

            self.faiss = faiss
        except ImportError:
            raise VectorDBError(
                'FAISS library not installed. Install with: pip install faiss-cpu'
            )

        self.storage_path = Path(
            self.config.get('storage_path', 'databases/faiss_index')
        )
        self.dimension = self.config.get('dimension', 1536)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # In-memory storage for collections
        self.collections: Dict[str, Any] = {}
        self._load_existing_collections()

        self.log_operation(
            'initialized_faiss_provider', storage_path=str(self.storage_path)
        )

    async def cleanup(self) -> None:
        """Cleanup FAISS provider resources."""
        await self._save_all_collections()
        self.log_operation('cleaned_up_faiss_provider')

    async def health_check(self) -> bool:
        """Check FAISS provider health."""
        try:
            # Test FAISS functionality
            test_index = self.faiss.IndexFlatL2(128)
            test_vector = np.random.random((1, 128)).astype('float32')
            test_index.add(test_vector)
            return test_index.ntotal == 1
        except Exception as e:
            self.log_error(e, 'faiss_health_check_failed')
            return False

    def _load_existing_collections(self) -> None:
        """Load existing collections from disk."""
        for collection_file in self.storage_path.glob('*.index'):
            collection_name = collection_file.stem
            try:
                self._load_collection(collection_name)
                self.log_operation('loaded_collection', collection=collection_name)
            except Exception as e:
                self.log_error(
                    e, 'failed_to_load_collection', collection=collection_name
                )

    def _load_collection(self, collection_name: str) -> None:
        """Load a specific collection from disk."""
        index_path = self.storage_path / f'{collection_name}.index'
        metadata_path = self.storage_path / f'{collection_name}_metadata.json'

        if index_path.exists():
            index = self.faiss.read_index(str(index_path))
            metadata = {}

            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)

            self.collections[collection_name] = {
                'index': index,
                'metadata': metadata.get('texts', []),
                'extra_metadata': metadata.get('extra_metadata', []),
            }

    async def _save_collection(self, collection_name: str) -> None:
        """Save a collection to disk."""
        if collection_name not in self.collections:
            return

        collection = self.collections[collection_name]
        index_path = self.storage_path / f'{collection_name}.index'
        metadata_path = self.storage_path / f'{collection_name}_metadata.json'

        # Save index
        self.faiss.write_index(collection['index'], str(index_path))

        # Save metadata
        metadata = {
            'texts': collection['metadata'],
            'extra_metadata': collection['extra_metadata'],
        }
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

    async def _save_all_collections(self) -> None:
        """Save all collections to disk."""
        for collection_name in self.collections:
            await self._save_collection(collection_name)

    async def create_collection(self, collection_name: str) -> None:
        """Create a new collection."""
        if collection_name in self.collections:
            self.log_operation('collection_already_exists', collection=collection_name)
            return

        index = self.faiss.IndexFlatL2(self.dimension)
        self.collections[collection_name] = {
            'index': index,
            'metadata': [],
            'extra_metadata': [],
        }

        await self._save_collection(collection_name)
        self.log_operation('created_collection', collection=collection_name)

    async def add_vectors(
        self,
        collection_name: str,
        vectors: List[List[float]],
        texts: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        """Add vectors to collection."""
        if collection_name not in self.collections:
            await self.create_collection(collection_name)

        collection = self.collections[collection_name]

        # Convert to numpy array
        vectors_array = np.array(vectors, dtype='float32')

        # Add to index
        start_id = collection['index'].ntotal
        collection['index'].add(vectors_array)

        # Add metadata
        collection['metadata'].extend(texts)
        if metadata:
            collection['extra_metadata'].extend(metadata)
        else:
            collection['extra_metadata'].extend([{}] * len(texts))

        # Generate IDs
        ids = [f'{collection_name}_{start_id + i}' for i in range(len(vectors))]

        await self._save_collection(collection_name)

        self.log_operation(
            'added_vectors',
            collection=collection_name,
            count=len(vectors),
            total_vectors=collection['index'].ntotal,
        )

        return ids

    async def search_vectors(
        self, collection_name: str, query_vector: List[float], limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        if collection_name not in self.collections:
            raise VectorDBError(f'Collection {collection_name} does not exist')

        collection = self.collections[collection_name]

        if collection['index'].ntotal == 0:
            return []

        # Convert query to numpy array
        query_array = np.array([query_vector], dtype='float32')

        # Search
        distances, indices = collection['index'].search(
            query_array, min(limit, collection['index'].ntotal)
        )

        results = []
        for distance, idx in zip(distances[0], indices[0]):
            if idx >= 0:  # Valid index
                result = {
                    'id': f'{collection_name}_{idx}',
                    'text': collection['metadata'][idx],
                    'distance': float(distance),
                    'metadata': collection['extra_metadata'][idx],
                }
                results.append(result)

        self.log_operation(
            'searched_vectors',
            collection=collection_name,
            query_length=len(query_vector),
            results_count=len(results),
        )

        return results

    async def delete_collection(self, collection_name: str) -> None:
        """Delete a collection."""
        if collection_name in self.collections:
            del self.collections[collection_name]

        # Remove files
        index_path = self.storage_path / f'{collection_name}.index'
        metadata_path = self.storage_path / f'{collection_name}_metadata.json'

        index_path.unlink(missing_ok=True)
        metadata_path.unlink(missing_ok=True)

        self.log_operation('deleted_collection', collection=collection_name)

    async def list_collections(self) -> List[str]:
        """List all collections."""
        try:
            collections = list(self.collections.keys())
            return collections
        except Exception as e:
            raise VectorDBError(f'Failed to list collections: {e}')

    async def get_collection_info(self, collection_name: str) -> Dict[str, Any]:
        """Get information about a collection."""
        if collection_name not in self.collections:
            raise VectorDBError(f'Collection {collection_name} does not exist')

        collection = self.collections[collection_name]
        return {
            'name': collection_name,
            'count': collection['index'].ntotal,
            'dimension': collection['index'].d,
            'metadata_count': len(collection['metadata']),
        }

    async def browse_vectors(
        self, collection_name: str, offset: int = 0, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Browse vectors in a collection."""
        if collection_name not in self.collections:
            raise VectorDBError(f'Collection {collection_name} does not exist')

        collection = self.collections[collection_name]
        total_count = collection['index'].ntotal

        if offset >= total_count:
            return []

        end_idx = min(offset + limit, total_count)
        results = []

        for i in range(offset, end_idx):
            if i < len(collection['metadata']):
                result = {
                    'id': f'{collection_name}_{i}',
                    'text': collection['metadata'][i],
                    'metadata': (
                        collection['extra_metadata'][i]
                        if i < len(collection['extra_metadata'])
                        else {}
                    ),
                    'index': i,
                }
                results.append(result)

        return results
