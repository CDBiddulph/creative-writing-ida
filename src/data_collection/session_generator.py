"""Session generation using the existing tree runner system."""

from pathlib import Path
from typing import List, Tuple

from .config import DataCollectionConfig
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
        raise NotImplementedError()
    
    def generate_sessions_for_iteration(self,
                                      iteration_path: Path,
                                      prompts: List[Tuple[int, str]],
                                      examples_dir: Path) -> None:
        """
        Generate all sessions needed for an iteration.
        
        Creates sample sessions from writing prompts, then generates leaf sessions
        from selected nodes in those sample sessions.
        
        Args:
            iteration_path: Path to iteration directory
            prompts: List of (prompt_index, prompt_text) tuples to generate from
            examples_dir: Directory containing current iteration's example files
        """
        raise NotImplementedError()