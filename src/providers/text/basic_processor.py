"""
Basic text processor for chunking and cleaning text.
Handles text preprocessing for RAG applications.
"""

import re
from typing import List

from ..base import TextProcessor


class BasicTextProcessor(TextProcessor):
    """Basic implementation of text processor."""

    async def initialize(self) -> None:
        """Initialize text processor."""
        self.log_operation('initialized_basic_text_processor')

    async def cleanup(self) -> None:
        """Cleanup text processor resources."""
        self.log_operation('cleaned_up_basic_text_processor')

    async def health_check(self) -> bool:
        """Check text processor health."""
        return True

    async def chunk_text(
        self, text: str, chunk_size: int = 1000, overlap: int = 200
    ) -> List[str]:
        """Split text into overlapping chunks."""
        if not text:
            return []

        # Clean the text first
        cleaned_text = await self.clean_text(text)

        # If text is shorter than chunk_size, return as single chunk
        if len(cleaned_text) <= chunk_size:
            return [cleaned_text]

        chunks = []
        start = 0

        while start < len(cleaned_text):
            # Calculate end position
            end = start + chunk_size

            # If this is not the last chunk, try to break at sentence boundary
            if end < len(cleaned_text):
                # Look for sentence ending within the last 100 characters
                sentence_break = cleaned_text.rfind('.', max(start, end - 100), end)
                if sentence_break > start:
                    end = sentence_break + 1
                else:
                    # Look for word boundary
                    word_break = cleaned_text.rfind(' ', max(start, end - 50), end)
                    if word_break > start:
                        end = word_break

            chunk = cleaned_text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start position with overlap
            # For short texts, prevent infinite loops
            next_start = end - overlap
            if next_start <= start:
                next_start = start + max(1, chunk_size - overlap)
            start = next_start

        self.log_operation(
            'chunked_text',
            original_length=len(text),
            chunks_count=len(chunks),
            chunk_size=chunk_size,
            overlap=overlap,
        )

        return chunks

    async def clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ''

        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', text)

        # Remove special characters but keep punctuation
        cleaned = re.sub(r'[^\w\s.,!?;:()\-\'""]', ' ', cleaned)

        # Remove multiple consecutive punctuation
        cleaned = re.sub(r'([.,!?;:]){2,}', r'\1', cleaned)

        # Normalize quotes
        cleaned = re.sub(r'["""]', '"', cleaned)
        cleaned = re.sub(r"['']", "'", cleaned)

        # Clean up spacing around punctuation
        cleaned = re.sub(r'\s+([.,!?;:])', r'\1', cleaned)
        cleaned = re.sub(r'([.,!?;:])\s+', r'\1 ', cleaned)

        # Remove extra spaces
        cleaned = re.sub(r'\s+', ' ', cleaned)

        cleaned = cleaned.strip()

        self.log_operation(
            'cleaned_text', original_length=len(text), cleaned_length=len(cleaned)
        )

        return cleaned
