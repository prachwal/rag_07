"""
Model cache manager for storing and retrieving model information.
Provides caching functionality to avoid frequent API calls for model lists.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from src.models.model_info import ModelListResponse
from src.utils.logger import LoggerMixin


class ModelCacheManager(LoggerMixin):
    """Manages caching of model information."""

    def __init__(self, cache_dir: str = "cache/models"):
        """Initialize cache manager."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_ttl = timedelta(hours=24)  # Cache TTL: 24 hours

    def _get_cache_file(self, provider: str) -> Path:
        """Get cache file path for provider."""
        return self.cache_dir / f"{provider}_models.json"

    def _is_cache_valid(self, cache_file: Path) -> bool:
        """Check if cache file is valid and not expired."""
        if not cache_file.exists():
            return False

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            cache_time = datetime.fromisoformat(data.get('timestamp', ''))
            return datetime.now() - cache_time < self.cache_ttl
        except (json.JSONDecodeError, ValueError, KeyError):
            return False

    def get_cached_models(self, provider: str) -> Optional[ModelListResponse]:
        """Get cached model list for provider."""
        cache_file = self._get_cache_file(provider)

        if not self._is_cache_valid(cache_file):
            return None

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Reconstruct ModelListResponse from cached data
            from src.models.model_info import ModelCapabilities, ModelInfo, ModelPricing

            models = []
            for model_data in data.get('models', []):
                # Reconstruct pricing if present
                pricing = None
                if model_data.get('pricing'):
                    pricing_data = model_data['pricing']
                    pricing = ModelPricing(
                        input_price_per_million=pricing_data.get(
                            'input_price_per_million'
                        ),
                        output_price_per_million=pricing_data.get(
                            'output_price_per_million'
                        ),
                        currency=pricing_data.get('currency', 'USD'),
                    )

                # Reconstruct capabilities
                capabilities = []
                for cap_str in model_data.get('capabilities', []):
                    try:
                        capabilities.append(ModelCapabilities(cap_str))
                    except ValueError:
                        continue  # Skip invalid capabilities

                model = ModelInfo(
                    id=model_data['id'],
                    name=model_data['name'],
                    provider=model_data['provider'],
                    description=model_data.get('description'),
                    max_tokens=model_data.get('max_tokens'),
                    capabilities=capabilities,
                    pricing=pricing,
                    multimodal=model_data.get('multimodal', False),
                    supports_tools=model_data.get('supports_tools', False),
                    supports_streaming=model_data.get('supports_streaming', False),
                    created_at=model_data.get('created_at'),
                    updated_at=model_data.get('updated_at'),
                    deprecated=model_data.get('deprecated', False),
                )
                models.append(model)

            response = ModelListResponse(
                provider=data['provider'],
                models=models,
                total_count=data['total_count'],
                cached=True,
                cache_timestamp=data['timestamp'],
            )

            self.log_operation(
                'loaded_cached_models', provider=provider, count=len(models)
            )
            return response

        except (json.JSONDecodeError, KeyError) as e:
            self.log_error(e, 'failed_to_load_cache', provider=provider)
            return None

    def cache_models(self, models_response: ModelListResponse) -> None:
        """Cache model list response."""
        cache_file = self._get_cache_file(models_response.provider)

        try:
            # Convert to JSON-serializable format
            models_data = []
            for model in models_response.models:
                model_data = {
                    'id': model.id,
                    'name': model.name,
                    'provider': model.provider,
                    'description': model.description,
                    'max_tokens': model.max_tokens,
                    'capabilities': [cap.value for cap in model.capabilities],
                    'multimodal': model.multimodal,
                    'supports_tools': model.supports_tools,
                    'supports_streaming': model.supports_streaming,
                    'created_at': model.created_at,
                    'updated_at': model.updated_at,
                    'deprecated': model.deprecated,
                }

                if model.pricing:
                    model_data['pricing'] = {
                        'input_price_per_million': (
                            model.pricing.input_price_per_million
                        ),
                        'output_price_per_million': (
                            model.pricing.output_price_per_million
                        ),
                        'currency': model.pricing.currency,
                    }

                models_data.append(model_data)

            cache_data = {
                'provider': models_response.provider,
                'models': models_data,
                'total_count': models_response.total_count,
                'timestamp': datetime.now().isoformat(),
            }

            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)

            self.log_operation(
                'cached_models',
                provider=models_response.provider,
                count=len(models_response.models),
            )

        except Exception as e:
            self.log_error(
                e, 'failed_to_cache_models', provider=models_response.provider
            )

    def clear_cache(self, provider: Optional[str] = None) -> None:
        """Clear cache for specific provider or all providers."""
        if provider:
            cache_file = self._get_cache_file(provider)
            if cache_file.exists():
                cache_file.unlink()
                self.log_operation('cleared_cache', provider=provider)
        else:
            # Clear all cache files
            for cache_file in self.cache_dir.glob("*_models.json"):
                cache_file.unlink()
            self.log_operation('cleared_all_cache')

    def list_cached_providers(self) -> list[str]:
        """List providers with cached data."""
        providers = []
        for cache_file in self.cache_dir.glob("*_models.json"):
            provider_name = cache_file.stem.replace('_models', '')
            if self._is_cache_valid(cache_file):
                providers.append(provider_name)
        return providers

    def get_all_cached_models(self) -> dict[str, list[str]]:
        """Get all cached models organized by provider, filtered for RAG compatibility."""
        result = {}
        for provider in self.list_cached_providers():
            models_response = self.get_cached_models(provider)
            if models_response and models_response.models:
                # Filter models for RAG compatibility
                compatible_models = []
                for model in models_response.models:
                    # Skip deprecated models
                    if model.deprecated:
                        continue

                    # For RAG operations, prefer models with function calling
                    # but also include basic text generation models
                    has_function_calling = model.supports_tools or any(
                        'function_calling' in str(cap).lower()
                        for cap in model.capabilities
                    )

                    has_text_generation = any(
                        'text_generation' in str(cap).lower()
                        for cap in model.capabilities
                    )

                    # Include if it has text generation capabilities
                    # Prioritize models with function calling for better RAG
                    if has_text_generation:
                        # Check token limit - prefer models with sufficient context
                        min_tokens = 2000  # Minimum for basic RAG
                        if model.max_tokens is None or model.max_tokens >= min_tokens:
                            compatible_models.append(model.id)
                        elif model.max_tokens and model.max_tokens >= 1000:
                            # Include smaller models but mark them
                            compatible_models.append(f"{model.id} (limited context)")

                # Sort models: function calling first, then by name
                def sort_key(model_id):
                    # Find the original model for sorting
                    original_model = next(
                        (
                            m
                            for m in models_response.models
                            if m.id == model_id.split(' ')[0]
                        ),
                        None,
                    )
                    if original_model:
                        has_fc = original_model.supports_tools or any(
                            'function_calling' in str(cap).lower()
                            for cap in original_model.capabilities
                        )
                        return (0 if has_fc else 1, model_id)
                    return (2, model_id)

                compatible_models.sort(key=sort_key)

                if compatible_models:
                    result[provider] = compatible_models
        return result
