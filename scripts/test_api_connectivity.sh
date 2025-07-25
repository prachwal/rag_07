#!/bin/bash
# test_api_connectivity.sh - Test API connections for all providers
# Checks if APIs are reachable and credentials are valid

set -e

echo "🌐 Testing API Connectivity"
echo "=========================="

# Load environment variables
source .env 2>/dev/null || echo "⚠️  .env file not found"

# Activate virtual environment
source .venv/bin/activate

echo "Testing LLM Provider APIs..."

# Test OpenAI
if [ ! -z "$OPENAI_API_KEY" ]; then
    echo "🤖 Testing OpenAI API..."
    python -c "
import asyncio
import aiohttp
import os

async def test_openai():
    api_key = os.getenv('OPENAI_API_KEY')
    headers = {'Authorization': f'Bearer {api_key}'}
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.openai.com/v1/models', headers=headers, timeout=10) as resp:
            if resp.status == 200:
                print('✅ OpenAI API: Connected')
            else:
                print(f'❌ OpenAI API: Failed ({resp.status})')

asyncio.run(test_openai())
" || echo "❌ OpenAI API: Connection failed"
else
    echo "⚠️  OpenAI API: No API key configured"
fi

# Test Google
if [ ! -z "$GOOGLE_API_KEY" ]; then
    echo "🧠 Testing Google API..."
    python -c "
import asyncio
import aiohttp
import os

async def test_google():
    api_key = os.getenv('GOOGLE_API_KEY')
    headers = {'x-goog-api-key': api_key}
    async with aiohttp.ClientSession() as session:
        async with session.get('https://generativelanguage.googleapis.com/v1beta/models', headers=headers, timeout=10) as resp:
            if resp.status == 200:
                print('✅ Google API: Connected')
            else:
                print(f'❌ Google API: Failed ({resp.status})')

asyncio.run(test_google())
" || echo "❌ Google API: Connection failed"
else
    echo "⚠️  Google API: No API key configured"
fi

# Test Anthropic
if [ ! -z "$ANTHROPIC_API_KEY" ]; then
    echo "🧑‍🎓 Testing Anthropic API..."
    python -c "
import asyncio
import aiohttp
import os

async def test_anthropic():
    api_key = os.getenv('ANTHROPIC_API_KEY')
    headers = {'x-api-key': api_key}
    async with aiohttp.ClientSession() as session:
        async with session.get('https://api.anthropic.com/v1/models', headers=headers, timeout=10) as resp:
            if resp.status == 200:
                print('✅ Anthropic API: Connected')
            else:
                print(f'❌ Anthropic API: Failed ({resp.status})')

asyncio.run(test_anthropic())
" || echo "❌ Anthropic API: Connection failed"
fi

# Test OpenRouter
if [ ! -z "$OPENROUT_API_KEY" ]; then
    echo "🌐 Testing OpenRouter API..."
    python -c "
import asyncio
import aiohttp
import os

async def test_openrouter():
    api_key = os.getenv('OPENROUT_API_KEY')
    headers = {'Authorization': f'Bearer {api_key}', 'HTTP-Referer': 'http://localhost:8000', 'X-Title': 'RAG_07'}
    async with aiohttp.ClientSession() as session:
        async with session.get('https://openrouter.ai/api/v1/models', headers=headers, timeout=10) as resp:
            if resp.status == 200:
                print('✅ OpenRouter API: Connected')
            else:
                print(f'❌ OpenRouter API: Failed ({resp.status})')

asyncio.run(test_openrouter())
" || echo "❌ OpenRouter API: Connection failed"
fi

# Test Ollama (local)
echo "🦙 Testing Ollama (local)..."
python -c "
import asyncio
import aiohttp

async def test_ollama():
    async with aiohttp.ClientSession() as session:
        async with session.get('http://192.168.1.11:11434/api/tags', timeout=5) as resp:
            if resp.status == 200:
                print('✅ Ollama: Connected')
            else:
                print(f'❌ Ollama: Failed ({resp.status})')

asyncio.run(test_ollama())
" || echo "❌ Ollama: Connection failed"

# Test LM Studio (local)
echo "🎭 Testing LM Studio (local)..."
python -c "
import asyncio
import aiohttp

async def test_lmstudio():
    async with aiohttp.ClientSession() as session:
        async with session.get('http://192.168.1.11:1234/v1/models', timeout=5) as resp:
            if resp.status == 200:
                print('✅ LM Studio: Connected')
            else:
                print(f'❌ LM Studio: Failed ({resp.status})')

asyncio.run(test_lmstudio())
" || echo "❌ LM Studio: Connection failed"

echo ""
echo "✅ API connectivity tests completed!"
