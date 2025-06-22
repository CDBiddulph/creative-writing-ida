"""Factory function for creating session XML generators."""

from src.config import resolve_model_name, resolve_model_type
from src.session_xml_generator.claude_base_xml import ClaudeBaseSessionXmlGenerator
from src.session_xml_generator.claude_chat_xml import ClaudeChatSessionXmlGenerator
from src.session_xml_generator.session_xml_generator import SessionXmlGenerator


def get_session_xml_generator(
    model: str,
    max_tokens: int,
    leaf_readme_path: str,
    parent_readme_path: str,
    temperature: float = 0.7,
    leaf_examples_xml_path: str = None,
    parent_examples_xml_path: str = None,
) -> SessionXmlGenerator:
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

    Returns:
        Appropriate API interface instance
    """
    model = resolve_model_name(model)
    model_type = resolve_model_type(model)
    if model_type == "base":
        return ClaudeBaseSessionXmlGenerator(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            leaf_readme_path=leaf_readme_path,
            parent_readme_path=parent_readme_path,
            leaf_examples_xml_path=leaf_examples_xml_path,
            parent_examples_xml_path=parent_examples_xml_path,
        )
    elif model_type == "chat":
        return ClaudeChatSessionXmlGenerator(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            leaf_readme_path=leaf_readme_path,
            parent_readme_path=parent_readme_path,
            leaf_examples_xml_path=leaf_examples_xml_path,
            parent_examples_xml_path=parent_examples_xml_path,
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")
