from typing import Literal

from pydantic import BaseModel, Field

# ─────────────────────────────────────────────────────────────
# 1. Literal types for model names (compile-time autocomplete)
# ─────────────────────────────────────────────────────────────
OpenAIModelName = Literal[
    "o3-deep-research-2025-06-26",
    "o4-mini-deep-research-2025-06-26",
    "gpt-5.2-2025-12-11",
    "gpt-5.2-pro-2025-12-11",
]

AnthropicModelName = Literal[
    "claude-sonnet-4-5-20250929",
    "claude-opus-4-5-20251101",
]

XAIModelName = Literal["grok-4-0709"]

# Union for general use
ModelName = OpenAIModelName | AnthropicModelName | XAIModelName


# ─────────────────────────────────────────────────────────────
# 2. Model config (just data, no provider coupling)
# ─────────────────────────────────────────────────────────────
class ModelConfig(BaseModel):
    """Immutable model configuration."""

    name: ModelName
    display_name: str  # Human-friendly name for UI
    description: str  # Short description for UI
    max_output_tokens: int = Field(ge=1000)
    max_input_tokens: int = Field(ge=1000)
    modalities: list[Literal["text", "image", "audio", "video"]] = Field(
        default=["text"]
    )
    is_default: bool = False  # Whether this is the default model for the provider

    model_config = {"frozen": True}


# ─────────────────────────────────────────────────────────────
# 3. Provider metadata for UI display
# ─────────────────────────────────────────────────────────────
class ProviderConfig(BaseModel):
    """Provider display configuration."""

    name: str  # Display name
    description: str  # Short description
    color: str  # CSS color class

    model_config = {"frozen": True}


PROVIDER_CONFIGS = {
    "openai": ProviderConfig(
        name="OpenAI",
        description="Advanced reasoning and deep research capabilities",
        color="bg-green-500",
    ),
    "anthropic": ProviderConfig(
        name="Anthropic",
        description="Extended thinking for deep insights",
        color="bg-purple-500",
    ),
    "xai": ProviderConfig(
        name="xAI",
        description="Technical depth and innovation focus",
        color="bg-blue-500",
    ),
}


# ─────────────────────────────────────────────────────────────
# 4. Typed registry with Literal keys (the magic)
# ─────────────────────────────────────────────────────────────
OPENAI_MODELS: dict[OpenAIModelName, ModelConfig] = {
    "o3-deep-research-2025-06-26": ModelConfig(
        name="o3-deep-research-2025-06-26",
        display_name="O3 Deep Research",
        description="Autonomous web research with real-time data",
        max_output_tokens=100000,
        max_input_tokens=200000,
        modalities=["text"],
        is_default=True,
    ),
    "o4-mini-deep-research-2025-06-26": ModelConfig(
        name="o4-mini-deep-research-2025-06-26",
        display_name="O4 Mini Deep Research",
        description="Faster research with efficient reasoning",
        max_output_tokens=100000,
        max_input_tokens=200000,
        modalities=["text"],
    ),
    "gpt-5.2-2025-12-11": ModelConfig(
        name="gpt-5.2-2025-12-11",
        display_name="GPT-5.2",
        description="Latest GPT model with enhanced capabilities",
        max_output_tokens=128000,
        max_input_tokens=400000,
        modalities=["text"],
    ),
    "gpt-5.2-pro-2025-12-11": ModelConfig(
        name="gpt-5.2-pro-2025-12-11",
        display_name="GPT-5.2 Pro",
        description="Professional tier with extended context",
        max_output_tokens=128000,
        max_input_tokens=400000,
        modalities=["text"],
    ),
}

ANTHROPIC_MODELS: dict[AnthropicModelName, ModelConfig] = {
    "claude-sonnet-4-5-20250929": ModelConfig(
        name="claude-sonnet-4-5-20250929",
        display_name="Claude Sonnet 4.5",
        description="Balanced performance with extended thinking",
        max_output_tokens=64000,
        max_input_tokens=1000000,
        modalities=["text"],
        is_default=True,
    ),
    "claude-opus-4-5-20251101": ModelConfig(
        name="claude-opus-4-5-20251101",
        display_name="Claude Opus 4.5",
        description="Most capable model for complex tasks",
        max_output_tokens=64000,
        max_input_tokens=200000,
        modalities=["text"],
    ),
}

XAI_MODELS: dict[XAIModelName, ModelConfig] = {
    "grok-4-0709": ModelConfig(
        name="grok-4-0709",
        display_name="Grok 4",
        description="Real-time knowledge with wit and depth",
        max_output_tokens=256000,
        max_input_tokens=256000,
        modalities=["text"],
        is_default=True,
    ),
}


# ─────────────────────────────────────────────────────────────
# 5. Helper to get all models grouped by provider
# ─────────────────────────────────────────────────────────────
def get_all_models_by_provider() -> dict:
    """Return all models grouped by provider with metadata."""
    return {
        "openai": {
            "provider": PROVIDER_CONFIGS["openai"].model_dump(),
            "models": [m.model_dump() for m in OPENAI_MODELS.values()],
        },
        "anthropic": {
            "provider": PROVIDER_CONFIGS["anthropic"].model_dump(),
            "models": [m.model_dump() for m in ANTHROPIC_MODELS.values()],
        },
        "xai": {
            "provider": PROVIDER_CONFIGS["xai"].model_dump(),
            "models": [m.model_dump() for m in XAI_MODELS.values()],
        },
    }
