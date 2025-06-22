"""Main orchestrator for tree-based story generation."""

from .tree_config import TreeRunnerConfig


class TreeRunner:
    """Main orchestrator for tree-based story generation."""
    
    def __init__(self, config: TreeRunnerConfig):
        """
        Initialize TreeRunner with configuration.
        
        Args:
            config: TreeRunnerConfig containing all settings for generation
        """
        pass
    
    def run(self, initial_prompt: str) -> str:
        """
        Run the complete tree generation process from initial prompt to saved file.
        
        Args:
            initial_prompt: The starting prompt for the root session
            
        Returns:
            str: Filename of the saved XML output file
            
        Creates a complete tree by calling SessionProcessor.process_session,
        then saves the result as a timestamped XML file.
        """
        pass