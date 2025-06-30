"""File management utilities for data collection."""

from pathlib import Path
from typing import Dict, Any
import json


class FileManager:
    """Manages file operations for data collection experiments."""

    def __init__(self, experiment_path: Path):
        """
        Initialize file manager for an experiment.

        Args:
            experiment_path: Base path to experiment directory
        """
        self.experiment_path = experiment_path

    def setup_experiment(self, config: Dict[str, Any]) -> None:
        """
        Set up experiment directory structure and save configuration.

        Args:
            config: Configuration dictionary to save
        """
        # Create experiment directory
        self.experiment_path.mkdir(parents=True, exist_ok=True)

        # Save configuration
        config_file = self.experiment_path / "config.json"
        config_file.write_text(json.dumps(config, indent=2))

    def setup_iteration(self, iteration: int) -> Path:
        """
        Set up directory structure for a specific iteration.

        Args:
            iteration: Iteration number (0-based)

        Returns:
            Path to the created iteration directory
        """
        iter_path = self.experiment_path / f"iteration_{iteration}"
        iter_path.mkdir(parents=True, exist_ok=True)

        # Create required subdirectories
        (iter_path / "examples").mkdir(exist_ok=True)
        (iter_path / "sample-sessions").mkdir(exist_ok=True)
        (iter_path / "leaf-sessions").mkdir(exist_ok=True)
        # Note: parent-sessions will be created when needed (not in MVP)

        return iter_path
