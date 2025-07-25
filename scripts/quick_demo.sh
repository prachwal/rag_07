#!/bin/bash

# Quick Demo Script for RAG_07 Database Management
# Creates sample collections with different configurations

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATABASE_SCRIPT="$SCRIPT_DIR/database_management.sh"

echo -e "${BLUE}=== RAG_07 Quick Demo Setup ===${NC}"
echo

echo -e "${CYAN}This script will create several demo collections with different configurations:${NC}"
echo "1. 📚 documents - Large chunks (1000 chars, 100 overlap)"
echo "2. 🧠 knowledge - Medium chunks (500 chars, 50 overlap)  "
echo "3. 💬 snippets - Small chunks (200 chars, 20 overlap)"
echo

read -p "Continue? (y/N): " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Demo cancelled"
    exit 0
fi

echo

# Collection 1: Large chunks for documents
echo -e "${GREEN}Creating 'documents' collection (large chunks)...${NC}"
$DATABASE_SCRIPT import \
  --provider faiss \
  --collection documents \
  --file examples/sample_documents.txt \
  --chunk-size 1000 \
  --overlap 100

echo

# Collection 2: Medium chunks for knowledge
echo -e "${GREEN}Creating 'knowledge' collection (medium chunks)...${NC}"
$DATABASE_SCRIPT import \
  --provider faiss \
  --collection knowledge \
  --file examples/sample_documents.txt \
  --chunk-size 500 \
  --overlap 50

echo

# Collection 3: Small chunks for snippets
echo -e "${GREEN}Creating 'snippets' collection (small chunks)...${NC}"
$DATABASE_SCRIPT import \
  --provider faiss \
  --collection snippets \
  --file examples/sample_documents.txt \
  --chunk-size 200 \
  --overlap 20

echo

# Show summary
echo -e "${BLUE}=== Demo Collections Created ===${NC}"
echo

echo -e "${CYAN}Collection Summary:${NC}"
$DATABASE_SCRIPT stats --provider faiss --collection documents | grep -E "(Collection|Vector count|Dimension)"
echo
$DATABASE_SCRIPT stats --provider faiss --collection knowledge | grep -E "(Collection|Vector count|Dimension)"
echo
$DATABASE_SCRIPT stats --provider faiss --collection snippets | grep -E "(Collection|Vector count|Dimension)"

echo
echo -e "${GREEN}Demo setup complete!${NC}"
echo
echo "Try these commands:"
echo "  # Browse different collections"
echo "  scripts/database_management.sh browse --collection documents --limit 3"
echo "  scripts/database_management.sh browse --collection snippets --limit 5"
echo
echo "  # Search in different collections"
echo "  scripts/database_management.sh search --collection knowledge --query \"machine learning\""
echo "  scripts/database_management.sh search --collection snippets --query \"Python programming\""
echo
echo "  # Get detailed stats"
echo "  scripts/database_management.sh stats --collection documents"
echo
echo "  # Clean up when done"
echo "  scripts/cleanup_databases.sh"
