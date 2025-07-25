"""
Tests for database initialization and management.
"""

import tempfile
from pathlib import Path

import pytest
import pytest_asyncio

from src.config.config_manager import ConfigManager
from src.providers.base import ProviderFactory


class TestDatabaseInitialization:
    """Test database initialization functionality."""

    @pytest.fixture
    def config_manager(self):
        """Create configuration manager."""
        return ConfigManager()

    @pytest.fixture
    def provider_factory(self, config_manager):
        """Create provider factory."""
        return ProviderFactory(config_manager)

    @pytest_asyncio.fixture
    async def temp_storage_path(self):
        """Create temporary storage path for tests."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield temp_dir

    @pytest.mark.asyncio
    async def test_faiss_database_initialization(
        self, provider_factory, temp_storage_path
    ):
        """Test FAISS database initialization."""
        # Custom config for test
        faiss_config = {
            'name': 'faiss',
            'storage_path': temp_storage_path,
            'dimension': 512,
        }

        # Create provider with custom config
        provider = await provider_factory.create_vector_provider('faiss')
        provider.config = faiss_config
        provider.storage_path = Path(temp_storage_path)
        provider.dimension = 512

        # Test initialization
        await provider.initialize()

        # Verify storage path exists
        assert provider.storage_path.exists()
        assert provider.storage_path.is_dir()

        # Test health check
        health = await provider.health_check()
        assert health is True

        # Test collection creation
        await provider.create_collection('test_init_collection')

        # Verify collection exists
        collections = await provider.list_collections()
        assert 'test_init_collection' in collections

        # Test collection info
        info = await provider.get_collection_info('test_init_collection')
        assert info['name'] == 'test_init_collection'
        assert info['count'] == 0
        assert info['dimension'] == 512

        await provider.cleanup()

    @pytest.mark.asyncio
    async def test_faiss_persistence_initialization(
        self, provider_factory, temp_storage_path
    ):
        """Test FAISS database persistence and reinitialization."""
        faiss_config = {
            'name': 'faiss',
            'storage_path': temp_storage_path,
            'dimension': 256,
        }

        # First provider instance
        provider1 = await provider_factory.create_vector_provider('faiss')
        provider1.config = faiss_config
        provider1.storage_path = Path(temp_storage_path)
        provider1.dimension = 256

        await provider1.initialize()

        # Add test data
        await provider1.create_collection('persistent_collection')
        vectors = [[0.1] * 256, [0.2] * 256]
        texts = ['first document', 'second document']
        metadata = [{'id': 1}, {'id': 2}]

        ids = await provider1.add_vectors(
            'persistent_collection', vectors, texts, metadata
        )

        assert len(ids) == 2

        # Verify data exists
        info1 = await provider1.get_collection_info('persistent_collection')
        assert info1['count'] == 2

        await provider1.cleanup()

        # Second provider instance (simulating restart)
        provider2 = await provider_factory.create_vector_provider('faiss')
        provider2.config = faiss_config
        provider2.storage_path = Path(temp_storage_path)
        provider2.dimension = 256

        await provider2.initialize()

        # Verify data persisted
        collections = await provider2.list_collections()
        assert 'persistent_collection' in collections

        info2 = await provider2.get_collection_info('persistent_collection')
        assert info2['count'] == 2

        # Test search functionality with persisted data
        query_vector = [0.1] * 256
        results = await provider2.search_vectors(
            'persistent_collection', query_vector, limit=2
        )

        assert len(results) == 2
        assert any('first document' in result['text'] for result in results)
        assert any('second document' in result['text'] for result in results)

        await provider2.cleanup()

    @pytest.mark.asyncio
    async def test_multiple_collections_initialization(
        self, provider_factory, temp_storage_path
    ):
        """Test initialization with multiple collections."""
        faiss_config = {
            'name': 'faiss',
            'storage_path': temp_storage_path,
            'dimension': 128,
        }

        provider = await provider_factory.create_vector_provider('faiss')
        provider.config = faiss_config
        provider.storage_path = Path(temp_storage_path)
        provider.dimension = 128

        await provider.initialize()

        # Create multiple collections
        collection_names = ['docs', 'embeddings', 'knowledge_base']

        for name in collection_names:
            await provider.create_collection(name)

            # Add some test data to each collection
            vectors = [[0.1] * 128, [0.2] * 128]
            texts = [f'{name}_doc1', f'{name}_doc2']

            await provider.add_vectors(name, vectors, texts)

        # Verify all collections exist
        collections = await provider.list_collections()
        for name in collection_names:
            assert name in collections

        # Verify each collection has data
        for name in collection_names:
            info = await provider.get_collection_info(name)
            assert info['count'] == 2
            assert info['dimension'] == 128

        # Test browsing each collection
        for name in collection_names:
            browse_results = await provider.browse_vectors(name, limit=2)
            assert len(browse_results) == 2
            assert all(name in result['text'] for result in browse_results)

        await provider.cleanup()

    @pytest.mark.asyncio
    async def test_database_directory_creation(self, provider_factory):
        """Test automatic database directory creation."""
        with tempfile.TemporaryDirectory() as temp_base:
            # Nested path that doesn't exist yet
            storage_path = Path(temp_base) / 'databases' / 'vector_store' / 'faiss'

            faiss_config = {
                'name': 'faiss',
                'storage_path': str(storage_path),
                'dimension': 384,
            }

            # Verify path doesn't exist initially
            assert not storage_path.exists()

            provider = await provider_factory.create_vector_provider('faiss')
            provider.config = faiss_config
            provider.storage_path = storage_path
            provider.dimension = 384

            await provider.initialize()

            # Verify directory was created
            assert storage_path.exists()
            assert storage_path.is_dir()

            # Test basic functionality
            await provider.create_collection('auto_created')
            collections = await provider.list_collections()
            assert 'auto_created' in collections

            await provider.cleanup()

    @pytest.mark.asyncio
    async def test_database_error_handling(self, provider_factory):
        """Test database initialization error handling."""
        # Test with invalid storage path (read-only)
        faiss_config = {
            'name': 'faiss',
            'storage_path': '/invalid/readonly/path',
            'dimension': 256,
        }

        provider = await provider_factory.create_vector_provider('faiss')
        provider.config = faiss_config
        provider.storage_path = Path('/invalid/readonly/path')
        provider.dimension = 256

        # This should handle the error gracefully
        try:
            await provider.initialize()
            # If it succeeds, test basic functionality
            health = await provider.health_check()
            assert isinstance(health, bool)
        except (PermissionError, OSError):
            # Expected for invalid paths
            pass
        finally:
            try:
                await provider.cleanup()
            except (PermissionError, OSError, RuntimeError):
                # Expected for invalid paths during cleanup
                pass

    @pytest.mark.asyncio
    async def test_concurrent_database_access(
        self, provider_factory, temp_storage_path
    ):
        """Test concurrent access to the same database."""
        faiss_config = {
            'name': 'faiss',
            'storage_path': temp_storage_path,
            'dimension': 128,
        }

        # Create two provider instances
        provider1 = await provider_factory.create_vector_provider('faiss')
        provider1.config = faiss_config
        provider1.storage_path = Path(temp_storage_path)
        provider1.dimension = 128

        provider2 = await provider_factory.create_vector_provider('faiss')
        provider2.config = faiss_config
        provider2.storage_path = Path(temp_storage_path)
        provider2.dimension = 128

        await provider1.initialize()
        await provider2.initialize()

        # Provider1 creates collection
        await provider1.create_collection('shared_collection')
        vectors = [[0.1] * 128]
        texts = ['shared document']

        await provider1.add_vectors('shared_collection', vectors, texts)

        # Provider2 should see the collection after reloading
        await provider2.cleanup()
        await provider2.initialize()

        collections = await provider2.list_collections()
        assert 'shared_collection' in collections

        info = await provider2.get_collection_info('shared_collection')
        assert info['count'] == 1

        await provider1.cleanup()
        await provider2.cleanup()

    @pytest.mark.asyncio
    async def test_empty_database_initialization(
        self, provider_factory, temp_storage_path
    ):
        """Test initialization of empty database."""
        faiss_config = {
            'name': 'faiss',
            'storage_path': temp_storage_path,
            'dimension': 512,
        }

        provider = await provider_factory.create_vector_provider('faiss')
        provider.config = faiss_config
        provider.storage_path = Path(temp_storage_path)
        provider.dimension = 512

        await provider.initialize()

        # Should have no collections initially
        collections = await provider.list_collections()
        assert collections == []

        # Health check should still work
        health = await provider.health_check()
        assert health is True

        # Should be able to create first collection
        await provider.create_collection('first_collection')

        collections = await provider.list_collections()
        assert len(collections) == 1
        assert 'first_collection' in collections

        await provider.cleanup()

    @pytest.mark.asyncio
    async def test_database_cleanup_and_reinitialization(
        self, provider_factory, temp_storage_path
    ):
        """Test database cleanup and reinitialization cycle."""
        faiss_config = {
            'name': 'faiss',
            'storage_path': temp_storage_path,
            'dimension': 256,
        }

        provider = await provider_factory.create_vector_provider('faiss')
        provider.config = faiss_config
        provider.storage_path = Path(temp_storage_path)
        provider.dimension = 256

        # Initial setup
        await provider.initialize()
        await provider.create_collection('test_cleanup')

        vectors = [[0.5] * 256]
        texts = ['cleanup test document']
        await provider.add_vectors('test_cleanup', vectors, texts)

        # Verify data exists
        info_before = await provider.get_collection_info('test_cleanup')
        assert info_before['count'] == 1

        # Cleanup
        await provider.cleanup()

        # Reinitialize
        await provider.initialize()

        # Verify data persisted
        collections = await provider.list_collections()
        assert 'test_cleanup' in collections

        info_after = await provider.get_collection_info('test_cleanup')
        assert info_after['count'] == 1

        # Test search functionality
        query_vector = [0.5] * 256
        results = await provider.search_vectors('test_cleanup', query_vector, limit=1)

        assert len(results) == 1
        assert 'cleanup test document' in results[0]['text']

        await provider.cleanup()
