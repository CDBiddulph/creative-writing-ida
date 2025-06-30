"""Example aggregation and formatting."""

from pathlib import Path
from typing import List, Dict, Any
import xml.etree.ElementTree as ET
import random
import shutil

# Import existing XML formatting utilities
from ..xml_formatter import XmlFormatter
from .config import DataCollectionConfig


class ExampleAggregator:
    """Aggregates and formats examples from generated sessions."""

    def __init__(self, config: DataCollectionConfig):
        """Initialize example aggregator with configuration."""
        self.config = config
        self.xml_formatter = XmlFormatter()

    def create_examples_for_iteration(
        self, iteration_path: Path, iteration: int, experiment_path: Path
    ) -> None:
        """
        Create example files for an iteration.

        For iteration 0, copies seed examples. For subsequent iterations,
        extracts and aggregates examples from previous iteration sessions.

        Args:
            iteration_path: Path to current iteration directory
            iteration: Current iteration number (0-based)
            experiment_path: Path to experiment directory
        """
        examples_dir = iteration_path / "examples"
        examples_dir.mkdir(exist_ok=True)

        if iteration == 0:
            # Copy seed examples
            self._copy_seed_examples(examples_dir)
        else:
            # Generate examples from previous iterations
            self._generate_leaf_examples(examples_dir, experiment_path, iteration)
            self._generate_parent_examples(examples_dir, experiment_path, iteration)

    def _copy_seed_examples(self, examples_dir: Path) -> None:
        """Copy seed example files to examples directory."""
        leaf_dest = examples_dir / "leaf_examples.xml"
        parent_dest = examples_dir / "parent_examples.xml"

        shutil.copy2(self.config.seed_leaf_examples, leaf_dest)
        shutil.copy2(self.config.seed_parent_examples, parent_dest)

    def _generate_leaf_examples(
        self, examples_dir: Path, experiment_path: Path, iteration: int
    ) -> None:
        """Generate leaf examples from previous iteration's leaf sessions."""
        # Only get examples from the previous iteration (leaf examples reset each time)
        prev_iteration_path = experiment_path / f"iteration_{iteration - 1}"
        leaf_sessions_dir = prev_iteration_path / "leaf-sessions"

        leaf_examples = []

        if leaf_sessions_dir.exists():
            for session_file in leaf_sessions_dir.glob("*.xml"):
                try:
                    tree = ET.parse(session_file)

                    # Find root session (id=0)
                    root_session = None
                    for session in tree.findall(".//session"):
                        id_elem = session.find("id")
                        if id_elem is not None and id_elem.text == "0":
                            root_session = session
                            break

                    if root_session is not None:
                        # Extract prompt and final-response
                        prompt_elem = root_session.find("prompt")
                        final_response_elem = tree.find(".//final-response")

                        if prompt_elem is not None and final_response_elem is not None:
                            leaf_examples.append(
                                {
                                    "prompt": prompt_elem.text,
                                    "submit": final_response_elem.text,
                                }
                            )

                except ET.ParseError:
                    # Skip malformed files
                    continue

        # Save leaf examples
        self._save_examples(leaf_examples, examples_dir / "leaf_examples.xml", "leaf")

    def _generate_parent_examples(
        self, examples_dir: Path, experiment_path: Path, iteration: int
    ) -> None:
        """Generate parent examples by accumulating from all previous parent sessions."""
        parent_examples = []

        # Accumulate from all previous iterations (up to max_parent_examples)
        for prev_iter in range(iteration):
            prev_iteration_path = experiment_path / f"iteration_{prev_iter}"
            parent_sessions_dir = prev_iteration_path / "parent-sessions"

            if parent_sessions_dir.exists():
                for session_file in parent_sessions_dir.glob("*.xml"):
                    if len(parent_examples) >= self.config.max_parent_examples:
                        break

                    try:
                        tree = ET.parse(session_file)

                        # Find root session (id=0)
                        root_session = None
                        for session in tree.findall(".//session"):
                            id_elem = session.find("id")
                            if id_elem is not None and id_elem.text == "0":
                                root_session = session
                                break

                        if root_session is not None:
                            # Extract full session structure
                            example = {}

                            # Get all elements in order
                            for elem in root_session:
                                if elem.tag == "prompt":
                                    example["prompt"] = elem.text
                                elif elem.tag == "submit":
                                    example["submit"] = elem.text
                                elif elem.tag in ["notes", "ask", "response"]:
                                    # Handle multiple instances
                                    if elem.tag not in example:
                                        example[elem.tag] = []
                                    example[elem.tag].append(elem.text)

                            if "prompt" in example:
                                parent_examples.append(example)

                    except ET.ParseError:
                        # Skip malformed files
                        continue

                if len(parent_examples) >= self.config.max_parent_examples:
                    break

        # Save parent examples
        self._save_examples(
            parent_examples, examples_dir / "parent_examples.xml", "parent"
        )

    def _save_examples(
        self, examples: List[Dict[str, Any]], output_path: Path, example_type: str
    ) -> None:
        """Save examples to XML file with proper formatting."""
        # Create XML structure
        sessions_elem = ET.Element("sessions")

        for example in examples:
            session_elem = ET.SubElement(sessions_elem, "session")

            # Add prompt first
            if "prompt" in example:
                prompt_elem = ET.SubElement(session_elem, "prompt")
                prompt_elem.text = example["prompt"]

            if example_type == "parent":
                # Add all elements in order for parent examples
                # Handle notes, asks, responses as lists
                for key in ["notes", "ask", "response"]:
                    if key in example and isinstance(example[key], list):
                        for value in example[key]:
                            elem = ET.SubElement(session_elem, key)
                            elem.text = value

            # Add submit last
            if "submit" in example:
                submit_elem = ET.SubElement(session_elem, "submit")
                submit_elem.text = example["submit"]

        # Pretty print using existing formatter's indent method
        self.xml_formatter._indent(sessions_elem)

        # Create XML string with declaration
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml_str += ET.tostring(sessions_elem, encoding="unicode")

        output_path.write_text(xml_str)
