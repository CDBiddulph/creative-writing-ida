"""Experiment management for data collection."""

from pathlib import Path
from typing import List, Optional

from .config import DataCollectionConfig


class Experiment:
    """Manages the lifecycle of a data collection experiment."""
    
    def __init__(self, config: DataCollectionConfig):
        """
        Initialize experiment with configuration.
        
        Args:
            config: Data collection configuration
        """
        raise NotImplementedError()
    
    def run(self) -> None:
        """
        Run the complete data collection experiment.
        
        Creates or resumes experiment, runs all iterations until completion,
        and outputs final results.
        
        Raises:
            ValueError: If experiment configuration is invalid
            RuntimeError: If experiment cannot be completed
        """
        raise NotImplementedError()
    
    def get_final_command(self) -> str:
        """
        Get the final tree_runner_main command to use generated examples.
        
        Returns:
            Complete command string with paths to final example files
        """
        raise NotImplementedError()