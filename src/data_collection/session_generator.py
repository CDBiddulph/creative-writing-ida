"""Session generation using the existing tree runner system."""

from pathlib import Path
from typing import List, Tuple
import re

from .config import DataCollectionConfig
from .node_selector import NodeSelector
from .prompt_sampler import PromptSampler
from ..xml_service import XmlService

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
        self.xml_service = XmlService()

    def _count_existing_parent_examples(
        self, iteration_path: Path, iteration: int
    ) -> int:
        """Count parent examples from the current iteration's parent_examples.xml file."""
        # Seed examples from the first iteration don't count toward our parent example total
        # unless keep_seed_parent_examples is True
        if iteration == 0 and not self.config.keep_seed_parent_examples:
            return 0

        parent_examples_path = iteration_path / "examples" / "parent_examples.xml"
        if not parent_examples_path.exists():
            return 0  # No parent examples file means no parent examples

        # Parse XML and count sessions using XmlService
        try:
            return self.xml_service.count_sessions(parent_examples_path)
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
                dirs["sample_sessions"],
                dirs["parent_sessions"],
                dirs["examples"],
                effective_parent_examples,
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
        # Convert to lowercase and strip leading/trailing whitespace
        text = prompt_text.lower().strip()
        # Remove all non-alphanumeric characters (keeping spaces for now)
        text = re.sub(r"[^a-z0-9\s]", "", text)
        # Replace one or more whitespace characters with a single hyphen
        text = re.sub(r"\s+", "-", text)
        # If the result is empty, use a fallback
        if not text:
            text = "unknown"
        # Take only the first 30 characters
        return text[:30]

    def _move_output_file(
        self, source_filename: str, output_dir: Path, target_filename: str
    ) -> None:
        """Move a file from TreeRunner output to target location."""
        source_path = output_dir / source_filename
        target_path = output_dir / target_filename

        if not source_path.exists():
            raise FileNotFoundError(
                f"TreeRunner output file not found: {source_path}. "
                f"TreeRunner may have failed to generate the expected output."
            )

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
        # If no leaf sessions are requested, return early
        if self.config.leaf_examples_per_iteration == 0:
            return

        # Select nodes from sample sessions
        try:
            selected_nodes = self.node_selector.select_nodes_for_examples(
                sample_sessions_dir, self.config.leaf_examples_per_iteration
            )
        except ValueError as e:
            # Check if this is specifically about insufficient nodes
            if "not enough" in str(e).lower() or "insufficient" in str(e).lower():
                raise RuntimeError(
                    f"Cannot generate {self.config.leaf_examples_per_iteration} leaf sessions: {e}. "
                    f"Sample sessions may not have enough nodes for selection."
                )
            else:
                # Re-raise other ValueErrors as they indicate real problems
                raise RuntimeError(f"Node selection failed: {e}")

        if not selected_nodes:
            raise RuntimeError(
                f"Node selector returned empty list despite requesting "
                f"{self.config.leaf_examples_per_iteration} leaf sessions. "
                f"This indicates a problem with node selection logic."
            )

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
        effective_parent_examples: int,
    ) -> None:
        """Generate parent sessions from selected nodes in sample sessions."""
        raise NotImplementedError(
            "Parent example generation requires a web UI for human interaction, "
            "which is not yet implemented. Parent examples can only be created "
            "through manual human curation via the planned web interface."
        )
