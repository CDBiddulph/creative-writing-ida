"""Interface for different API implementations (Claude or Human)."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List
from ..session import Session
from ..xml_service import XmlService


class SessionGenerator(ABC):
    """Abstract interface for generating sessions.

    Given a prompt and existing files for the LLM to use, generate a complete Session.

    Args:
        model: Model name
        max_tokens: Maximum tokens to generate
        temperature: Temperature for generation
        leaf_readme_path: Path to leaf README file
        parent_readme_path: Path to parent README file
        leaf_examples_xml_path: Path to leaf examples XML file
        parent_examples_xml_path: Path to parent examples XML file
    """

    STOP_SEQUENCES = ["</ask>", "</submit>"]

    def __init__(
        self,
        model: str,
        max_tokens: int,
        leaf_readme_path: str,
        parent_readme_path: str,
        temperature: float = 0.7,
        leaf_examples_xml_path: str | None = None,
        parent_examples_xml_path: str | None = None,
    ):
        self.model = model
        self.max_tokens = max_tokens
        self.leaf_readme_path = leaf_readme_path
        self.parent_readme_path = parent_readme_path
        self.temperature = temperature
        self.leaf_examples_xml_path = leaf_examples_xml_path
        self.parent_examples_xml_path = parent_examples_xml_path
        self.xml_service = XmlService()

    @abstractmethod
    def generate_leaf(
        self, prompt: str, session_id: int, max_retries: int = 3
    ) -> Session:
        """Generate a leaf session."""
        pass

    @abstractmethod
    def generate_parent(
        self, prompt: str, session_id: int, max_retries: int = 3
    ) -> Session:
        """Generate a parent session."""
        pass

    @abstractmethod
    def continue_parent(
        self, current_session: Session, max_retries: int = 3
    ) -> Session:
        """Continue generating a parent session from existing Session."""
        pass

    def _load_readme_content(self, readme_path: str) -> str:
        """Load README content from file."""
        with open(readme_path, "r") as f:
            return f.read()

    def _load_examples_sessions(self, examples_path: str | None) -> List[Session]:
        """Load example sessions from XML file or return empty list."""
        if examples_path is None:
            return []

        return self.xml_service.parse_sessions_file(Path(examples_path))
