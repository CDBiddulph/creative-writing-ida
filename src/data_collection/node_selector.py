"""Node selection from generated sessions."""

from pathlib import Path
from typing import List, Tuple
import random
import xml.etree.ElementTree as ET


class NodeSelector:
    """Selects nodes from session trees for example generation."""
    
    def __init__(self, random_seed: int = None):
        """
        Initialize node selector with optional random seed.
        
        Args:
            random_seed: Optional seed for reproducible random selection
        """
        raise NotImplementedError()
    
    def select_nodes_for_examples(self, 
                                sessions_dir: Path, 
                                num_examples: int) -> List[Tuple[str, int, str]]:
        """
        Select random nodes from sessions for example generation.
        
        Args:
            sessions_dir: Directory containing session XML files
            num_examples: Number of nodes to select
            
        Returns:
            List of tuples (session_filename, node_id, prompt_text) for selected nodes
            
        Raises:
            ValueError: If not enough nodes available for selection
        """
        raise NotImplementedError()