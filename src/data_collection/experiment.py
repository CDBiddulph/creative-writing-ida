"""Experiment management for data collection."""

from pathlib import Path

from .config import DataCollectionConfig
from .file_manager import FileManager
from .session_generator import SessionGenerator
from .example_aggregator import ExampleAggregator


class Experiment:
    """Manages the lifecycle of a data collection experiment."""

    def __init__(self, config: DataCollectionConfig, base_dir: Path):
        """
        Initialize experiment with configuration.

        Args:
            config: Data collection configuration
            base_dir: Base directory for experiment
        """
        self.config = config

        # Set up experiment directory
        self.experiment_path = base_dir / config.experiment_id

        self.file_manager = FileManager(self.experiment_path)
        self.session_generator = SessionGenerator(config)
        self.example_aggregator = ExampleAggregator(config)

    def run(self) -> None:
        """
        Run the complete data collection experiment.

        Creates or resumes experiment, runs all iterations until completion,
        and outputs final results.

        Raises:
            ValueError: If experiment configuration is invalid
            RuntimeError: If experiment cannot be completed
        """
        # Setup or resume experiment
        current_iteration = self._setup_or_resume_experiment()

        if current_iteration == 0:
            print(f"Starting new experiment '{self.config.experiment_id}'")
        else:
            print(
                f"WARNING: Resuming existing experiment '{self.config.experiment_id}' at iteration {current_iteration}"
            )
            print(f"Existing experiment directory: {self.experiment_path}")

        # Check if experiment is already complete
        if current_iteration >= self.config.max_iterations:
            print(
                f"Experiment '{self.config.experiment_id}' is already complete ({self.config.max_iterations} iterations)"
            )
            print(f"Final command: {self.get_final_command()}")
            return

        # Run iterations until completion
        while current_iteration < self.config.max_iterations:
            print(f"Running iteration {current_iteration}...")

            try:
                self._run_iteration(current_iteration)
                current_iteration += 1
            except Exception as e:
                raise RuntimeError(f"Iteration {current_iteration} failed: {e}")

        print(
            f"Experiment '{self.config.experiment_id}' completed after {self.config.max_iterations} iterations"
        )
        print(f"Final command: {self.get_final_command()}")

    def get_final_command(self) -> str:
        """
        Get the final tree_runner_main command to use generated examples.

        Returns:
            Complete command string with paths to final example files
        """
        # Get the final iteration's examples
        final_iteration = self.config.max_iterations - 1
        final_iteration_path = self.experiment_path / f"iteration_{final_iteration}"

        leaf_examples_path = final_iteration_path / "examples" / "leaf_examples.xml"
        parent_examples_path = final_iteration_path / "examples" / "parent_examples.xml"

        return (
            f"python src/tree_runner_main.py "
            f"--model {self.config.model} "
            f"--max-depth {self.config.leaf_max_depth} "
            f"--temperature {self.config.temperature} "
            f"--max-tokens {self.config.max_tokens} "
            f"--leaf-readme-path {self.config.leaf_readme_path} "
            f"--parent-readme-path {self.config.parent_readme_path} "
            f"--leaf-examples-xml-path {leaf_examples_path} "
            f"--parent-examples-xml-path {parent_examples_path} "
            f'--prompt "Your prompt here"'
        )

    def _setup_or_resume_experiment(self) -> int:
        """Setup new experiment or resume existing one. Returns starting iteration."""
        if self.experiment_path.exists():
            # Resume existing experiment
            return self._find_next_iteration()
        else:
            # Create new experiment
            self.file_manager.setup_experiment(self.config.__dict__)
            return 0

    def _find_next_iteration(self) -> int:
        """Find the next iteration to run in an existing experiment."""
        iteration_dirs = list(self.experiment_path.glob("iteration_*"))
        if not iteration_dirs:
            return 0

        # Find the highest numbered iteration
        iteration_numbers = []
        for iter_dir in iteration_dirs:
            try:
                iter_num = int(iter_dir.name.split("_")[1])
                iteration_numbers.append(iter_num)
            except (IndexError, ValueError):
                continue

        if not iteration_numbers:
            return 0

        return max(iteration_numbers) + 1

    def _run_iteration(self, iteration: int) -> None:
        """Run a complete iteration of the data collection process."""
        # Setup iteration directory
        iteration_path = self.file_manager.setup_iteration(iteration)

        # Create examples for this iteration
        self.example_aggregator.create_examples_for_iteration(
            iteration_path, iteration, self.experiment_path
        )

        # Generate sessions for this iteration
        self.session_generator.generate_sessions_for_iteration(
            iteration_path, self.experiment_path, iteration
        )
