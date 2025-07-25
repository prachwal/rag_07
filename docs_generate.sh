#!/bin/bash

# docs_generate.sh - Generate comprehensive documentation for RAG_07 project
# This script generates both Python (Sphinx) and TypeScript (TypeDoc) documentation

set -e

echo "🚀 Generating RAG_07 Documentation..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo -e "${BLUE}📁 Project root: $PROJECT_ROOT${NC}"

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install missing dependencies
install_deps() {
    echo -e "${YELLOW}📦 Installing documentation dependencies...${NC}"

    # Python dependencies
    if [ -f ".venv/bin/pip" ]; then
        .venv/bin/pip install sphinx sphinx-rtd-theme myst-parser sphinx-autodoc-typehints
    else
        pip install sphinx sphinx-rtd-theme myst-parser sphinx-autodoc-typehints
    fi

    # Node dependencies
    if [ -f "package.json" ]; then
        npm install --save-dev typedoc typedoc-plugin-markdown @microsoft/tsdoc
    fi
}

# Function to generate Python documentation
generate_python_docs() {
    echo -e "${BLUE}🐍 Generating Python documentation with Sphinx...${NC}"

    # Create docs directories
    mkdir -p docs/python/_build
    mkdir -p docs/python/_static
    mkdir -p docs/python/_templates

    # Generate module documentation
    echo -e "${YELLOW}📝 Auto-generating module documentation...${NC}"

    # Ensure modules directory exists
    mkdir -p docs/python/modules

    # Create module documentation files
    cat > docs/python/modules/index.rst << EOF
Core Modules
============

This section documents the core modules of RAG_07.

.. toctree::
   :maxdepth: 2

   main
   cli
   exceptions

Module Overview
---------------

- **main**: Application entry point
- **cli**: Command-line interface
- **exceptions**: Custom exception classes
EOF

    mkdir -p docs/python/modules
    mkdir -p docs/python/providers
    mkdir -p docs/python/services
    mkdir -p docs/python/utils
    mkdir -p docs/python/models

    # Generate provider documentation
    cat > docs/python/providers/index.md << EOF
# Providers

Provider implementations for LLM and vector database backends.

\`\`\`{toctree}
:maxdepth: 2

base
llm/index
vector/index
\`\`\`
EOF

    # Generate services documentation
    cat > docs/python/services/index.md << EOF
# Services

Business logic services and application orchestration.

\`\`\`{toctree}
:maxdepth: 2

application_service
\`\`\`
EOF

    # Generate utils documentation
    cat > docs/python/utils/index.md << EOF
# Utilities

Utility modules and helper functions.

\`\`\`{toctree}
:maxdepth: 2

logger
model_cache
\`\`\`
EOF

    # Generate models documentation
    cat > docs/python/models/index.md << EOF
# Data Models

Data structures and model definitions.

\`\`\`{toctree}
:maxdepth: 2

model_info
\`\`\`
EOF

    # Build Sphinx documentation
    cd docs/python
    if [ -f "../../.venv/bin/sphinx-build" ]; then
        ../../.venv/bin/sphinx-build -b html . _build/html
    else
        sphinx-build -b html . _build/html
    fi
    cd ../..

    echo -e "${GREEN}✅ Python documentation generated in docs/python/_build/html${NC}"
}

# Function to generate TypeScript documentation
generate_typescript_docs() {
    echo -e "${BLUE}📘 Generating TypeScript documentation with TypeDoc...${NC}"

    # Check if TypeScript files exist
    if [ ! -f "tsconfig.json" ]; then
        echo -e "${YELLOW}⚠️  No tsconfig.json found, skipping TypeScript documentation${NC}"
        return
    fi

    # Create output directory
    mkdir -p public/docs/api

    # Generate TypeDoc documentation
    if command_exists npx; then
        npx typedoc
        echo -e "${GREEN}✅ TypeScript documentation generated in public/docs/api${NC}"
    else
        echo -e "${RED}❌ npx not found, skipping TypeScript documentation${NC}"
    fi
}

# Function to create unified documentation index
create_unified_index() {
    echo -e "${BLUE}📋 Creating unified documentation index...${NC}"

    mkdir -p public/docs

    cat > public/docs/index.html << EOF
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAG_07 Documentation</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            line-height: 1.6;
        }
        .header {
            text-align: center;
            margin-bottom: 3rem;
            padding-bottom: 2rem;
            border-bottom: 2px solid #eee;
        }
        .docs-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-top: 2rem;
        }
        .doc-card {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 1.5rem;
            text-decoration: none;
            color: inherit;
            transition: all 0.3s ease;
        }
        .doc-card:hover {
            border-color: #007acc;
            box-shadow: 0 4px 12px rgba(0,122,204,0.1);
            transform: translateY(-2px);
        }
        .doc-title {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: #007acc;
        }
        .doc-description {
            color: #666;
            margin-bottom: 1rem;
        }
        .doc-status {
            font-size: 0.9rem;
            color: #28a745;
            font-weight: 500;
        }
        .overview {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 2rem;
            margin-bottom: 2rem;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>RAG_07 Documentation</h1>
        <p>Comprehensive multi-provider LLM and RAG system</p>
    </div>

    <div class="overview">
        <h2>Project Overview</h2>
        <p>RAG_07 provides a unified interface for multiple LLM providers (OpenAI, Anthropic, Google, Ollama, OpenRouter, LM Studio) with integrated vector database support for Retrieval-Augmented Generation (RAG) workflows.</p>

        <h3>Key Features</h3>
        <ul>
            <li>🤖 Multi-provider LLM integration</li>
            <li>🔍 Vector database support (FAISS, Chroma)</li>
            <li>📊 Model management and capability detection</li>
            <li>💰 Pricing information and cost optimization</li>
            <li>🛠️ Command-line interface</li>
            <li>🔄 Caching and performance optimization</li>
        </ul>
    </div>

    <div class="docs-grid">
        <a href="../python/_build/html/index.html" class="doc-card">
            <div class="doc-title">🐍 Python API Documentation</div>
            <div class="doc-description">
                Complete Python API reference including providers, services, models, and utilities.
            </div>
            <div class="doc-status">✅ Generated with Sphinx</div>
        </a>

        <a href="api/index.html" class="doc-card">
            <div class="doc-title">📘 TypeScript API Documentation</div>
            <div class="doc-description">
                TypeScript/JavaScript API documentation for frontend components and utilities.
            </div>
            <div class="doc-status">✅ Generated with TypeDoc</div>
        </a>

        <a href="../model_management.md" class="doc-card">
            <div class="doc-title">📋 Model Management Guide</div>
            <div class="doc-description">
                Guide for managing models across different providers, including pricing and capabilities.
            </div>
            <div class="doc-status">📖 User Guide</div>
        </a>

        <a href="../database_management.md" class="doc-card">
            <div class="doc-title">🗄️ Database Management Guide</div>
            <div class="doc-description">
                Documentation for vector database setup, management, and optimization.
            </div>
            <div class="doc-status">📖 User Guide</div>
        </a>
    </div>

    <div style="margin-top: 3rem; text-align: center; color: #666; border-top: 1px solid #eee; padding-top: 2rem;">
        <p>Generated on $(date) | RAG_07 v1.0.0</p>
    </div>
</body>
</html>
EOF

    echo -e "${GREEN}✅ Unified documentation index created at public/docs/index.html${NC}"
}

# Main execution
main() {
    echo -e "${GREEN}🎯 Starting documentation generation...${NC}"

    # Install dependencies if needed
    install_deps

    # Generate Python documentation
    generate_python_docs

    # Generate TypeScript documentation (if applicable)
    generate_typescript_docs

    # Create unified index
    create_unified_index

    echo -e "${GREEN}🎉 Documentation generation completed!${NC}"
    echo -e "${BLUE}📍 View documentation at: file://$PROJECT_ROOT/public/docs/index.html${NC}"

    # Try to open documentation in browser
    if command_exists xdg-open; then
        echo -e "${YELLOW}🌐 Opening documentation in browser...${NC}"
        xdg-open "file://$PROJECT_ROOT/public/docs/index.html"
    elif command_exists open; then
        echo -e "${YELLOW}🌐 Opening documentation in browser...${NC}"
        open "file://$PROJECT_ROOT/public/docs/index.html"
    fi
}

# Run main function
main "$@"
