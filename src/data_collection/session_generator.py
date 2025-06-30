"""Session generation using the existing tree runner system."""

from pathlib import Path
from typing import List, Tuple
import random

from .config import DataCollectionConfig
from .node_selector import NodeSelector

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

    def generate_sessions_for_iteration(
        self, iteration_path: Path, prompts: List[Tuple[int, str]], examples_dir: Path
    ) -> None:
        """
        Generate all sessions needed for an iteration.

        Creates sample sessions from writing prompts, then generates leaf sessions
        from selected nodes in those sample sessions.

        Args:
            iteration_path: Path to iteration directory
            prompts: List of (prompt_index, prompt_text) tuples to generate from
            examples_dir: Directory containing current iteration's example files
        """
        # Create directories
        sample_sessions_dir = iteration_path / "sample-sessions"
        leaf_sessions_dir = iteration_path / "leaf-sessions"
        sample_sessions_dir.mkdir(exist_ok=True)
        leaf_sessions_dir.mkdir(exist_ok=True)

        # Generate sample sessions from writing prompts
        self._generate_sample_sessions(prompts, sample_sessions_dir, examples_dir)

        # Generate leaf sessions from selected nodes
        self._generate_leaf_sessions(
            sample_sessions_dir, leaf_sessions_dir, examples_dir
        )

    def _generate_sample_sessions(
        self,
        prompts: List[Tuple[int, str]],
        sample_sessions_dir: Path,
        examples_dir: Path,
    ) -> None:
        """Generate sample sessions from writing prompts using tree runner."""
        # Create TreeRunner config for sample generation
        sample_config = TreeRunnerConfig(
            model=self.config.model,
            max_depth=self.config.sample_max_depth,
            output_dir=str(sample_sessions_dir),
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            leaf_readme_path=self.config.leaf_readme_path,
            parent_readme_path=self.config.parent_readme_path,
            prompt="",  # Will be set per prompt in the loop
            leaf_examples_xml_path=str(examples_dir / "leaf_examples.xml"),
            parent_examples_xml_path=str(examples_dir / "parent_examples.xml"),
        )

        sample_runner = TreeRunner(sample_config)

        for prompt_index, prompt_text in prompts:
            try:
                # Add story prefix to prompt
                story_prompt = (
                    f"Write a story using the following prompt: {prompt_text}"
                )

                # Update config with current prompt
                sample_config.prompt = story_prompt

                # Generate session tree
                output_filename = sample_runner.run(story_prompt)

                # Move/rename to sample-sessions directory with proper naming
                # Truncate prompt for filename (first 30 chars, replace spaces with hyphens)
                truncated_prompt = (
                    prompt_text[:30]
                    .lower()
                    .replace(" ", "-")
                    .replace("'", "")
                    .replace("?", "")
                    .replace("!", "")
                )
                target_filename = f"{prompt_index}-{truncated_prompt}.xml"
                target_path = sample_sessions_dir / target_filename

                # TreeRunner returns just the filename, file is saved in output_dir
                source_path = Path(sample_config.output_dir) / output_filename
                if source_path.exists():
                    source_path.rename(target_path)

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
        leaf_config = TreeRunnerConfig(
            model=self.config.model,
            max_depth=self.config.leaf_max_depth,
            output_dir=str(leaf_sessions_dir),
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            leaf_readme_path=self.config.leaf_readme_path,
            parent_readme_path=self.config.parent_readme_path,
            prompt="",  # Will be set per prompt in the loop
            leaf_examples_xml_path=str(examples_dir / "leaf_examples.xml"),
            parent_examples_xml_path=str(examples_dir / "parent_examples.xml"),
        )

        leaf_runner = TreeRunner(leaf_config)

        for filename, node_id, prompt_text in selected_nodes:
            try:
                # Extract original prompt index from filename
                prompt_index = filename.split("-", 1)[0]

                # Update config with current prompt
                leaf_config.prompt = prompt_text

                # Generate leaf session
                output_filename = leaf_runner.run(prompt_text)

                # Create proper filename for leaf session
                truncated_prompt = (
                    prompt_text[:30]
                    .lower()
                    .replace(" ", "-")
                    .replace("'", "")
                    .replace("?", "")
                    .replace("!", "")
                )
                target_filename = f"{prompt_index}-{node_id}-{truncated_prompt}.xml"
                target_path = leaf_sessions_dir / target_filename

                # TreeRunner returns just the filename, file is saved in output_dir
                source_path = Path(leaf_config.output_dir) / output_filename
                if source_path.exists():
                    source_path.rename(target_path)

            except Exception as e:
                raise RuntimeError(
                    f"Leaf session generation failed for node {node_id}: {e}"
                )
