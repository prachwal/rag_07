#!/bin/bash

# Database Management Script for RAG_07
# Manages both FAISS and Chroma vector databases
# Operations: create, import, query, stats, cleanup

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DATABASE_DIR="$PROJECT_ROOT/databases"
EXAMPLES_DIR="$PROJECT_ROOT/examples"
LOGS_DIR="$PROJECT_ROOT/logs"

# Default values
PROVIDER="faiss"
COLLECTION_NAME="test_collection"
SAMPLE_FILE="$EXAMPLES_DIR/sample_documents.txt"
CHUNK_SIZE=500
OVERLAP=50

# Ensure required directories exist
mkdir -p "$DATABASE_DIR" "$LOGS_DIR"

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

info() {
    echo -e "${CYAN}[INFO] $1${NC}"
}

# Function to check if Python environment is active
check_python_env() {
    log "Checking Python environment..."

    if [[ -z "$VIRTUAL_ENV" ]] && [[ ! -f "$PROJECT_ROOT/.venv/bin/activate" ]]; then
        error "Virtual environment not found or not activated"
        info "Please run: source .venv/bin/activate"
        exit 1
    fi

    if [[ -z "$VIRTUAL_ENV" ]]; then
        log "Activating virtual environment..."
        source "$PROJECT_ROOT/.venv/bin/activate"
    fi

    success "Python environment ready"
}

# Function to check dependencies
check_dependencies() {
    log "Checking dependencies..."

    # Check if required Python packages are installed
    cd "$PROJECT_ROOT"

    if ! python -c "import faiss" 2>/dev/null; then
        error "FAISS not installed"
        exit 1
    fi

    # Check if ChromaDB is available (optional)
    if python -c "import chromadb" 2>/dev/null; then
        CHROMA_AVAILABLE=true
        success "Both FAISS and ChromaDB available"
    else
        CHROMA_AVAILABLE=false
        warning "ChromaDB not available (optional)"
        success "FAISS available"
    fi
}

# Function to create database and collection
create_database() {
    local provider=$1
    local collection=$2

    log "Creating database with provider: $provider, collection: $collection"

    cd "$PROJECT_ROOT"

    # Create collection using Python CLI
    if ! python -m src.cli list-collections --provider "$provider" >/dev/null 2>&1; then
        warning "Provider $provider may not be available or configured"
    fi

    success "Database setup complete for provider: $provider"
}

