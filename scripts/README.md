# 🗄️ Database Management Scripts

Collection of shell scripts for managing vector databases in RAG_07 application.

## 📋 Available Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `database_management.sh` | Main database management tool | Full CRUD operations |
| `cleanup_databases.sh` | Clean all test databases | Quick cleanup |
| `quick_demo.sh` | Create sample collections | Demo setup |

## 🚀 Quick Start

```bash
# 1. Run complete demo
scripts/database_management.sh demo

# 2. Create multiple sample collections
scripts/quick_demo.sh

# 3. Clean everything when done
scripts/cleanup_databases.sh
```

## 📝 Main Database Management Tool

`database_management.sh` - Comprehensive vector database management

### Commands

```bash
# Create database and collection
scripts/database_management.sh create --provider faiss --collection docs

# Import documents
scripts/database_management.sh import --file my_document.txt --collection docs

# Get statistics
scripts/database_management.sh stats --collection docs

# Browse contents
scripts/database_management.sh browse --collection docs --limit 5

# Search database
scripts/database_management.sh search --query "machine learning" --limit 3

# Delete collection
scripts/database_management.sh delete --collection docs

# Run full demo
scripts/database_management.sh demo
```

### Options

- `--provider` (`-p`) - Vector database provider: `faiss` or `chroma`
- `--collection` (`-c`) - Collection name
- `--file` (`-f`) - File to import
- `--query` (`-q`) - Search query
- `--limit` (`-l`) - Limit results
- `--chunk-size` - Text chunk size (default: 500)
- `--overlap` - Text chunk overlap (default: 50)

## 🧹 Cleanup Tool

`cleanup_databases.sh` - Remove all test databases and logs

```bash
# Interactive cleanup with prompts
scripts/cleanup_databases.sh
```

Features:
- Lists existing collections before deletion
- Confirms each deletion step
- Shows database size information
- Cleans log files optionally

## 🎯 Quick Demo Setup

`quick_demo.sh` - Create multiple demo collections with different configurations

```bash
# Create 3 collections with different chunk sizes
scripts/quick_demo.sh
```

Creates:
- **documents** - Large chunks (1000 chars, 100 overlap)
- **knowledge** - Medium chunks (500 chars, 50 overlap)
- **snippets** - Small chunks (200 chars, 20 overlap)

## 🔧 Configuration

Scripts use configuration from `config/app_config.json`:
- Vector dimensions: 1536 (OpenAI compatible)
- Storage paths: `databases/faiss_index`, `databases/chroma_db`
- Default providers and collections

## 📊 Supported Operations

### Database Providers
- ✅ **FAISS** - Facebook AI Similarity Search (always available)
- ✅ **ChromaDB** - Vector database with persistence (optional)

### File Operations
- ✅ **Text Import** - UTF-8 text files
- ✅ **Chunking** - Configurable chunk sizes and overlap
- ✅ **Metadata** - Source file, chunk info, custom metadata

### Database Operations
- ✅ **Create** - Initialize collections
- ✅ **Import** - Add documents to collections
- ✅ **Search** - Vector similarity search
- ✅ **Browse** - Paginated content viewing
- ✅ **Statistics** - Collection info and counts
- ✅ **Delete** - Remove collections

## 📁 Directory Structure

```
databases/
├── faiss_index/                    # FAISS storage
│   ├── collection_name.index      # Vector index files
│   └── collection_name_metadata.json  # Metadata files
└── chroma_db/                      # ChromaDB storage
    └── [ChromaDB internal files]
```

## 🎭 Example Workflows

### Basic Workflow
```bash
# 1. Create and populate collection
scripts/database_management.sh import --file my_data.txt --collection my_docs

# 2. Check what was imported
scripts/database_management.sh stats --collection my_docs

# 3. Search for content
scripts/database_management.sh search --query "important topic" --collection my_docs

# 4. Browse content
scripts/database_management.sh browse --collection my_docs

# 5. Clean up
scripts/database_management.sh delete --collection my_docs
```

### Multi-Collection Setup
```bash
# Set up different collections for different content types
scripts/database_management.sh import --file docs.txt --collection documentation --chunk-size 1000
scripts/database_management.sh import --file faqs.txt --collection faq --chunk-size 300
scripts/database_management.sh import --file code.txt --collection code_examples --chunk-size 500

# Search across different collections
scripts/database_management.sh search --query "API usage" --collection documentation
scripts/database_management.sh search --query "how to" --collection faq
scripts/database_management.sh search --query "function" --collection code_examples
```

### ChromaDB Usage (if available)
```bash
# Install ChromaDB
pip install chromadb

# Use ChromaDB provider
scripts/database_management.sh demo --provider chroma
scripts/database_management.sh import --provider chroma --file data.txt --collection chroma_docs
```

## 🔍 Debugging

### Environment Issues
```bash
# Ensure virtual environment is active
source .venv/bin/activate

# Check dependencies
python -c "import faiss; print('FAISS available')"
python -c "import chromadb; print('ChromaDB available')" 2>/dev/null || echo "ChromaDB not available"
```

### Script Permissions
```bash
# Make scripts executable
chmod +x scripts/*.sh
```

### Log Files
```bash
# Check application logs
tail -f logs/app.log

# Check for errors
grep ERROR logs/app.log
```

## 📈 Performance Tips

- **Chunk Sizes**: Smaller chunks = more granular search, larger chunks = more context
- **Vector Dimensions**: 1536 works well with OpenAI embeddings
- **FAISS**: Better for large datasets and fast search
- **ChromaDB**: Better for complex metadata and persistence

## 🔒 Security Notes

- Scripts validate input files and parameters
- No hardcoded credentials or API keys
- Safe file operations with proper encoding
- Directory permissions respected
- Confirmation prompts for destructive operations
