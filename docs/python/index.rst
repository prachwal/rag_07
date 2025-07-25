RAG_07 Python Documentation
============================

Welcome to the RAG_07 Python codebase documentation.

About RAG_07
============

RAG_07 is a comprehensive **Retrieval-Augmented Generation (RAG)** system that combines the power of
multiple Large Language Models (LLMs) with advanced vector databases to provide intelligent document
processing and question-answering capabilities.

Key Features
------------

🤖 **Multi-Provider LLM Support**
  - OpenAI GPT models (GPT-4, GPT-3.5-turbo)
  - Anthropic Claude models (Claude-3.5-Sonnet, Claude-3-Haiku)
  - Google AI models (Gemini Pro, Gemini Flash)
  - Ollama local models
  - OpenRouter model marketplace
  - LM Studio local inference

🗄️ **Vector Database Integration**
  - FAISS for high-performance similarity search
  - Chroma DB for persistent vector storage
  - Automatic embedding generation and caching

📊 **Model Management System**
  - Real-time model availability checking
  - Pricing information and cost estimation
  - Model capabilities assessment (context length, multimodal support)
  - Local caching with TTL for performance optimization

🔧 **Advanced Configuration**
  - Environment-based configuration management
  - Provider-specific settings and API key management
  - Automatic fallback between providers
  - Retry mechanisms and error handling

Architecture Overview
---------------------

The system follows a **layered architecture** with clear separation of concerns:

**Service Layer** (``src/services/``)
  - ``ApplicationService``: Main orchestration and business logic
  - Handles RAG workflows, model selection, and response generation

**Provider Layer** (``src/providers/``)
  - **LLM Providers**: Adapters for different AI model APIs
  - **Vector Providers**: Database adapters for vector storage and retrieval
  - **Text Processors**: Document parsing and preprocessing

**Configuration Layer** (``src/config/``)
  - Environment management and API key handling
  - Provider-specific configuration files
  - Dynamic configuration loading and validation

**Utility Layer** (``src/utils/``)
  - Logging, caching, and helper functions
  - Model information management and caching

Use Cases
----------

📚 **Document Analysis**
  - Process and analyze large document collections
  - Extract insights and answer questions about content
  - Support for multiple document formats

🔍 **Intelligent Search**
  - Semantic search across document repositories
  - Context-aware query processing
  - Ranked results with relevance scoring

💬 **Conversational AI**
  - Multi-turn conversations with context retention
  - Provider-agnostic chat interfaces
  - Automatic model selection based on query complexity

📈 **Research Assistant**
  - Academic paper analysis and summarization
  - Cross-reference generation and fact-checking
  - Citation management and source tracking

Getting Started
---------------

1. **Installation**: Run ``./setup.sh`` to install dependencies
2. **Configuration**: Set up API keys in ``.env`` file
3. **Basic Usage**: ``python src/main.py query "Your question here"``
4. **Model Management**: ``python src/main.py list-models --provider openai``

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules/index

Core Modules
------------

This documentation covers all Python modules in the RAG_07 system.

API Reference
-------------

Auto-generated API documentation is available in the modules section.

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