# Function to import documents into database
import_documents() {
    local provider=$1
    local collection=$2
    local file_path=$3

    log "Importing documents from $file_path into $provider/$collection"

    if [[ ! -f "$file_path" ]]; then
        error "File not found: $file_path"
        return 1
    fi

    cd "$PROJECT_ROOT"

    # Create a Python script to import documents
    python << EOF
import asyncio
import sys
from pathlib import Path
from src.config.config_manager import ConfigManager
from src.providers.base import ProviderFactory
from src.utils.logger import get_logger

logger = get_logger(__name__)

async def import_documents():
    try:
        # Initialize components
        config_manager = ConfigManager()
        factory = ProviderFactory(config_manager)

        # Read document
        file_path = Path("$file_path")
        if not file_path.exists():
            print(f"File not found: {file_path}")
            return False

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Create providers
        text_processor = await factory.create_text_processor('basic')
        vector_provider = await factory.create_vector_provider('$provider')

        # Process text
        print(f"Cleaning text...")
        clean_text = await text_processor.clean_text(content)

        print(f"Chunking text with size {$CHUNK_SIZE}, overlap {$OVERLAP}...")
        chunks = await text_processor.chunk_text(
            clean_text,
            chunk_size=$CHUNK_SIZE,
            overlap=$OVERLAP
        )

        print(f"Created {len(chunks)} chunks")

        # Create collection
        await vector_provider.create_collection('$collection')

        # Create simple vectors (in real scenario, you'd use embeddings)
        import numpy as np
        dimension = 1536  # Match configuration dimension
        vectors = []
        texts = []
        metadata = []

        for i, chunk in enumerate(chunks):
            # Create simple normalized random vector
            vector = np.random.random(dimension)
            vector = vector / np.linalg.norm(vector)  # Normalize
            vectors.append(vector.tolist())
            texts.append(chunk)
            metadata.append({
                'chunk_id': i,
                'source': '$file_path',
                'chunk_size': len(chunk)
            })

        # Add vectors to database
        print(f"Adding {len(vectors)} vectors to database...")
        print(f"Vector dimensions: {len(vectors[0]) if vectors else 'N/A'}")
        print(f"Text samples: {len(texts)} texts")

        try:
            ids = await vector_provider.add_vectors('$collection', vectors, texts, metadata)
            print(f"Successfully imported {len(ids)} documents")
            print(f"Document IDs: {ids[:5]}..." if len(ids) > 5 else f"Document IDs: {ids}")
        except Exception as e:
            print(f"Error adding vectors: {e}")
            import traceback
            traceback.print_exc()
            print("Trying without metadata...")
            try:
                ids = await vector_provider.add_vectors('$collection', vectors, texts)
                print(f"Successfully imported {len(ids)} documents (without metadata)")
                print(f"Document IDs: {ids[:5]}..." if len(ids) > 5 else f"Document IDs: {ids}")
            except Exception as e2:
                print(f"Error adding vectors without metadata: {e2}")
                traceback.print_exc()
                return False        # Cleanup
        await text_processor.cleanup()
        await vector_provider.cleanup()

        return True

    except Exception as e:
        print(f"Error importing documents: {e}")
        return False

# Run import
success = asyncio.run(import_documents())
sys.exit(0 if success else 1)
EOF

    if [[ $? -eq 0 ]]; then
        success "Documents imported successfully"
    else
        error "Failed to import documents"
        return 1
    fi
}

# Function to get database statistics
get_stats() {
    local provider=$1
    local collection=$2

    log "Getting statistics for $provider/$collection"

    cd "$PROJECT_ROOT"

    # Get collection info using Python
    python << EOF
import asyncio
from src.config.config_manager import ConfigManager
from src.providers.base import ProviderFactory

async def get_stats():
    try:
        config_manager = ConfigManager()
        factory = ProviderFactory(config_manager)
        vector_provider = await factory.create_vector_provider('$provider')

        # List all collections
        collections = await vector_provider.list_collections()
        print(f"Available collections: {collections}")

        if '$collection' in collections:
            # Get collection info
            info = await vector_provider.get_collection_info('$collection')
            print(f"Collection: $collection")
            print(f"Vector count: {info.get('count', 0)}")
            print(f"Dimension: {info.get('dimension', 'N/A')}")

            # Browse some vectors
            if info.get('count', 0) > 0:
                print("\\nSample documents:")
                results = await vector_provider.browse_vectors('$collection', limit=3)
                for i, result in enumerate(results):
                    text = result.get('text', '')
                    print(f"{i+1}. {text[:100]}..." if len(text) > 100 else f"{i+1}. {text}")
        else:
            print(f"Collection '$collection' not found")

        await vector_provider.cleanup()

    except Exception as e:
        print(f"Error getting stats: {e}")

asyncio.run(get_stats())
EOF
}

# Function to search in database
search_database() {
    local provider=$1
    local collection=$2
    local query=$3
    local limit=${4:-5}

    log "Searching in $provider/$collection for: '$query'"

    cd "$PROJECT_ROOT"

    python << EOF
import asyncio
import numpy as np
from src.config.config_manager import ConfigManager
from src.providers.base import ProviderFactory

async def search():
    try:
        config_manager = ConfigManager()
        factory = ProviderFactory(config_manager)
        vector_provider = await factory.create_vector_provider('$provider')

        # Create dummy query vector (replace with real embeddings)
        dimension = 1536  # Match configuration dimension
        query_vector = np.random.random(dimension).tolist()

        print(f"Searching for: '$query'")
        results = await vector_provider.search_vectors(
            '$collection',
            query_vector,
            limit=$limit
        )

        print(f"Found {len(results)} results:")
        for i, result in enumerate(results):
            text = result.get('text', '')
            score = result.get('score', 'N/A')
            metadata = result.get('metadata', {})
            print(f"\\n{i+1}. Score: {score}")
            print(f"   Text: {text[:200]}..." if len(text) > 200 else f"   Text: {text}")
            print(f"   Metadata: {metadata}")

        await vector_provider.cleanup()

    except Exception as e:
        print(f"Error searching: {e}")

asyncio.run(search())
EOF
}

