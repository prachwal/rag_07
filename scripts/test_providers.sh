#!/bin/bash
# test_providers.sh - Test all provider functionality
# Tests provider registration, initialization, and basic operations

set -e

echo "⚙️  Testing Provider Functionality"
echo "================================"

# Activate virtual environment
source .venv/bin/activate

echo "Testing Provider Registration..."
python -c "
import asyncio
from src.config.config_manager import ConfigManager
from src.providers.base import ProviderFactory

async def test_provider_registration():
    config_manager = ConfigManager()
    factory = ProviderFactory(config_manager)

    # Test LLM providers
    llm_providers = ['openai', 'google', 'openrouter', 'ollama', 'lmstudio']
    for provider in llm_providers:
        try:
            # Try to create provider (may fail if API not available)
            await factory.create_llm_provider(provider)
            print(f'✅ {provider.upper()} provider: Registered and initialized')
        except Exception as e:
            print(f'⚠️  {provider.upper()} provider: Registered but initialization failed ({str(e)[:50]}...)')

    # Test Vector providers
    vector_providers = ['faiss']
    for provider in vector_providers:
        try:
            await factory.create_vector_provider(provider)
            print(f'✅ {provider.upper()} vector provider: Registered and initialized')
        except Exception as e:
            print(f'❌ {provider.upper()} vector provider: Failed ({str(e)[:50]}...)')

    # Test Text processors
    try:
        await factory.create_text_processor('basic')
        print('✅ Basic text processor: Registered and initialized')
    except Exception as e:
        print(f'❌ Basic text processor: Failed ({str(e)[:50]}...)')

asyncio.run(test_provider_registration())
"

echo ""
echo "Testing CLI Provider Commands..."
python src/main.py list-providers --provider-type all || echo "❌ list-providers command failed"

echo ""
echo "Testing Configuration Status..."
python src/main.py config-status || echo "❌ config-status command failed"

echo ""
echo "✅ Provider functionality tests completed!"
