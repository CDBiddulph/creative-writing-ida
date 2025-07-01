"""Node selection from generated sessions."""

from pathlib import Path
from typing import List, Tuple
import random

from ..xml_service import XmlService


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
        self.xml_service = XmlService()

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
        # Get all XML files
        xml_files = list(sessions_dir.glob("*.xml"))

        if len(xml_files) < num_examples:
            raise ValueError(
                f"Not enough files available for selection. "
                f"Need {num_examples}, but only {len(xml_files)} files found."
            )

        # Randomly select the requested number of files
        selected_files = random.sample(xml_files, num_examples)

        selected_nodes = []
        for xml_file in selected_files:
            sessions = self.xml_service.parse_sessions_file(xml_file)

            # Collect all nodes from this file
            file_nodes = []
            for session in sessions:
                prompt_text = session.get_prompt_text()
                file_nodes.append((xml_file.name, session.session_id, prompt_text))

            # Randomly select one node from this file
            if file_nodes:
                selected_node = random.choice(file_nodes)
                selected_nodes.append(selected_node)
            else:
                raise ValueError(f"No valid nodes found in file: {xml_file}")

        return selected_nodes