# Function to browse database contents
browse_database() {
    local provider=$1
    local collection=$2
    local limit=${3:-10}

    log "Browsing $provider/$collection (limit: $limit)"

    cd "$PROJECT_ROOT"

    python << EOF
import asyncio
from src.config.config_manager import ConfigManager
from src.providers.base import ProviderFactory

async def browse():
    try:
        config_manager = ConfigManager()
        factory = ProviderFactory(config_manager)
        vector_provider = await factory.create_vector_provider('$provider')

        print(f"Browsing collection: $collection")
        results = await vector_provider.browse_vectors('$collection', limit=$limit)

        print(f"Found {len(results)} documents:")
        for i, result in enumerate(results):
            text = result.get('text', '')
            metadata = result.get('metadata', {})
            print(f"\\n{i+1}. ID: {result.get('id', 'N/A')}")
            print(f"   Text: {text[:150]}..." if len(text) > 150 else f"   Text: {text}")
            print(f"   Metadata: {metadata}")

        await vector_provider.cleanup()

    except Exception as e:
        print(f"Error browsing: {e}")

asyncio.run(browse())
EOF
}

# Function to delete collection
delete_collection() {
    local provider=$1
    local collection=$2

    warning "This will permanently delete collection: $collection"
    read -p "Are you sure? (y/N): " confirm

    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        log "Deleting collection $provider/$collection"

        cd "$PROJECT_ROOT"

        python << EOF
import asyncio
from src.config.config_manager import ConfigManager
from src.providers.base import ProviderFactory

async def delete():
    try:
        config_manager = ConfigManager()
        factory = ProviderFactory(config_manager)
        vector_provider = await factory.create_vector_provider('$provider')

        await vector_provider.delete_collection('$collection')
        print(f"Collection '$collection' deleted successfully")

        await vector_provider.cleanup()

    except Exception as e:
        print(f"Error deleting collection: {e}")

asyncio.run(delete())
EOF

        success "Collection deleted"
    else
        info "Operation cancelled"
    fi
}

# Function to run full demo cycle
demo_cycle() {
    local provider=$1

    log "Running full demo cycle for provider: $provider"

    echo
    info "=== DEMO: Full Database Management Cycle ==="
    echo

    # Step 1: Create collection
    info "Step 1: Creating collection"
    create_database "$provider" "$COLLECTION_NAME"

    echo
    # Step 2: Import documents
    info "Step 2: Importing sample documents"
    import_documents "$provider" "$COLLECTION_NAME" "$SAMPLE_FILE"

    echo
    # Step 3: Get statistics
    info "Step 3: Getting database statistics"
    get_stats "$provider" "$COLLECTION_NAME"

    echo
    # Step 4: Browse contents
    info "Step 4: Browsing database contents"
    browse_database "$provider" "$COLLECTION_NAME" 3

    echo
    # Step 5: Search
    info "Step 5: Searching database"
    search_database "$provider" "$COLLECTION_NAME" "machine learning" 3

    echo
    # Step 6: Cleanup (optional)
    info "Step 6: Cleanup (optional)"
    echo "To delete the test collection, run:"
    echo "  $0 delete --provider $provider --collection $COLLECTION_NAME"

    echo
    success "Demo cycle completed!"
}

