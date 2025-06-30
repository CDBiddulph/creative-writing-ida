"""Node selection from generated sessions."""

from pathlib import Path
from typing import List, Tuple
import random
import xml.etree.ElementTree as ET


class NodeSelector:
    """Selects nodes from session trees for example generation."""

    def __init__(self, random_seed: int = None):
        """
        Initialize node selector with optional random seed.

        Args:
            random_seed: Optional seed for reproducible random selection
        """
        if random_seed is not None:
            random.seed(random_seed)

    def select_nodes_for_examples(
        self, sessions_dir: Path, num_examples: int
    ) -> List[Tuple[str, int, str]]:
        """
        Select random nodes from sessions for example generation.

        Args:
            sessions_dir: Directory containing session XML files
            num_examples: Number of nodes to select

        Returns:
            List of tuples (session_filename, node_id, prompt_text) for selected nodes

        Raises:
            ValueError: If not enough nodes available for selection
        """
        # Collect all nodes from all session files
        all_nodes = []

        for session_file in sessions_dir.glob("*.xml"):
            try:
                tree = ET.parse(session_file)
                sessions = tree.findall(".//session")

                for session in sessions:
                    session_id_elem = session.find("id")
                    prompt_elem = session.find("prompt")

                    if session_id_elem is not None and prompt_elem is not None:
                        node_id = int(session_id_elem.text)
                        prompt_text = prompt_elem.text
                        all_nodes.append((session_file.name, node_id, prompt_text))

            except (ET.ParseError, ValueError) as e:
                raise ValueError(f"XML parsing error in {session_file}: {e}")

        if len(all_nodes) < num_examples:
            raise ValueError(
                f"Not enough nodes available for selection. "
                f"Need {num_examples}, but only {len(all_nodes)} nodes found."
            )

        # Randomly select the requested number
        return random.sample(all_nodes, num_examples)
