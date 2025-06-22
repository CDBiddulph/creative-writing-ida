"""Configuration management for tree generation system."""

import argparse
from dataclasses import dataclass
from .session_xml_generator.factory import get_session_xml_generator


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
    prompt: str                        # Initial prompt for tree generation
    leaf_examples_xml_path: str = None # Optional path to leaf examples
    parent_examples_xml_path: str = None # Optional path to parent examples


def parse_args() -> TreeRunnerConfig:
    """
    Parse command line arguments into TreeRunnerConfig object.
    
    Returns:
        TreeRunnerConfig: Parsed configuration from command line args
        
    Handles argument parsing, validation, and default value assignment.
    """
    parser = argparse.ArgumentParser(description="Tree-based story generation")
    
    parser.add_argument('--model', required=True, 
                       help='Model name for SessionXmlGenerator')
    parser.add_argument('--max-depth', type=int, required=True,
                       help='Maximum tree depth (root = depth 0)')
    parser.add_argument('--output-dir', default='sessions/',
                       help='Directory for saving output files (default: sessions/)')
    parser.add_argument('--temperature', type=float, required=True,
                       help='Generation temperature (0.0-1.0)')
    parser.add_argument('--max-tokens', type=int, required=True,
                       help='Maximum tokens per generation')
    parser.add_argument('--leaf-readme-path', required=True,
                       help='Path to leaf README file')
    parser.add_argument('--parent-readme-path', required=True,
                       help='Path to parent README file')
    parser.add_argument('--leaf-examples-xml-path',
                       help='Optional path to leaf examples XML file')
    parser.add_argument('--parent-examples-xml-path',
                       help='Optional path to parent examples XML file')
    parser.add_argument('--prompt', required=True,
                       help='Initial prompt for tree generation')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.max_depth < 0:
        parser.error("max-depth must be non-negative")
    if not (0.0 <= args.temperature <= 1.0):
        parser.error("temperature must be between 0.0 and 1.0")
    if args.max_tokens <= 0:
        parser.error("max-tokens must be positive")
    
    return TreeRunnerConfig(
        model=args.model,
        max_depth=args.max_depth,
        output_dir=args.output_dir,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        leaf_readme_path=args.leaf_readme_path,
        parent_readme_path=args.parent_readme_path,
        prompt=args.prompt,
        leaf_examples_xml_path=args.leaf_examples_xml_path,
        parent_examples_xml_path=args.parent_examples_xml_path
    )


def create_session_generator(config: TreeRunnerConfig):
    """
    Create appropriate SessionXmlGenerator using factory pattern.
    
    Args:
        config: TreeRunnerConfig containing model name and paths
        
    Returns:
        SessionXmlGenerator: Configured generator instance (base or chat model)
        
    Uses the existing factory to map model names to generator types.
    """
    return get_session_xml_generator(
        model=config.model,
        max_tokens=config.max_tokens,
        leaf_readme_path=config.leaf_readme_path,
        parent_readme_path=config.parent_readme_path,
        temperature=config.temperature,
        leaf_examples_xml_path=config.leaf_examples_xml_path,
        parent_examples_xml_path=config.parent_examples_xml_path
    )