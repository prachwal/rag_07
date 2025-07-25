#!/bin/bash

# Database Cleanup Script for RAG_07
# Removes all test collections and provides clean slate

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DATABASE_DIR="$PROJECT_ROOT/databases"

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}

echo
echo -e "${BLUE}=== RAG_07 Database Cleanup Tool ===${NC}"
echo

log "Cleaning up test databases..."

# Clean FAISS collections
if [[ -d "$DATABASE_DIR/faiss_index" ]]; then
    log "Found FAISS database directory"

    # List files
    faiss_files=$(find "$DATABASE_DIR/faiss_index" -name "*.index" -o -name "*_metadata.json" 2>/dev/null | wc -l)

    if [[ $faiss_files -gt 0 ]]; then
        echo "FAISS collections found:"
        find "$DATABASE_DIR/faiss_index" -name "*.index" | sed 's/.*\///; s/\.index$//' | sort | sed 's/^/  • /'
        echo

        read -p "Delete all FAISS collections? (y/N): " confirm_faiss
        if [[ "$confirm_faiss" =~ ^[Yy]$ ]]; then
            rm -f "$DATABASE_DIR/faiss_index"/*.index
            rm -f "$DATABASE_DIR/faiss_index"/*_metadata.json
            success "FAISS collections deleted"
        else
            log "FAISS collections preserved"
        fi
    else
        log "No FAISS collections found"
    fi
else
    log "No FAISS database directory found"
fi

echo

# Clean ChromaDB collections
if [[ -d "$DATABASE_DIR/chroma_db" ]]; then
    log "Found ChromaDB database directory"

    chroma_size=$(du -sh "$DATABASE_DIR/chroma_db" 2>/dev/null | cut -f1)
    echo "ChromaDB directory size: $chroma_size"
    echo

    read -p "Delete ChromaDB directory? (y/N): " confirm_chroma
    if [[ "$confirm_chroma" =~ ^[Yy]$ ]]; then
        rm -rf "$DATABASE_DIR/chroma_db"
        success "ChromaDB directory deleted"
    else
        log "ChromaDB directory preserved"
    fi
else
    log "No ChromaDB database directory found"
fi

echo

# Clean logs if requested
if [[ -d "$PROJECT_ROOT/logs" ]]; then
    log "Found logs directory"

    log_size=$(du -sh "$PROJECT_ROOT/logs" 2>/dev/null | cut -f1)
    echo "Logs directory size: $log_size"
    echo

    read -p "Clean log files? (y/N): " confirm_logs
    if [[ "$confirm_logs" =~ ^[Yy]$ ]]; then
        find "$PROJECT_ROOT/logs" -name "*.log" -exec rm -f {} \;
        success "Log files cleaned"
    else
        log "Log files preserved"
    fi
fi

echo

# Show final status
log "Final database status:"

if [[ -d "$DATABASE_DIR" ]]; then
    echo "Database directories:"
    ls -la "$DATABASE_DIR" 2>/dev/null | grep "^d" | awk '{print "  • " $9 " (" $5 " bytes)"}' || echo "  • No subdirectories"

    echo
    echo "Database files:"
    find "$DATABASE_DIR" -type f 2>/dev/null | wc -l | awk '{print "  • " $1 " files total"}'

    # Show space usage
    db_size=$(du -sh "$DATABASE_DIR" 2>/dev/null | cut -f1)
    echo "  • Total size: $db_size"
else
    echo "  • No database directory"
fi

echo
success "Cleanup completed!"

echo
echo "To start fresh, you can now run:"
echo "  scripts/database_management.sh demo --provider faiss"
echo "  scripts/database_management.sh demo --provider chroma"
