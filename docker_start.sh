#!/bin/bash

# docker_start.sh - Start RAG_07 system using Docker Compose
# This script provides easy deployment with Docker

set -e

echo "🐳 Starting RAG_07 with Docker Compose"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -d, --dev          Start in development mode (with nginx)"
    echo "  -p, --production   Start in production mode (with nginx and SSL)"
    echo "  -b, --build        Force rebuild of containers"
    echo "  -h, --help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                 # Start basic services (API + Dashboard + Redis)"
    echo "  $0 --dev           # Start with nginx proxy"
    echo "  $0 --production    # Start production mode with nginx"
    echo "  $0 --build         # Rebuild and start"
}

# Parse command line arguments
PROFILE=""
BUILD_FLAG=""
COMPOSE_FILE="docker-compose.yml"

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--dev)
            PROFILE="--profile development"
            shift
            ;;
        -p|--production)
            PROFILE="--profile production"
            shift
            ;;
        -b|--build)
            BUILD_FLAG="--build"
            shift
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            show_usage
            exit 1
            ;;
    esac
done

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    echo -e "${RED}❌ docker-compose not found. Please install Docker Compose.${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating template...${NC}"
    cat > .env << EOF
# RAG_07 Environment Configuration
# Copy this file to .env and configure your API keys

# LLM Provider API Keys
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
GOOGLE_API_KEY=your_google_key_here
OPENROUTER_API_KEY=your_openrouter_key_here

# Application Settings
LOG_LEVEL=INFO
DEBUG=false

# Database Settings
VECTOR_DB_TYPE=faiss
DEFAULT_COLLECTION=default

# Optional: Custom model endpoints
OLLAMA_BASE_URL=http://localhost:11434
LMSTUDIO_BASE_URL=http://localhost:1234
EOF
    echo -e "${YELLOW}📝 Please edit .env file with your API keys before starting.${NC}"
fi

# Create necessary directories
echo -e "${BLUE}📁 Creating directories...${NC}"
mkdir -p databases logs docker/ssl

# Start services
echo -e "${BLUE}🚀 Starting services...${NC}"

if [ ! -z "$PROFILE" ]; then
    echo -e "${BLUE}Using profile: $PROFILE${NC}"
fi

# Build and start containers
docker-compose $PROFILE up $BUILD_FLAG -d

# Wait for services to be healthy
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"

# Check API health
echo -e "${BLUE}🔍 Checking API health...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API Server is healthy${NC}"
        break
    else
        if [ $i -eq 30 ]; then
            echo -e "${RED}❌ API Server failed to start${NC}"
            docker-compose logs rag-api
            exit 1
        fi
        echo -e "${YELLOW}⏳ Waiting for API... ($i/30)${NC}"
        sleep 2
    fi
done

# Check Streamlit health
echo -e "${BLUE}🔍 Checking Streamlit health...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8501/_stcore/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Streamlit Dashboard is healthy${NC}"
        break
    else
        if [ $i -eq 30 ]; then
            echo -e "${RED}❌ Streamlit Dashboard failed to start${NC}"
            docker-compose logs rag-dashboard
            exit 1
        fi
        echo -e "${YELLOW}⏳ Waiting for Streamlit... ($i/30)${NC}"
        sleep 2
    fi
done

# Show service status
echo -e "${GREEN}🎉 RAG_07 System Started Successfully!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}📱 Streamlit Dashboard: http://localhost:8501${NC}"
echo -e "${GREEN}📡 FastAPI Backend:     http://localhost:8000${NC}"
echo -e "${GREEN}📋 API Documentation:  http://localhost:8000/docs${NC}"
echo -e "${GREEN}🗄️  Redis Cache:        localhost:6379${NC}"

if [[ "$PROFILE" == *"production"* ]]; then
    echo -e "${GREEN}🌐 Nginx Proxy:        http://localhost${NC}"
fi

echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${YELLOW}💡 Commands:${NC}"
echo -e "${YELLOW}   View logs:     docker-compose logs -f${NC}"
echo -e "${YELLOW}   Stop system:   docker-compose down${NC}"
echo -e "${YELLOW}   Restart:       docker-compose restart${NC}"
echo -e "${YELLOW}   Shell access:  docker-compose exec rag-api bash${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
