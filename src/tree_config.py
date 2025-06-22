"""Configuration management for tree generation system."""

import argparse
from dataclasses import dataclass


@dataclass
class TreeRunnerConfig:
    """Configuration for tree runner containing all generation parameters."""
    model: str                          # Model name for SessionXmlGenerator factory
    max_depth: int                      # Maximum tree depth (root = depth 0)
    output_dir: str                     # Directory for saving output files
    temperature: float                  # Generation temperature
    max_tokens: int                     # Maximum tokens per generation
    leaf_readme_path: str              # Path to leaf README file
    parent_readme_path: str            # Path to parent README file  
    leaf_examples_xml_path: str = None # Optional path to leaf examples
    parent_examples_xml_path: str = None # Optional path to parent examples


def parse_args() -> TreeRunnerConfig:
    """
    Parse command line arguments into TreeRunnerConfig object.
    
    Returns:
        TreeRunnerConfig: Parsed configuration from command line args
        
    Handles argument parsing, validation, and default value assignment.
    """
    pass


def create_session_generator(config: TreeRunnerConfig):
    """
    Create appropriate SessionXmlGenerator using factory pattern.
    
    Args:
        config: TreeRunnerConfig containing model name and paths
        
    Returns:
        SessionXmlGenerator: Configured generator instance (base or chat model)
        
    Uses the existing factory to map model names to generator types.
    """
    pass