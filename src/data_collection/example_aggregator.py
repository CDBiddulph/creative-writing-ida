"""Example aggregation and formatting."""

from pathlib import Path
from typing import List
import shutil
import logging

from ..session import Session, PromptEvent, SubmitEvent
from ..xml_service import XmlService
from .config import DataCollectionConfig


class ExampleAggregator:
    """Aggregates and formats examples from generated sessions."""

    def __init__(self, config: DataCollectionConfig):
        """Initialize example aggregator with configuration."""
        self.config = config
        self.xml_service = XmlService()

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

        if leaf_sessions_dir.exists():
            # Extract leaf examples: root session with prompt + final-response as submit
            leaf_sessions = self._extract_leaf_examples_from_trees(leaf_sessions_dir)
            # Write sessions directly to file
            if leaf_sessions:
                self.xml_service.write_sessions_file(
                    leaf_sessions, examples_dir / "leaf_examples.xml"
                )

    def _generate_parent_examples(
        self, examples_dir: Path, experiment_path: Path, iteration: int
    ) -> None:
        """Generate parent examples by accumulating from all previous parent sessions."""
        parent_sessions = []

        # Accumulate from all previous iterations (up to max_parent_examples)
        for prev_iter in range(iteration):
            prev_iteration_path = experiment_path / f"iteration_{prev_iter}"
            parent_sessions_dir = prev_iteration_path / "parent-sessions"

            if parent_sessions_dir.exists():
                # Extract parent examples: complete root session structure
                batch_sessions = self._extract_parent_examples_from_trees(
                    parent_sessions_dir,
                    self.config.max_parent_examples - len(parent_sessions),
                )
                parent_sessions.extend(batch_sessions)

                if len(parent_sessions) >= self.config.max_parent_examples:
                    break

        # Write sessions directly to file (empty list is valid)
        self.xml_service.write_sessions_file(
            parent_sessions, examples_dir / "parent_examples.xml"
        )

    def _extract_leaf_examples_from_trees(
        self, leaf_sessions_dir: Path
    ) -> List[Session]:
        """Extract leaf examples from tree files: root session prompt + final-response as submit."""

        leaf_sessions = []
        for xml_file in leaf_sessions_dir.glob("*.xml"):
            try:
                # Parse the full tree and extract final-response
                final_response = self.xml_service.extract_final_response(xml_file)
                if final_response is None:
                    logging.warning(f"No final response found for {xml_file}; skipping")
                    continue

                # Parse sessions and find root session (id=0)
                all_sessions = self.xml_service.parse_sessions_file(xml_file)
                root_session = None
                for session in all_sessions:
                    if session.session_id == 0:
                        root_session = session
                        break

                if root_session is None:
                    logging.warning(f"Root session not found for {xml_file}; skipping")
                    continue

                # Extract prompt from root session
                prompt_event = root_session.events[0] if root_session.events else None
                if not isinstance(prompt_event, PromptEvent):
                    logging.warning(
                        f"First event for {xml_file} is not a prompt event (found {type(prompt_event) if prompt_event else 'empty list'}); skipping"
                    )
                    continue

                # Create new leaf session with prompt + final-response as submit
                leaf_session = Session(session_id=len(leaf_sessions))
                leaf_session.add_event(PromptEvent(prompt_event.text))
                leaf_session.add_event(SubmitEvent(final_response))
                leaf_sessions.append(leaf_session)

                if len(leaf_sessions) >= self.config.leaf_examples_per_iteration:
                    break

            except Exception:
                logging.warning(f"Error parsing {xml_file}; skipping")
                continue

        return leaf_sessions

    def _extract_parent_examples_from_trees(
        self, parent_sessions_dir: Path, max_count: int
    ) -> List[Session]:
        """Extract parent examples from tree files: complete root session structure."""
        parent_sessions = []
        for xml_file in parent_sessions_dir.glob("*.xml"):
            try:
                # Parse sessions and find root session (id=0)
                all_sessions = self.xml_service.parse_sessions_file(xml_file)
                root_session = None
                for session in all_sessions:
                    if session.session_id == 0:
                        root_session = session
                        break

                if root_session is not None:
                    # Copy the root session and update its ID for the examples file
                    example_session = root_session.copy()
                    example_session.session_id = len(parent_sessions)
                    parent_sessions.append(example_session)

                    if len(parent_sessions) >= max_count:
                        break

            except Exception:
                # Skip malformed files
                continue

        return parent_sessions
