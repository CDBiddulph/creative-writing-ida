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
        raise NotImplementedError()
    
    def setup_experiment(self, config: Dict[str, Any]) -> None:
        """
        Set up experiment directory structure and save configuration.
        
        Args:
            config: Configuration dictionary to save
        """
        raise NotImplementedError()
    
    def setup_iteration(self, iteration: int) -> Path:
        """
        Set up directory structure for a specific iteration.
        
        Args:
            iteration: Iteration number (0-based)
            
        Returns:
            Path to the created iteration directory
        """
        raise NotImplementedError()