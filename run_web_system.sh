#!/bin/bash

# run_web_system.sh - Start RAG_07 Web System (FastAPI + Streamlit)
# This script starts both FastAPI backend and Streamlit frontend

set -e

echo "🚀 Starting RAG_07 Web System"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${RED}❌ Virtual environment not found. Run setup.sh first.${NC}"
    exit 1
fi

# Activate virtual environment
source .venv/bin/activate

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down system...${NC}"

    # Kill background processes
    if [ ! -z "$API_PID" ] && kill -0 $API_PID 2>/dev/null; then
        echo -e "${YELLOW}Stopping API Server (PID: $API_PID)...${NC}"
        kill $API_PID
        wait $API_PID 2>/dev/null || true
    fi

    echo -e "${GREEN}✅ System shutdown completed${NC}"
    exit 0
}

# Register cleanup function
trap cleanup SIGINT SIGTERM EXIT

# Check if all dependencies are installed
echo -e "${BLUE}📦 Checking dependencies...${NC}"
python -c "import fastapi, uvicorn, streamlit" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  Missing dependencies. Installing...${NC}"
    pip install -r requirements.txt
}

# Start FastAPI server in background
echo -e "${BLUE}📡 Starting FastAPI API Server...${NC}"
python -m src.web.api_server &
API_PID=$!

# Wait for API to start
echo -e "${YELLOW}⏳ Waiting for API to start...${NC}"
sleep 3

# Check if API is running
API_URL="http://localhost:8000"
for i in {1..10}; do
    if curl -s "$API_URL/api/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API Server started successfully${NC}"
        echo -e "${BLUE}📍 API running at: $API_URL${NC}"
        echo -e "${BLUE}📋 API Documentation: $API_URL/docs${NC}"
        break
    else
        if [ $i -eq 10 ]; then
            echo -e "${RED}❌ Failed to start API Server${NC}"
            kill $API_PID 2>/dev/null || true
            exit 1
        fi
        echo -e "${YELLOW}⏳ Waiting for API... (attempt $i/10)${NC}"
        sleep 2
    fi
done

# Start Streamlit frontend
echo -e "${BLUE}🎨 Starting Streamlit Dashboard...${NC}"
echo -e "${GREEN}🌐 Dashboard will open at: http://localhost:8501${NC}"
echo -e "${YELLOW}📝 Press Ctrl+C to stop both services${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════${NC}"

# Run Streamlit (this will block until stopped)
streamlit run src/web/streamlit_app.py --server.port 8501 --server.address localhost

# Cleanup will be called automatically when script exits
