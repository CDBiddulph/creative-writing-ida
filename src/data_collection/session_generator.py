"""Session generation using the existing tree runner system."""

from pathlib import Path
from typing import List, Tuple
import random
import xml.etree.ElementTree as ET

from .config import DataCollectionConfig
from .node_selector import NodeSelector
from .prompt_sampler import PromptSampler

# Import existing tree runner components
from ..tree_runner import TreeRunner
from ..tree_runner_config import TreeRunnerConfig


class SessionGenerator:
    """Generates sessions using the tree runner system."""

    def __init__(self, config: DataCollectionConfig):
        """
        Initialize session generator with configuration.

        Args:
            config: Data collection configuration containing tree runner parameters
        """
        self.config = config
        self.node_selector = NodeSelector()
        self.prompt_sampler = PromptSampler(config.writing_prompts_path)

    def _count_existing_parent_examples(
        self, iteration_path: Path, iteration: int
    ) -> int:
        """Count parent examples from the current iteration's parent_examples.xml file."""
        if iteration == 0:
            # Seed examples from the first iteration don't count toward our parent example total
            return 0

        examples_dir = iteration_path / "examples"
        if not examples_dir.exists():
            raise FileNotFoundError(f"Examples directory not found: {examples_dir}")

        parent_examples_path = examples_dir / "parent_examples.xml"
        if not parent_examples_path.exists():
            raise FileNotFoundError(
                f"Parent examples file not found: {parent_examples_path}"
            )

        # Parse XML and count session elements
        try:
            tree = ET.parse(parent_examples_path)
            root = tree.getroot()
            return len(root.findall("session"))
        except Exception as e:
            raise ValueError(
                f"Failed to parse parent examples XML from {parent_examples_path}: {e}"
            )

    def _calculate_iteration_needs(
        self, iteration_path: Path, iteration: int
    ) -> tuple[int, int]:
        """Calculate how many parent examples and prompts are needed for this iteration.

        Returns:
            tuple: (effective_parent_examples, prompts_needed)
        """
        # Count existing parent examples to determine how many more we need
        existing_parent_count = self._count_existing_parent_examples(
            iteration_path, iteration
        )
        remaining_parent_needed = max(
            0, self.config.max_parent_examples - existing_parent_count
        )

        # Calculate effective parent examples for this iteration
        effective_parent_examples = min(
            self.config.parent_examples_per_iteration, remaining_parent_needed
        )

        # Calculate prompts needed (max of parent and leaf requirements)
        prompts_needed = max(
            self.config.leaf_examples_per_iteration, effective_parent_examples
        )

        return effective_parent_examples, prompts_needed

    def _setup_session_directories(
        self, iteration_path: Path, effective_parent_examples: int
    ) -> dict[str, Path]:
        """Create necessary directories for session generation.

        Returns:
            dict: Mapping of directory names to paths
        """
        dirs = {
            "examples": iteration_path / "examples",
            "sample_sessions": iteration_path / "sample-sessions",
            "leaf_sessions": iteration_path / "leaf-sessions",
        }

        dirs["sample_sessions"].mkdir(exist_ok=True)
        dirs["leaf_sessions"].mkdir(exist_ok=True)

        if effective_parent_examples > 0:
            dirs["parent_sessions"] = iteration_path / "parent-sessions"
            dirs["parent_sessions"].mkdir(exist_ok=True)

        return dirs

    def generate_sessions_for_iteration(
        self, iteration_path: Path, experiment_path: Path, iteration: int
    ) -> None:
        """
        Generate all sessions needed for an iteration.

        Handles prompt sampling, parent example counting, and session generation.

        Args:
            iteration_path: Path to iteration directory
            experiment_path: Path to experiment root directory
            iteration: Current iteration number
        """
        # Calculate how many parent examples and prompts we need
        effective_parent_examples, prompts_needed = self._calculate_iteration_needs(
            iteration_path, iteration
        )

        # Sample prompts for this iteration
        try:
            prompts = self.prompt_sampler.sample_prompts_for_iteration(
                experiment_path, iteration, prompts_needed
            )
        except ValueError as e:
            raise RuntimeError(f"Prompt sampling failed: {e}")

        # Set up directories for session generation
        dirs = self._setup_session_directories(
            iteration_path, effective_parent_examples
        )

        # Generate sample sessions from writing prompts
        self._generate_sample_sessions(
            prompts, dirs["sample_sessions"], dirs["examples"]
        )

        # Generate parent sessions if needed
        if effective_parent_examples > 0:
            self._generate_parent_sessions(
                dirs["sample_sessions"], dirs["parent_sessions"], dirs["examples"]
            )

        # Generate leaf sessions from selected nodes in sample sessions
        self._generate_leaf_sessions(
            dirs["sample_sessions"], dirs["leaf_sessions"], dirs["examples"]
        )

    def _create_tree_runner_config(
        self, max_depth: int, output_dir: Path, examples_dir: Path
    ) -> TreeRunnerConfig:
        """Create a TreeRunner configuration with common settings."""
        return TreeRunnerConfig(
            model=self.config.model,
            max_depth=max_depth,
            output_dir=str(output_dir),
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            leaf_readme_path=self.config.leaf_readme_path,
            parent_readme_path=self.config.parent_readme_path,
            leaf_examples_xml_path=str(examples_dir / "leaf_examples.xml"),
            parent_examples_xml_path=str(examples_dir / "parent_examples.xml"),
        )

    def _sanitize_prompt_for_filename(self, prompt_text: str) -> str:
        """Sanitize prompt text for use in filenames."""
        return (
            prompt_text[:30]
            .lower()
            .replace(" ", "-")
            .replace("'", "")
            .replace("?", "")
            .replace("!", "")
        )

    def _move_output_file(
        self, source_filename: str, output_dir: Path, target_filename: str
    ) -> None:
        """Move a file from TreeRunner output to target location."""
        source_path = output_dir / source_filename
        target_path = output_dir / target_filename
        if source_path.exists():
            source_path.rename(target_path)

    def _generate_sample_sessions(
        self,
        prompts: List[Tuple[int, str]],
        sample_sessions_dir: Path,
        examples_dir: Path,
    ) -> None:
        """Generate sample sessions from writing prompts using tree runner."""
        config = self._create_tree_runner_config(
            self.config.sample_max_depth, sample_sessions_dir, examples_dir
        )
        runner = TreeRunner(config)

        for prompt_index, prompt_text in prompts:
            try:
                # Add story prefix to prompt
                story_prompt = (
                    f"Write a story using the following prompt: {prompt_text}"
                )

                # Generate session tree
                output_filename = runner.run(story_prompt)

                # Create target filename
                sanitized_prompt = self._sanitize_prompt_for_filename(prompt_text)
                target_filename = f"{prompt_index}-{sanitized_prompt}.xml"

                # Move file to proper location
                self._move_output_file(
                    output_filename, sample_sessions_dir, target_filename
                )

            except Exception as e:
                raise RuntimeError(
                    f"Sample session generation failed for prompt {prompt_index}: {e}"
                )

    def _generate_leaf_sessions(
        self, sample_sessions_dir: Path, leaf_sessions_dir: Path, examples_dir: Path
    ) -> None:
        """Generate leaf sessions from selected nodes in sample sessions."""
        # Select nodes from sample sessions
        try:
            selected_nodes = self.node_selector.select_nodes_for_examples(
                sample_sessions_dir, self.config.leaf_examples_per_iteration
            )
        except ValueError:
            # Not enough nodes available - this is ok, just generate what we can
            selected_nodes = []

        if not selected_nodes:
            return

        # Create TreeRunner config for leaf generation
        config = self._create_tree_runner_config(
            self.config.leaf_max_depth, leaf_sessions_dir, examples_dir
        )
        runner = TreeRunner(config)

        for filename, node_id, prompt_text in selected_nodes:
            try:
                # Extract original prompt index from filename
                prompt_index = filename.split("-", 1)[0]

                # Generate leaf session
                output_filename = runner.run(prompt_text)

                # Create proper filename for leaf session
                sanitized_prompt = self._sanitize_prompt_for_filename(prompt_text)
                target_filename = f"{prompt_index}-{node_id}-{sanitized_prompt}.xml"

                # Move file to proper location
                self._move_output_file(
                    output_filename, leaf_sessions_dir, target_filename
                )

            except Exception as e:
                raise RuntimeError(
                    f"Leaf session generation failed for node {node_id}: {e}"
                )

    def _generate_parent_sessions(
        self,
        sample_sessions_dir: Path,
        parent_sessions_dir: Path,
        examples_dir: Path,
    ) -> None:
        """Generate parent sessions from selected nodes in sample sessions."""
        raise NotImplementedError(
            "Parent example generation requires a web UI for human interaction, "
            "which is not yet implemented. Parent examples can only be created "
            "through manual human curation via the planned web interface."
        )
