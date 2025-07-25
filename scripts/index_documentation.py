#!/usr/bin/env python3
"""
Documentation indexer for RAG_07 project.
Automatically adds project documentation to the 'default' vector collection.
"""

import asyncio
import sys
from pathlib import Path
from typing import List

# Add src to path for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "src"))

from config.config_manager import ConfigManager
from services.application_service import ApplicationService
from utils.logger import get_logger

logger = get_logger(__name__)


class DocumentationIndexer:
    """Indexes project documentation into vector database."""

    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.app_service = ApplicationService(config_manager)
        self.project_root = project_root
        self.collection_name = "default"

    async def index_all_documentation(self) -> None:
        """Index all project documentation."""
        print("🤖 RAG_07 Documentation Indexer")
        print("=" * 50)

        try:
            # List all documents to be indexed
            docs_to_index = await self._collect_documentation_files()

            print(f"📚 Found {len(docs_to_index)} documentation files to index")
            print()

            indexed_count = 0

            for doc_info in docs_to_index:
                try:
                    await self._index_document(doc_info)
                    indexed_count += 1
                    print(f"  ✅ {doc_info['title']}")
                except Exception as e:
                    print(f"  ❌ {doc_info['title']}: {e}")
                    logger.error(f"Failed to index {doc_info['path']}: {e}")

            print()
            print(
                f"✅ Successfully indexed {indexed_count}/"
                f"{len(docs_to_index)} documents"
            )

            # Show collection status
            await self._show_collection_status()

        except Exception as e:
            print(f"❌ Error during indexing: {e}")
            logger.error(f"Documentation indexing failed: {e}")
            raise

    async def _collect_documentation_files(self) -> List[dict]:
        """Collect all documentation files to be indexed."""
        docs = []

        # Main documentation files
        main_docs = [
            ("README.md", "RAG_07 Main Documentation"),
            ("IMPLEMENTATION_PLAN.md", "Implementation Plan"),
            (
                "FUNCTION_CALLING_IMPLEMENTATION_PLAN.md",
                "Function Calling Implementation Plan",
            ),
        ]

        for filename, title in main_docs:
            file_path = self.project_root / filename
            if file_path.exists():
                docs.append(
                    {
                        "path": file_path,
                        "title": title,
                        "content": file_path.read_text(encoding="utf-8"),
                    }
                )

        # Documentation directory
        docs_dir = self.project_root / "docs"
        if docs_dir.exists():
            for md_file in docs_dir.rglob("*.md"):
                relative_path = md_file.relative_to(self.project_root)
                docs.append(
                    {
                        "path": md_file,
                        "title": f"Documentation: {relative_path}",
                        "content": md_file.read_text(encoding="utf-8"),
                    }
                )

        # Examples README
        examples_readme = self.project_root / "examples" / "README.md"
        if examples_readme.exists():
            docs.append(
                {
                    "path": examples_readme,
                    "title": "Examples Documentation",
                    "content": examples_readme.read_text(encoding="utf-8"),
                }
            )

        # Project structure information
        docs.append(
            {
                "path": self.project_root / "src",
                "title": "RAG_07 Project Structure and Architecture",
                "content": self._generate_project_structure_info(),
            }
        )

        # Configuration information
        config_file = self.project_root / "config" / "app_config.json"
        if config_file.exists():
            docs.append(
                {
                    "path": config_file,
                    "title": "RAG_07 Configuration Guide",
                    "content": self._generate_config_info(),
                }
            )

        return docs

    def _generate_project_structure_info(self) -> str:
        """Generate comprehensive project structure information."""
        structure_info = """
# RAG_07 Project Structure and Architecture

## Main Components:

### Core Application Files:
- src/main.py: Application entry point
- src/cli.py: Command line interface with all available commands
- src/services/application_service.py: Main business logic orchestration
- src/services/function_calling_service.py: Advanced function calling with LLM

### Provider Architecture:
- src/providers/base.py: Base interfaces and ProviderFactory
- src/providers/llm/: LLM providers (OpenAI, Anthropic, Google, Ollama, etc.)
- src/providers/vector/: Vector database providers (FAISS, Chroma)
- src/providers/text/: Text processing providers

### Tools and Utilities:
- src/tools/: Function calling tools (VectorSearchTools, FunctionExecutor)
- src/utils/: Utilities (logger, model cache)
- src/config/: Configuration management

### Key Features:
1. Multi-provider LLM support with unified interface
2. Vector database integration for RAG
3. Function calling capabilities for advanced interactions
4. Comprehensive CLI with multiple commands
5. Async architecture with proper error handling
6. Structured logging and configuration management

### Available CLI Commands:
- query: Send queries to LLM providers
- embed: Add text to vector databases
- search: Search in vector databases
- rag: RAG queries with context
- ask-with-tools: Advanced function calling queries
- list-providers: Show available providers
- list-models: Show available models
- config-status: Show configuration status
- list-collections: Show vector database collections
"""

        # Add actual file listing
        src_files = []
        for py_file in (self.project_root / "src").rglob("*.py"):
            relative_path = py_file.relative_to(self.project_root)
            src_files.append(str(relative_path))

        structure_info += f"\n### Source Files:\n"
        for file in sorted(src_files):
            structure_info += f"- {file}\n"

        return structure_info

    def _generate_config_info(self) -> str:
        """Generate configuration information."""
        config_info = """
# RAG_07 Configuration Guide

## Overview:
RAG_07 uses a centralized configuration system with support for multiple LLM and vector database providers.

## Configuration Files:
- config/app_config.json: Main application configuration
- .env: Environment variables for API keys

## Supported LLM Providers:
- OpenAI (GPT models)
- Anthropic (Claude models)
- Google (Gemini models)
- Ollama (local models)
- OpenRouter (multiple models)
- LMStudio (local models)

## Supported Vector Databases:
- FAISS (local, high performance)
- Chroma (local, easy to use)
- Pinecone (cloud-based)

## Key Configuration Options:
- default_llm_provider: Default LLM provider to use
- default_vector_provider: Default vector database provider
- Collection settings for vector databases
- API timeout and retry settings
- Model-specific configurations

## Environment Setup:
Required environment variables in .env:
- OPENAI_API_KEY: For OpenAI models
- ANTHROPIC_API_KEY: For Anthropic models
- GOOGLE_API_KEY: For Google models
- PINECONE_API_KEY: For Pinecone (if used)
"""
        return config_info

    async def _index_document(self, doc_info: dict) -> None:
        """Index a single document."""
        # Split long documents into chunks
        content = doc_info["content"]
        title = doc_info["title"]

        # Add title as context
        full_content = f"Document: {title}\n\n{content}"

        # For very long documents, split into chunks
        if len(full_content) > 8000:  # Adjust chunk size as needed
            chunks = self._split_content(full_content, title)
            for i, chunk in enumerate(chunks):
                chunk_title = f"{title} (Part {i+1}/{len(chunks)})"
                await self.app_service.add_to_vector_store(
                    text=chunk,
                    collection=self.collection_name,
                    provider=None,  # Use default
                )
        else:
            await self.app_service.add_to_vector_store(
                text=full_content,
                collection=self.collection_name,
                provider=None,  # Use default
            )

    def _split_content(
        self, content: str, title: str, chunk_size: int = 6000
    ) -> List[str]:
        """Split content into manageable chunks."""
        chunks = []
        lines = content.split('\n')
        current_chunk = f"Document: {title}\n\n"

        for line in lines:
            if len(current_chunk) + len(line) + 1 > chunk_size:
                if current_chunk.strip():
                    chunks.append(current_chunk)
                current_chunk = f"Document: {title} (continued)\n\n{line}\n"
            else:
                current_chunk += line + "\n"

        if current_chunk.strip():
            chunks.append(current_chunk)

        return chunks

    async def _show_collection_status(self) -> None:
        """Show the status of the indexed collection."""
        try:
            print("\n📊 Collection Status:")
            print(f"   Collection: {self.collection_name}")

            # Try to get collection info (this might not work with all providers)
            try:
                from src.providers.base import ProviderFactory

                factory = ProviderFactory(self.config_manager)
                vector_provider = await factory.create_vector_provider()

                if hasattr(vector_provider, 'get_collection_info'):
                    info = await vector_provider.get_collection_info(
                        self.collection_name
                    )
                    count = info.get('count', 'Unknown')
                    dimension = info.get('dimension', 'Unknown')
                    print(f"   Vector count: {count}")
                    print(f"   Dimension: {dimension}")

                await vector_provider.cleanup()

            except Exception as e:
                print(f"   Status: Created (details unavailable: {e})")

            print("\n🎯 Test the knowledge base:")
            print(
                './run.sh ask-with-tools "What are the main features of RAG_07?" --verbose'
            )

        except Exception as e:
            print(f"   Error getting collection status: {e}")


async def main():
    """Main function."""
    try:
        # Initialize configuration
        config_manager = ConfigManager()

        # Create and run indexer
        indexer = DocumentationIndexer(config_manager)
        await indexer.index_all_documentation()

    except KeyboardInterrupt:
        print("\n⏹️  Indexing interrupted by user")
    except Exception as e:
        print(f"\n❌ Indexing failed: {e}")
        logger.error(f"Documentation indexing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
