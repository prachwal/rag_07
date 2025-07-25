"""
Tests for Chroma vector provider.
"""

import tempfile
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

from src.exceptions import VectorDBError
from src.providers.vector.chroma_provider import ChromaProvider

# Skip all tests if ChromaDB is not available
pytest.importorskip("chromadb")


class TestChromaProvider:
    """Test Chroma provider functionality."""

    @pytest.fixture
    def chroma_config(self):
        """Sample Chroma provider configuration."""
        return {
            'name': 'chroma',
            'storage_path': 'test_databases/chroma_test',
            'dimension': 384,
        }

    @pytest.fixture
    def mock_config_manager(self):
        """Mock configuration manager."""
        config_manager = AsyncMock()
        return config_manager

    @pytest_asyncio.fixture
    async def chroma_provider(self, chroma_config, mock_config_manager):
        """Create Chroma provider instance."""
        # Use temporary directory for tests
        with tempfile.TemporaryDirectory() as temp_dir:
            chroma_config['storage_path'] = temp_dir
            provider = ChromaProvider(chroma_config)
            provider.config_manager = mock_config_manager
            await provider.initialize()
            yield provider
            await provider.cleanup()

    @pytest.mark.asyncio
    async def test_initialization(self, chroma_provider):
        """Test Chroma provider initialization."""
        # Test health check after initialization
        health = await chroma_provider.health_check()
        assert health is True

    @pytest.mark.asyncio
    async def test_database_initialization_from_scratch(self, mock_config_manager):
        """Test Chroma database initialization from scratch."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                'name': 'chroma',
                'storage_path': temp_dir,
                'dimension': 512,
            }

            provider = ChromaProvider(config)
            provider.config_manager = mock_config_manager

            # Initialize database
            await provider.initialize()

            # Verify health check
            health = await provider.health_check()
            assert health is True

            # Should start with no collections
            collections = await provider.list_collections()
            assert collections == []

            # Should be able to create first collection
            await provider.create_collection('init_test')

            collections = await provider.list_collections()
            assert 'init_test' in collections

            await provider.cleanup()

    @pytest.mark.asyncio
    async def test_persistent_database_initialization(self, mock_config_manager):
        """Test Chroma database persistence across restarts."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                'name': 'chroma',
                'storage_path': temp_dir,
                'dimension': 256,
            }

            # First instance - create data
            provider1 = ChromaProvider(config)
            provider1.config_manager = mock_config_manager
            await provider1.initialize()

            await provider1.create_collection('persistent_collection')
            vectors = [[0.1] * 256, [0.2] * 256]
            texts = ['doc1', 'doc2']
            metadata = [{'type': 'test'}, {'type': 'test'}]

            ids = await provider1.add_vectors(
                'persistent_collection', vectors, texts, metadata
            )
            assert len(ids) == 2

            # Verify data
            collection_name = 'persistent_collection'
            info1 = await provider1.get_collection_info(collection_name)
            assert info1['count'] == 2

            await provider1.cleanup()

            # Second instance - check persistence
            provider2 = ChromaProvider(config)
            provider2.config_manager = mock_config_manager
            await provider2.initialize()

            # Should find existing collection
            collections = await provider2.list_collections()
            assert 'persistent_collection' in collections

            # Data should be preserved
            info2 = await provider2.get_collection_info(collection_name)
            assert info2['count'] == 2

            # Should be able to search
            query_vector = [0.1] * 256
            results = await provider2.search_vectors(
                'persistent_collection', query_vector, limit=2
            )
            assert len(results) == 2

            await provider2.cleanup()

    @pytest.mark.asyncio
    async def test_multiple_database_initialization(self, mock_config_manager):
        """Test initialization with multiple databases."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {
                'name': 'chroma',
                'storage_path': temp_dir,
                'dimension': 128,
            }

            provider = ChromaProvider(config)
            provider.config_manager = mock_config_manager
            await provider.initialize()

            # Create multiple collections
            collection_names = ['documents', 'knowledge', 'embeddings']

            for name in collection_names:
                await provider.create_collection(name)

                # Add test data
                vectors = [[0.3] * 128, [0.7] * 128]
                texts = [f'{name}_text1', f'{name}_text2']

                await provider.add_vectors(name, vectors, texts)

            # Verify all collections exist
            collections = await provider.list_collections()
            for name in collection_names:
                assert name in collections

            # Verify each has data
            for name in collection_names:
                info = await provider.get_collection_info(name)
                assert info['count'] == 2
                assert info['dimension'] == 128

            await provider.cleanup()

    @pytest.mark.asyncio
    async def test_health_check_success(self, chroma_provider):
        """Test successful health check."""
        result = await chroma_provider.health_check()
        assert result is True

    @pytest.mark.asyncio
    async def test_create_collection(self, chroma_provider):
        """Test collection creation."""
        collection_name = 'test_collection'
        await chroma_provider.create_collection(collection_name)

        # Verify collection exists
        collections = await chroma_provider.list_collections()
        assert collection_name in collections

    @pytest.mark.asyncio
    async def test_create_duplicate_collection(self, chroma_provider):
        """Test creating duplicate collection (should not fail)."""
        collection_name = 'duplicate_collection'

        # Create first time
        await chroma_provider.create_collection(collection_name)

        # Create again - should not raise error
        await chroma_provider.create_collection(collection_name)

        collections = await chroma_provider.list_collections()
        assert collection_name in collections

    @pytest.mark.asyncio
    async def test_add_vectors(self, chroma_provider):
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

        ids = await chroma_provider.add_vectors(
            collection_name, vectors, texts, metadata
        )

        assert len(ids) == 3
        assert all(id.startswith(collection_name) for id in ids)

        # Verify collection info
        info = await chroma_provider.get_collection_info(collection_name)
        assert info['count'] == 3

    @pytest.mark.asyncio
    async def test_add_vectors_without_metadata(self, chroma_provider):
        """Test adding vectors without metadata."""
        collection_name = 'test_collection'

        vectors = [[0.1] * 384, [0.2] * 384]
        texts = ['text1', 'text2']

        ids = await chroma_provider.add_vectors(collection_name, vectors, texts)

        assert len(ids) == 2

    @pytest.mark.asyncio
    async def test_search_vectors(self, chroma_provider):
        """Test vector search."""
        collection_name = 'test_collection'

        # Add some test vectors
        vectors = [
            [0.1] * 384,
            [0.5] * 384,
            [0.9] * 384,
        ]
        texts = ['similar to query', 'medium match', 'different']

        await chroma_provider.add_vectors(collection_name, vectors, texts)

        # Search with query similar to first vector
        query_vector = [0.1] * 384
        results = await chroma_provider.search_vectors(
            collection_name, query_vector, limit=2
        )

        assert len(results) <= 2  # Chroma might return fewer results
        assert all('text' in result for result in results)
        assert all('distance' in result for result in results)
        assert all('id' in result for result in results)
        assert all('metadata' in result for result in results)

    @pytest.mark.asyncio
    async def test_search_nonexistent_collection(self, chroma_provider):
        """Test search in non-existent collection."""
        query_vector = [0.1] * 384

        with pytest.raises(VectorDBError) as exc_info:
            await chroma_provider.search_vectors('nonexistent', query_vector)

        assert 'does not exist' in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_list_collections(self, chroma_provider):
        """Test listing collections."""
        # Initially empty
        collections = await chroma_provider.list_collections()
        assert isinstance(collections, list)

        # Create some collections
        await chroma_provider.create_collection('collection1')
        await chroma_provider.create_collection('collection2')

        collections = await chroma_provider.list_collections()
        assert 'collection1' in collections
        assert 'collection2' in collections

    @pytest.mark.asyncio
    async def test_get_collection_info(self, chroma_provider):
        """Test getting collection information."""
        collection_name = 'test_collection'

        # Add some vectors
        vectors = [[0.1] * 384, [0.2] * 384]
        texts = ['text1', 'text2']

        await chroma_provider.add_vectors(collection_name, vectors, texts)

        info = await chroma_provider.get_collection_info(collection_name)

        assert info['name'] == collection_name
        assert info['count'] == 2
        assert 'metadata' in info

    @pytest.mark.asyncio
    async def test_get_nonexistent_collection_info(self, chroma_provider):
        """Test getting info for non-existent collection."""
        with pytest.raises(VectorDBError) as exc_info:
            await chroma_provider.get_collection_info('nonexistent')

        assert 'Failed to get collection info' in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_delete_collection(self, chroma_provider):
        """Test collection deletion."""
        collection_name = 'test_collection'

        # Create and populate collection
        vectors = [[0.1] * 384]
        texts = ['text1']
        await chroma_provider.add_vectors(collection_name, vectors, texts)

        # Verify collection exists
        collections = await chroma_provider.list_collections()
        assert collection_name in collections

        # Delete collection
        await chroma_provider.delete_collection(collection_name)

        # Verify collection is gone
        collections = await chroma_provider.list_collections()
        assert collection_name not in collections

    @pytest.mark.asyncio
    async def test_delete_nonexistent_collection(self, chroma_provider):
        """Test deleting non-existent collection."""
        with pytest.raises(VectorDBError) as exc_info:
            await chroma_provider.delete_collection('nonexistent')

        assert 'Failed to delete collection' in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_empty_collection_search(self, chroma_provider):
        """Test search in empty collection."""
        collection_name = 'empty_collection'
        await chroma_provider.create_collection(collection_name)

        query_vector = [0.1] * 384
        results = await chroma_provider.search_vectors(collection_name, query_vector)

        assert isinstance(results, list)
        # Empty collection might return empty list

    @pytest.mark.asyncio
    async def test_persistence(self, chroma_config, mock_config_manager):
        """Test data persistence across provider instances."""
        with tempfile.TemporaryDirectory() as temp_dir:
            chroma_config['storage_path'] = temp_dir

            # First provider instance
            provider1 = ChromaProvider(chroma_config)
            provider1.config_manager = mock_config_manager
            await provider1.initialize()

            # Add data
            collection_name = 'persistent_collection'
            vectors = [[0.1] * 384, [0.2] * 384]
            texts = ['persistent1', 'persistent2']

            await provider1.add_vectors(collection_name, vectors, texts)
            await provider1.cleanup()

            # Second provider instance
            provider2 = ChromaProvider(chroma_config)
            provider2.config_manager = mock_config_manager
            await provider2.initialize()

            # Check if data persisted
            collections = await provider2.list_collections()
            assert collection_name in collections

            info = await provider2.get_collection_info(collection_name)
            assert info['count'] == 2

            await provider2.cleanup()
