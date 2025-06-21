"""Configuration and constants for the tree simulation system."""

# Model name mappings for convenience
MODEL_MAPPINGS = {
    "opus": "claude-opus-4-20250514",
    "sonnet": "claude-sonnet-4-20250514",
    "haiku": "claude-3-5-haiku-20241022",
    "big-base": "as-hackathon-big-base-rollout",
    "little-base": "as-hackathon-little-base-rollout",
}

# Default file paths
DEFAULT_PARENT_README = "prompts/fiction_parent_readme.md"
DEFAULT_LEAF_README = "prompts/fiction_leaf_readme.md"
DEFAULT_OUTPUT_DIR = "sessions"

# Default model and parameters
DEFAULT_MODEL = "haiku"
DEFAULT_MAX_TOKENS = 2048
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TREE_DEPTH = 2


def resolve_model_name(model_name: str) -> str:
    """Resolve short model name to full model name."""
    return MODEL_MAPPINGS.get(model_name, model_name)


def resolve_model_type(model_name: str) -> str:
    """Resolve model name to model type."""
    return "base" if model_name.startswith("as-hackathon") else "chat"
