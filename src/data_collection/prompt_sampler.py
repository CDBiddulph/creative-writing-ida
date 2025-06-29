"""Prompt sampling with cross-iteration tracking."""

from pathlib import Path
from typing import List, Set, Tuple


class PromptSampler:
    """Manages prompt sampling without replacement across iterations."""
    
    def __init__(self, prompts_file_path: str):
        """
        Initialize prompt sampler with prompts file.
        
        Args:
            prompts_file_path: Path to file containing writing prompts (one per line)
        """
        raise NotImplementedError()
    
    def sample_prompts_for_iteration(self, 
                                   experiment_path: Path, 
                                   iteration: int,
                                   num_prompts: int) -> List[Tuple[int, str]]:
        """
        Sample prompts for an iteration without replacement across all iterations.
        
        Args:
            experiment_path: Path to experiment directory
            iteration: Current iteration number (0-based)
            num_prompts: Number of prompts to sample
            
        Returns:
            List of tuples (prompt_index, prompt_text) for sampled prompts
            
        Raises:
            ValueError: If not enough unused prompts available
        """
        raise NotImplementedError()