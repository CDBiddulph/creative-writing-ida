"""Interface for different API implementations (Claude or Human)."""

from abc import ABC, abstractmethod
from config import resolve_model_type

CLI_SIMULATION_SYSTEM_PROMPT = "The assistant is in CLI simulation mode, and responds to the user's CLI commands only with the output of the command."


class SessionXmlGenerator(ABC):
    """Abstract interface for generating sessions in XML format."""

    def __init__(
        self,
        model: str,
        max_tokens: int,
        temperature: float = 0.7,
        leaf_readme_path: str = None,
        parent_readme_path: str = None,
        leaf_examples_xml_path: str = None,
        parent_examples_xml_path: str = None,
    ):
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.leaf_readme_path = leaf_readme_path
        self.parent_readme_path = parent_readme_path
        self.leaf_examples_xml_path = leaf_examples_xml_path
        self.parent_examples_xml_path = parent_examples_xml_path

    @abstractmethod
    def generate_leaf(self, prompt: str) -> str:
        """Generate a leaf session."""
        pass

    @abstractmethod
    def generate_parent(self, prompt: str) -> str:
        """Generate a parent session."""
        pass


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
        model_type: 'base', 'chat'
        readme_content: README content string for claude modes

    Returns:
        Appropriate API interface instance
    """
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
