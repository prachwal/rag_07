"""
Tests for FAISS vector provider.
"""

import tempfile
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

from src.exceptions import VectorDBError
from src.providers.vector.faiss_provider import FAISSProvider


class TestFAISSProvider:
    """Test FAISS provider functionality."""

    @pytest.fixture
    def faiss_config(self):
        """Sample FAISS provider configuration."""
        return {
            'name': 'faiss',
            'storage_path': 'test_databases/faiss_test',
            'dimension': 384,
        }

    @pytest.fixture
    def mock_config_manager(self):
        """Mock configuration manager."""
        config_manager = AsyncMock()
        return config_manager

    @pytest_asyncio.fixture
    async def faiss_provider(self, faiss_config, mock_config_manager):
        """Create FAISS provider instance."""
        # Use temporary directory for tests
        with tempfile.TemporaryDirectory() as temp_dir:
            faiss_config['storage_path'] = temp_dir
            provider = FAISSProvider(faiss_config)
            provider.config_manager = mock_config_manager
            await provider.initialize()
            yield provider
            await provider.cleanup()

    @pytest.mark.asyncio
    async def test_initialization(self, faiss_provider):
        """Test FAISS provider initialization."""
        assert faiss_provider.dimension == 384
        assert faiss_provider.storage_path.exists()
        assert hasattr(faiss_provider, 'faiss')

    @pytest.mark.asyncio
    async def test_health_check_success(self, faiss_provider):
        """Test successful health check."""
        result = await faiss_provider.health_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_create_collection(self, faiss_provider):
        """Test collection creation."""
        collection_name = 'test_collection'
        await faiss_provider.create_collection(collection_name)

        assert collection_name in faiss_provider.collections
        collection = faiss_provider.collections[collection_name]
        assert collection['index'].d == 384  # dimension
        assert collection['index'].ntotal == 0  # no vectors yet

    @pytest.mark.asyncio
    async def test_add_vectors(self, faiss_provider):
        """Test adding vectors to collection."""
        collection_name = 'test_collection'

        # Test vectors (384 dimensions to match config)
        vectors = [
            [0.1] * 384,
            [0.2] * 384,
            [0.3] * 384,
        ]
        texts = ['text1', 'text2', 'text3']
        metadata = [
            {'source': 'doc1'},
            {'source': 'doc2'},
            {'source': 'doc3'},
        ]

        ids = await faiss_provider.add_vectors(
            collection_name, vectors, texts, metadata
        )

        assert len(ids) == 3
        assert collection_name in faiss_provider.collections

        collection = faiss_provider.collections[collection_name]
        assert collection['index'].ntotal == 3
        assert len(collection['metadata']) == 3
        assert len(collection['extra_metadata']) == 3

    @pytest.mark.asyncio
    async def test_search_vectors(self, faiss_provider):
        """Test vector search."""
        collection_name = 'test_collection'

        # Add some test vectors
        vectors = [
            [0.1] * 384,
            [0.5] * 384,
            [0.9] * 384,
        ]
        texts = ['similar to query', 'medium match', 'different']

        await faiss_provider.add_vectors(collection_name, vectors, texts)

        # Search with query similar to first vector
        query_vector = [0.1] * 384
        results = await faiss_provider.search_vectors(
            collection_name, query_vector, limit=2
        )

        assert len(results) == 2
        assert results[0]['text'] == 'similar to query'
        assert 'distance' in results[0]
        assert 'id' in results[0]
        assert 'metadata' in results[0]

    @pytest.mark.asyncio
    async def test_search_nonexistent_collection(self, faiss_provider):
        """Test search in non-existent collection."""
        query_vector = [0.1] * 384

        with pytest.raises(VectorDBError) as exc_info:
            await faiss_provider.search_vectors('nonexistent', query_vector)

        assert 'does not exist' in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_collections(self, faiss_provider):
        """Test listing collections."""
        # Initially empty
        collections = await faiss_provider.list_collections()
        assert collections == []

        # Create some collections
        await faiss_provider.create_collection('collection1')
        await faiss_provider.create_collection('collection2')

        collections = await faiss_provider.list_collections()
        assert len(collections) == 2
        assert 'collection1' in collections
        assert 'collection2' in collections

    @pytest.mark.asyncio
    async def test_get_collection_info(self, faiss_provider):
        """Test getting collection information."""
        collection_name = 'test_collection'

        # Add some vectors
        vectors = [[0.1] * 384, [0.2] * 384]
        texts = ['text1', 'text2']

        await faiss_provider.add_vectors(collection_name, vectors, texts)

        info = await faiss_provider.get_collection_info(collection_name)

        assert info['name'] == collection_name
        assert info['count'] == 2
        assert info['dimension'] == 384
        assert info['metadata_count'] == 2

    @pytest.mark.asyncio
    async def test_browse_vectors(self, faiss_provider):
        """Test browsing vectors in collection."""
        collection_name = 'test_collection'

        # Add test vectors
        vectors = [[0.1] * 384, [0.2] * 384, [0.3] * 384]
        texts = ['text1', 'text2', 'text3']
        metadata = [{'id': 1}, {'id': 2}, {'id': 3}]

        await faiss_provider.add_vectors(collection_name, vectors, texts, metadata)

        # Browse first 2 vectors
        results = await faiss_provider.browse_vectors(
            collection_name, offset=0, limit=2
        )

        assert len(results) == 2
        assert results[0]['text'] == 'text1'
        assert results[0]['metadata'] == {'id': 1}
        assert results[1]['text'] == 'text2'
        assert results[1]['metadata'] == {'id': 2}

        # Browse with offset
        results = await faiss_provider.browse_vectors(
            collection_name, offset=1, limit=2
        )

        assert len(results) == 2
        assert results[0]['text'] == 'text2'
        assert results[1]['text'] == 'text3'

    @pytest.mark.asyncio
    async def test_delete_collection(self, faiss_provider):
        """Test collection deletion."""
        collection_name = 'test_collection'

        # Create and populate collection
        vectors = [[0.1] * 384]
        texts = ['text1']
        await faiss_provider.add_vectors(collection_name, vectors, texts)

        assert collection_name in faiss_provider.collections

        # Delete collection
        await faiss_provider.delete_collection(collection_name)

        assert collection_name not in faiss_provider.collections

    @pytest.mark.asyncio
    async def test_empty_collection_search(self, faiss_provider):
        """Test search in empty collection."""
        collection_name = 'empty_collection'
        await faiss_provider.create_collection(collection_name)

        query_vector = [0.1] * 384
        results = await faiss_provider.search_vectors(collection_name, query_vector)

        assert results == []

    @pytest.mark.asyncio
    async def test_persistence(self, faiss_config, mock_config_manager):
        """Test data persistence across provider instances."""
        with tempfile.TemporaryDirectory() as temp_dir:
            faiss_config['storage_path'] = temp_dir

            # First provider instance
            provider1 = FAISSProvider(faiss_config)
            provider1.config_manager = mock_config_manager
            await provider1.initialize()

            # Add data
            collection_name = 'persistent_collection'
            vectors = [[0.1] * 384, [0.2] * 384]
            texts = ['persistent1', 'persistent2']

            await provider1.add_vectors(collection_name, vectors, texts)
            await provider1.cleanup()

            # Second provider instance
            provider2 = FAISSProvider(faiss_config)
            provider2.config_manager = mock_config_manager
            await provider2.initialize()

            # Check if data persisted
            collections = await provider2.list_collections()
            assert collection_name in collections

            info = await provider2.get_collection_info(collection_name)
            assert info['count'] == 2

            await provider2.cleanup()
