"""Configuration management for data collection experiments."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class DataCollectionConfig:
    """Configuration for data collection experiments."""
    
    # Experiment identification
    experiment_id: str
    
    # Example generation parameters
    leaf_examples_per_iteration: int
    parent_examples_per_iteration: int
    max_parent_examples: int
    max_iterations: int
    
    # Tree generation depth parameters
    sample_max_depth: int
    parent_max_depth: int
    leaf_max_depth: int
    
    # File paths
    writing_prompts_path: str
    seed_leaf_examples: str
    seed_parent_examples: str
    
    # Character limits
    parent_total_char_limit: int
    parent_submit_char_limit: int
    
    # Web UI
    web_ui_port: int
    
    # Tree runner parameters
    model: str
    temperature: float
    max_tokens: int
    leaf_readme_path: str
    parent_readme_path: str


def parse_data_collection_args() -> DataCollectionConfig:
    """
    Parse command line arguments for data collection.
    
    Returns:
        DataCollectionConfig with all parameters validated and set to defaults where applicable.
        
    Raises:
        SystemExit: If required arguments are missing or validation fails.
    """
    raise NotImplementedError()