# Function to show usage
show_usage() {
    echo "Database Management Script for RAG_07"
    echo
    echo "Usage: $0 <command> [options]"
    echo
    echo "Commands:"
    echo "  create      Create database and collection"
    echo "  import      Import documents from file"
    echo "  stats       Show database statistics"
    echo "  browse      Browse database contents"
    echo "  search      Search in database"
    echo "  delete      Delete collection"
    echo "  demo        Run full demo cycle"
    echo "  help        Show this help"
    echo
    echo "Options:"
    echo "  --provider, -p     Vector database provider (faiss|chroma) [default: faiss]"
    echo "  --collection, -c   Collection name [default: test_collection]"
    echo "  --file, -f         File to import [default: examples/sample_documents.txt]"
    echo "  --query, -q        Search query"
    echo "  --limit, -l        Limit results [default: 5]"
    echo "  --chunk-size       Text chunk size [default: 500]"
    echo "  --overlap          Text chunk overlap [default: 50]"
    echo
    echo "Examples:"
    echo "  $0 demo                                    # Run full demo with FAISS"
    echo "  $0 demo --provider chroma                  # Run full demo with Chroma"
    echo "  $0 create --provider faiss --collection docs"
    echo "  $0 import --file my_document.txt --collection docs"
    echo "  $0 search --query 'machine learning' --limit 3"
    echo "  $0 stats --provider faiss --collection docs"
    echo "  $0 delete --collection docs"
}

# Parse command line arguments
COMMAND=""
while [[ $# -gt 0 ]]; do
    case $1 in
        create|import|stats|browse|search|delete|demo|help)
            COMMAND="$1"
            shift
            ;;
        --provider|-p)
            PROVIDER="$2"
            shift 2
            ;;
        --collection|-c)
            COLLECTION_NAME="$2"
            shift 2
            ;;
        --file|-f)
            SAMPLE_FILE="$2"
            shift 2
            ;;
        --query|-q)
            QUERY="$2"
            shift 2
            ;;
        --limit|-l)
            LIMIT="$2"
            shift 2
            ;;
        --chunk-size)
            CHUNK_SIZE="$2"
            shift 2
            ;;
        --overlap)
            OVERLAP="$2"
            shift 2
            ;;
        *)
            error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Main execution
main() {
    echo
    info "=== RAG_07 Database Management Tool ==="
    echo

    # Check environment
    check_python_env
    check_dependencies

    # Validate provider
    if [[ "$PROVIDER" == "chroma" ]] && [[ "$CHROMA_AVAILABLE" != "true" ]]; then
        error "ChromaDB not available. Install with: pip install chromadb"
        exit 1
    fi

    echo
    info "Configuration:"
    echo "  Provider: $PROVIDER"
    echo "  Collection: $COLLECTION_NAME"
    echo "  Sample file: $SAMPLE_FILE"
    echo "  Chunk size: $CHUNK_SIZE"
    echo "  Overlap: $OVERLAP"
    echo

    # Execute command
    case "$COMMAND" in
        create)
            create_database "$PROVIDER" "$COLLECTION_NAME"
            ;;
        import)
            create_database "$PROVIDER" "$COLLECTION_NAME"
            import_documents "$PROVIDER" "$COLLECTION_NAME" "$SAMPLE_FILE"
            ;;
        stats)
            get_stats "$PROVIDER" "$COLLECTION_NAME"
            ;;
        browse)
            browse_database "$PROVIDER" "$COLLECTION_NAME" "${LIMIT:-10}"
            ;;
        search)
            if [[ -z "$QUERY" ]]; then
                error "Query required for search command. Use --query option"
                exit 1
            fi
            search_database "$PROVIDER" "$COLLECTION_NAME" "$QUERY" "${LIMIT:-5}"
            ;;
        delete)
            delete_collection "$PROVIDER" "$COLLECTION_NAME"
            ;;
        demo)
            demo_cycle "$PROVIDER"
            ;;
        help|"")
            show_usage
            ;;
        *)
            error "Unknown command: $COMMAND"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main
