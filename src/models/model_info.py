"""
Model information data structures.
Standardized format for model information across all providers.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class ModelCapabilities(Enum):
    """Model capabilities enum."""

    TEXT_GENERATION = "text_generation"
    EMBEDDINGS = "embeddings"
    TOOLS = "tools"
    VISION = "vision"
    CODE = "code"
    FUNCTION_CALLING = "function_calling"


@dataclass
class ModelPricing:
    """Model pricing information."""

    # USD per million input tokens
    input_price_per_million: Optional[float] = None
    # USD per million output tokens
    output_price_per_million: Optional[float] = None
    currency: str = "USD"


@dataclass
class ModelInfo:
    """Standardized model information structure."""

    id: str  # Model identifier
    name: str  # Human-readable name
    provider: str  # Provider name
    description: Optional[str] = None
    max_tokens: Optional[int] = None  # Maximum context length
    capabilities: List[ModelCapabilities] = None
    pricing: Optional[ModelPricing] = None
    multimodal: bool = False
    supports_tools: bool = False
    supports_streaming: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    deprecated: bool = False

    def __post_init__(self):
        """Initialize default values."""
        if self.capabilities is None:
            self.capabilities = []


@dataclass
class ModelListResponse:
    """Response structure for model list operations."""

    provider: str
    models: List[ModelInfo]
    total_count: int
    cached: bool = False
    cache_timestamp: Optional[str] = None
    error: Optional[str] = None

    def __post_init__(self):
        """Calculate total count if not provided."""
        if self.total_count == 0:
            self.total_count = len(self.models)
