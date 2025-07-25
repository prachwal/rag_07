"""
Tests for text processing provider.
"""

from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

from src.providers.text.basic_processor import BasicTextProcessor


class TestBasicTextProcessor:
    """Test basic text processor functionality."""

    @pytest.fixture
    def processor_config(self):
        """Sample text processor configuration."""
        return {
            'name': 'basic',
            'min_chunk_size': 50,
            'max_chunk_size': 500,
            'overlap': 20,
        }

    @pytest.fixture
    def mock_config_manager(self):
        """Mock configuration manager."""
        config_manager = AsyncMock()
        return config_manager

    @pytest_asyncio.fixture
    async def text_processor(self, processor_config, mock_config_manager):
        """Create text processor instance."""
        processor = BasicTextProcessor(processor_config)
        processor.config_manager = mock_config_manager
        await processor.initialize()
        yield processor
        await processor.cleanup()

    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test text processor initialization."""
        processor = BasicTextProcessor({'name': 'basic'})
        await processor.initialize()

        health = await processor.health_check()
        assert health is True

        await processor.cleanup()

    @pytest.mark.asyncio
    async def test_clean_text(self):
        """Test text cleaning functionality."""
        processor = BasicTextProcessor({'name': 'basic'})
        await processor.initialize()

        # Test basic cleaning
        dirty_text = "  This   is    a   test.  "
        clean_text = await processor.clean_text(dirty_text)
        assert clean_text == "This is a test."

        # Test special character removal
        dirty_text = "Text with @#$% special chars!!!"
        clean_text = await processor.clean_text(dirty_text)
        assert "Text with" in clean_text
        assert "@#$%" not in clean_text

        await processor.cleanup()

    @pytest.mark.asyncio
    async def test_clean_text_advanced(self, text_processor):
        """Test advanced text cleaning scenarios."""
        # Test newlines and tabs
        dirty_text = "Line 1\n\nLine 2\t\tTabbed"
        clean_text = await text_processor.clean_text(dirty_text)
        assert "Line 1" in clean_text
        assert "Line 2" in clean_text
        assert "Tabbed" in clean_text

        # Test mixed whitespace
        dirty_text = "   Start  \t\n  Middle   \r\n  End   "
        clean_text = await text_processor.clean_text(dirty_text)
        # No leading/trailing whitespace
        assert clean_text.strip() == clean_text
        assert "  " not in clean_text  # No double spaces

    @pytest.mark.asyncio
    async def test_chunk_text(self):
        """Test text chunking functionality."""
        processor = BasicTextProcessor({'name': 'basic'})
        await processor.initialize()

        # Test with short text
        short_text = "This is a short text."
        chunks = await processor.chunk_text(short_text, chunk_size=100)
        assert len(chunks) == 1
        assert chunks[0] == "This is a short text."

        # Test with long text
        long_text = "This is a sentence. " * 100  # Create long text
        chunks = await processor.chunk_text(long_text, chunk_size=50, overlap=10)
        assert len(chunks) > 1

        # Check overlap
        if len(chunks) > 1:
            # chunk_size + some flexibility for sentence breaks
            assert len(chunks[0]) <= 60

        await processor.cleanup()

    @pytest.mark.asyncio
    async def test_chunk_text_with_sentences(self, text_processor):
        """Test chunking with sentence boundaries."""
        text = (
            "First sentence is here. Second sentence follows. "
            "Third sentence continues the text. Fourth sentence ends it."
        )

        chunks = await text_processor.chunk_text(text, chunk_size=50, overlap=10)

        assert len(chunks) >= 1
        # Each chunk should contain complete words
        for chunk in chunks:
            assert not chunk.startswith(' ')
            assert not chunk.endswith(' ')

    @pytest.mark.asyncio
    async def test_chunk_text_edge_cases(self, text_processor):
        """Test chunking edge cases."""
        # Very long word
        long_word = "a" * 100
        chunks = await text_processor.chunk_text(long_word, chunk_size=50)
        assert len(chunks) >= 1

        # Text with only spaces
        space_text = "   " * 20
        chunks = await text_processor.chunk_text(space_text)
        # Should handle gracefully
        assert isinstance(chunks, list)

    @pytest.mark.asyncio
    async def test_empty_text_handling(self):
        """Test handling of empty or None text."""
        processor = BasicTextProcessor({'name': 'basic'})
        await processor.initialize()

        # Test empty string
        chunks = await processor.chunk_text("")
        assert chunks == []

        clean_text = await processor.clean_text("")
        assert clean_text == ""

        # Test None (should not crash)
        clean_text = await processor.clean_text(None)
        assert clean_text == ""

        await processor.cleanup()

    @pytest.mark.asyncio
    async def test_extract_keywords(self, text_processor):
        """Test keyword extraction if available."""
        text = (
            "Machine learning is a subset of artificial intelligence. "
            "Deep learning uses neural networks for pattern recognition."
        )

        # Test if method exists and works
        if hasattr(text_processor, 'extract_keywords'):
            keywords = await text_processor.extract_keywords(text)
            assert isinstance(keywords, list)
            assert len(keywords) > 0

    @pytest.mark.asyncio
    async def test_process_large_text(self, text_processor):
        """Test processing very large text."""
        # Generate large text
        large_text = "This is a test sentence. " * 1000

        # Should not crash with large input
        clean_text = await text_processor.clean_text(large_text)
        assert isinstance(clean_text, str)
        assert len(clean_text) > 0

        chunks = await text_processor.chunk_text(large_text, chunk_size=200)
        assert len(chunks) > 1
        assert all(isinstance(chunk, str) for chunk in chunks)

    @pytest.mark.asyncio
    async def test_unicode_handling(self, text_processor):
        """Test handling of unicode characters."""
        unicode_text = "Café naïve résumé 中文 日本語 🚀"

        clean_text = await text_processor.clean_text(unicode_text)
        assert isinstance(clean_text, str)

        chunks = await text_processor.chunk_text(unicode_text)
        assert len(chunks) >= 1
        assert all(isinstance(chunk, str) for chunk in chunks)

    @pytest.mark.asyncio
    async def test_configuration_parameters(
        self, processor_config, mock_config_manager
    ):
        """Test processor with custom configuration."""
        processor = BasicTextProcessor(processor_config)
        processor.config_manager = mock_config_manager
        await processor.initialize()

        # Test with custom chunk size
        text = "Word " * 50
        chunks = await processor.chunk_text(text, chunk_size=100)

        assert isinstance(chunks, list)
        await processor.cleanup()

    @pytest.mark.asyncio
    async def test_health_check_detailed(self, text_processor):
        """Test detailed health check."""
        health = await text_processor.health_check()
        assert health is True

        # Health check should work multiple times
        health2 = await text_processor.health_check()
        assert health2 is True
