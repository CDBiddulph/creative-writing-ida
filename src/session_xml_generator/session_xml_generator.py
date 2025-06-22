"""Interface for different API implementations (Claude or Human)."""

from abc import ABC, abstractmethod


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
