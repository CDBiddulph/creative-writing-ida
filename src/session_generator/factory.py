"""Factory function for creating session generators."""

from src.config import resolve_model_name, resolve_model_type
from src.session_generator.claude_chat import ClaudeChatSessionGenerator
from src.session_generator.session_generator import SessionGenerator


def get_session_generator(
    model: str,
    max_tokens: int,
    leaf_readme_path: str,
    parent_readme_path: str,
    temperature: float = 0.7,
    leaf_examples_xml_path: str = None,
    parent_examples_xml_path: str = None,
    shuffle_examples: bool = True,
) -> SessionGenerator:
    """
    Get the appropriate API interface based on mode.

    Args:
        model: Model name
        max_tokens: Maximum tokens to generate
        leaf_readme_path: Path to leaf README file
        parent_readme_path: Path to parent README file
        temperature: Temperature for generation
        leaf_examples_xml_path: Optional path to leaf examples XML
        parent_examples_xml_path: Optional path to parent examples XML
        shuffle_examples: Whether to shuffle examples during generation

    Returns:
        Appropriate API interface instance
    """
    model = resolve_model_name(model)
    model_type = resolve_model_type(model)

    # Only support chat models now
    # In the future, we may bring back ClaudeBaseSessionGenerator
    if model_type == "chat":
        return ClaudeChatSessionGenerator(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            leaf_readme_path=leaf_readme_path,
            parent_readme_path=parent_readme_path,
            leaf_examples_xml_path=leaf_examples_xml_path,
            parent_examples_xml_path=parent_examples_xml_path,
            shuffle_examples=shuffle_examples,
        )
    else:
        raise ValueError(f"Only chat models are supported, got: {model_type}")
