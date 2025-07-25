#!/bin/bash
# Setup script for RAG_07 Python application
# Configures virtual environment and installs dependencies

set -e  # Exit on any error

echo "🔧 Setting up RAG_07 Python application..."

# Check if Python 3.8+ is available
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "📍 Found Python $python_version"

if ! python3 -c "import sys; assert sys.version_info >= (3, 8)" 2>/dev/null; then
    echo "❌ Python 3.8+ is required"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "🐍 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "📦 Upgrading pip..."
python -m pip install --upgrade pip

# Install dependencies
if [ -f "requirements.txt" ]; then
    echo "📋 Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
elif [ -f "pyproject.toml" ]; then
    echo "📋 Installing dependencies from pyproject.toml..."
    pip install -e .
else
    echo "📋 Installing basic dependencies..."
    pip install \
        click \
        pydantic \
        python-dotenv \
        structlog \
        aiohttp \
        httpx \
        pytest \
        pytest-asyncio \
        pytest-cov \
        black \
        isort \
        pylint \
        mypy \
        ruff
fi

# Create necessary directories
echo "📁 Creating project structure..."
mkdir -p src/{cli,services,utils,models,providers,config}
mkdir -p tests
mkdir -p examples
mkdir -p databases
mkdir -p logs

# Create basic .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating basic .env file..."
    cat > .env << 'EOF'
# API Keys (replace with your actual keys)
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
GOOGLE_API_KEY=your_google_key_here

# Application Settings
LOG_LEVEL=INFO
DEBUG=false
APP_NAME=rag_07

# Database Settings
DATABASE_PATH=databases/local.db
VECTOR_DB_PATH=databases/vector_store

# Default Provider Settings
DEFAULT_LLM_PROVIDER=openai
DEFAULT_VECTOR_DB_PROVIDER=faiss
DEFAULT_TEXT_PROCESSOR=basic
EOF
    echo "⚠️  Please update .env file with your actual API keys"
fi

# Make CLI executable
if [ -f "src/main.py" ]; then
    chmod +x src/main.py
fi

echo "✅ Setup completed successfully!"
echo ""
echo "📚 Next steps:"
echo "1. Update .env file with your API keys"
echo "2. Run: source .venv/bin/activate"
echo "3. Run: python src/main.py --help"
echo ""
echo "🔧 Development commands:"
echo "- Format code: black src/ && isort src/"
echo "- Run tests: pytest"
echo "- Type check: mypy src/"
echo "- Lint: pylint src/"
