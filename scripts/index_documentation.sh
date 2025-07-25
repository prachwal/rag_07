#!/bin/bash
"""
Script to populate vector database with project documentation.
Creates 'default' collection and adds documentation files.
"""

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🤖 RAG_07 Documentation Indexer"
echo "================================"
echo "📁 Project directory: $PROJECT_DIR"

# Activate virtual environment
source "$PROJECT_DIR/.venv/bin/activate"

# Change to project directory
cd "$PROJECT_DIR"

echo "📚 Adding documentation to vector database..."

# Add main README.md
echo "  📄 Adding README.md..."
./run.sh embed --collection default "$(cat README.md)"

# Add implementation plans
if [ -f "IMPLEMENTATION_PLAN.md" ]; then
    echo "  📄 Adding IMPLEMENTATION_PLAN.md..."
    ./run.sh embed --collection default "$(cat IMPLEMENTATION_PLAN.md)"
fi

if [ -f "FUNCTION_CALLING_IMPLEMENTATION_PLAN.md" ]; then
    echo "  📄 Adding FUNCTION_CALLING_IMPLEMENTATION_PLAN.md..."
    ./run.sh embed --collection default "$(cat FUNCTION_CALLING_IMPLEMENTATION_PLAN.md)"
fi

# Add documentation files from docs/ directory
if [ -d "docs" ]; then
    echo "  📁 Adding docs/ directory files..."

    # Find and add all .md files in docs/
    find docs/ -name "*.md" -type f | while read -r file; do
        echo "    📄 Adding $file..."
        ./run.sh embed --collection default "$(cat "$file")"
    done

    # Add README files if they exist
    find docs/ -name "README*" -type f | while read -r file; do
        echo "    📄 Adding $file..."
        ./run.sh embed --collection default "$(cat "$file")"
    done
fi

# Add examples README if exists
if [ -f "examples/README.md" ]; then
    echo "  📄 Adding examples/README.md..."
    ./run.sh embed --collection default "$(cat examples/README.md)"
fi

# Add setup and run scripts as documentation
echo "  📄 Adding setup script info..."
./run.sh embed --collection default "Setup script (setup.sh): $(head -20 setup.sh)"

echo "  📄 Adding run script info..."
./run.sh embed --collection default "Run script (run.sh): $(head -20 run.sh)"

# Add project structure documentation
echo "  📄 Adding project structure..."
./run.sh embed --collection default "RAG_07 Project Structure: $(find src/ -name "*.py" | head -20 | paste -sd, -)"

# Add configuration info
if [ -f "config/app_config.json" ]; then
    echo "  📄 Adding configuration info..."
    ./run.sh embed --collection default "RAG_07 Configuration: Available providers and settings from app_config.json"
fi

echo ""
echo "✅ Documentation indexing completed!"
echo "📊 Checking collection status..."

# Show collection info
./run.sh collection-info default

echo ""
echo "🎯 Test the knowledge base:"
echo "./run.sh ask-with-tools \"What are the main features of RAG_07?\" --verbose"
