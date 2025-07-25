"""
Tests for text processing provider.
"""
import pytest

from src.providers.text.basic_processor import BasicTextProcessor


class TestBasicTextProcessor:
    """Test basic text processor functionality."""

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
            # Some content should overlap between chunks
            assert len(chunks[0]) <= 60  # chunk_size + some flexibility for sentence breaks

        await processor.cleanup()

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
