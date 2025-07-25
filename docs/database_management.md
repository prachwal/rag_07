# Database Management Script Documentation

## Overview

`database_management.sh` is a comprehensive shell script for managing vector databases in the RAG_07 application. It supports both FAISS and ChromaDB providers with full CRUD operations.

## Features

✅ **Database Creation** - Initialize collections in vector databases
✅ **Document Import** - Process and import text files into vector databases
✅ **Statistics & Analytics** - Get detailed database statistics and collection info
✅ **Content Browsing** - Browse stored documents with pagination
✅ **Semantic Search** - Search documents using vector similarity
✅ **Collection Management** - Create, list, and delete collections
✅ **Full Demo Mode** - Complete demonstration of all features

## Supported Providers

- **FAISS** - Facebook AI Similarity Search (always available)
- **ChromaDB** - Vector database with persistence (optional - requires `pip install chromadb`)

## Usage

### Basic Commands

```bash
# Show help
scripts/database_management.sh help

# Run full demo with FAISS
scripts/database_management.sh demo

# Run full demo with ChromaDB (if available)
scripts/database_management.sh demo --provider chroma
```

### Database Operations

```bash
# Create a collection
scripts/database_management.sh create --provider faiss --collection documents

# Import documents from file
scripts/database_management.sh import --file examples/sample_documents.txt --collection documents

# Get database statistics
scripts/database_management.sh stats --provider faiss --collection documents

# Browse database contents
scripts/database_management.sh browse --collection documents --limit 5

# Search in database
scripts/database_management.sh search --query "machine learning" --limit 3

# Delete a collection
scripts/database_management.sh delete --collection documents
```

### Advanced Usage

```bash
# Custom chunk settings
scripts/database_management.sh import --file my_doc.txt --chunk-size 1000 --overlap 100

# Different providers and collections
scripts/database_management.sh create --provider chroma --collection knowledge_base
scripts/database_management.sh import --provider chroma --collection knowledge_base --file data.txt
```

## Command Reference

### Commands

| Command | Description | Required Args | Optional Args |
|---------|-------------|---------------|---------------|
| `create` | Create database and collection | - | `--provider`, `--collection` |
| `import` | Import documents from file | - | `--file`, `--provider`, `--collection`, `--chunk-size`, `--overlap` |
| `stats` | Show database statistics | - | `--provider`, `--collection` |
| `browse` | Browse database contents | - | `--provider`, `--collection`, `--limit` |
| `search` | Search in database | `--query` | `--provider`, `--collection`, `--limit` |
| `delete` | Delete collection | - | `--provider`, `--collection` |
| `demo` | Run full demo cycle | - | `--provider`, `--collection` |
| `help` | Show help message | - | - |

### Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--provider` | `-p` | Vector database provider (`faiss`/`chroma`) | `faiss` |
| `--collection` | `-c` | Collection name | `test_collection` |
| `--file` | `-f` | File to import | `examples/sample_documents.txt` |
| `--query` | `-q` | Search query | - |
| `--limit` | `-l` | Limit results | `5` (search), `10` (browse) |
| `--chunk-size` | - | Text chunk size | `500` |
| `--overlap` | - | Text chunk overlap | `50` |

## Demo Workflow

The demo command runs a complete database management cycle:

1. **Create Collection** - Initialize a new collection
2. **Import Documents** - Process and import sample documents
3. **Show Statistics** - Display collection info and document count
4. **Browse Contents** - Show sample stored documents
5. **Search Database** - Demonstrate search functionality
6. **Cleanup Instructions** - Show how to delete the test collection

## File Processing

The script automatically:
- Reads text files with UTF-8 encoding
- Cleans and normalizes text content
- Splits text into overlapping chunks
- Creates normalized random vectors (in production, use real embeddings)
- Stores vectors with metadata including source file and chunk information

## Directory Structure

```
databases/
├── faiss_index/                 # FAISS storage
│   ├── collection_name.index   # Vector index files
│   └── collection_name_metadata.json  # Metadata files
└── chroma_db/                   # ChromaDB storage (if available)
    └── [ChromaDB internal files]
```

## Configuration

The script uses configuration from `config/app_config.json`:
- Vector dimensions: 1536 (matches OpenAI embeddings)
- Storage paths: `databases/faiss_index` and `databases/chroma_db`
- Default providers and collections

## Error Handling

The script includes comprehensive error handling:
- **Environment Checks** - Validates Python virtual environment
- **Dependency Checks** - Verifies required packages are installed
- **File Validation** - Checks input files exist and are readable
- **Provider Validation** - Ensures selected provider is available
- **Graceful Failures** - Handles missing ChromaDB gracefully

## Logging

All operations are logged with:
- Structured JSON logging from Python components
- Colored console output for script operations
- Operation timestamps and component information
- Error details and stack traces when needed

## Examples

### Complete FAISS Workflow

```bash
# 1. Run demo to see everything working
scripts/database_management.sh demo --provider faiss

# 2. Create your own collection
scripts/database_management.sh create --provider faiss --collection my_docs

# 3. Import your documents
scripts/database_management.sh import --file my_document.txt --collection my_docs

# 4. Check what was imported
scripts/database_management.sh stats --collection my_docs

# 5. Browse the content
scripts/database_management.sh browse --collection my_docs --limit 3

# 6. Search for specific content
scripts/database_management.sh search --query "artificial intelligence" --collection my_docs

# 7. Clean up when done
scripts/database_management.sh delete --collection my_docs
```

### ChromaDB Workflow (if available)

```bash
# Install ChromaDB first
pip install chromadb

# Then use the same commands with --provider chroma
scripts/database_management.sh demo --provider chroma
scripts/database_management.sh import --provider chroma --file data.txt
```

## Performance Notes

- **FAISS** - Fast similarity search, good for large datasets
- **ChromaDB** - Rich metadata support, good for complex queries
- **Vector Dimensions** - Currently uses 1536 to match OpenAI embeddings
- **Chunk Sizes** - Default 500 characters with 50 character overlap

## Troubleshooting

### Common Issues

1. **Virtual Environment Not Active**
   ```bash
   source .venv/bin/activate
   ```

2. **ChromaDB Not Available**
   ```bash
   pip install chromadb
   ```

3. **Permission Errors**
   ```bash
   chmod +x scripts/database_management.sh
   ```

4. **Vector Dimension Mismatch**
   - Ensure configuration matches your embedding provider
   - Default is 1536 for OpenAI compatibility

### Debug Mode

For debugging, check the log files:
```bash
tail -f logs/app.log
```

Or run with verbose Python logging:
```bash
export PYTHONPATH=$PWD/src
python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
```

## Integration

This script integrates with:
- **RAG_07 Configuration System** - Uses `config/app_config.json`
- **Provider Factory** - Leverages existing provider infrastructure
- **Text Processing** - Uses BasicTextProcessor for document preparation
- **Logging System** - Integrates with structured logging

## Security

- No hardcoded credentials
- Uses environment variables for API keys
- Safe file operations with proper encoding
- Input validation and sanitization
