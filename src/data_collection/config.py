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
    import argparse

    parser = argparse.ArgumentParser(
        description="Data collection for improved example generation"
    )

    # Experiment setup
    parser.add_argument(
        "--experiment-id", required=True, help="Unique identifier for this experiment"
    )
    parser.add_argument(
        "--leaf-examples-per-iteration",
        type=int,
        required=True,
        help="Number of leaf examples to generate per iteration",
    )
    parser.add_argument(
        "--parent-examples-per-iteration",
        type=int,
        required=True,
        help="Number of parent examples to generate per iteration",
    )
    parser.add_argument(
        "--max-parent-examples",
        type=int,
        default=20,
        help="Maximum total parent examples to accumulate (default: 20)",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        required=True,
        help="Maximum number of iterations to run",
    )

    # Depth configuration
    parser.add_argument(
        "--sample-max-depth",
        type=int,
        required=True,
        help="Maximum depth for sample session generation",
    )
    parser.add_argument(
        "--parent-max-depth",
        type=int,
        default=1,
        help="Maximum depth for parent example generation (default: 1)",
    )
    parser.add_argument(
        "--leaf-max-depth",
        type=int,
        required=True,
        help="Maximum depth for leaf example generation",
    )

    # File paths
    parser.add_argument(
        "--writing-prompts-path",
        required=True,
        help="Path to file containing writing prompts (one per line)",
    )
    parser.add_argument(
        "--seed-leaf-examples",
        required=True,
        help="Path to seed leaf examples XML file",
    )
    parser.add_argument(
        "--seed-parent-examples",
        required=True,
        help="Path to seed parent examples XML file",
    )
    parser.add_argument(
        "--leaf-readme-path", required=True, help="Path to leaf generation README file"
    )
    parser.add_argument(
        "--parent-readme-path",
        required=True,
        help="Path to parent generation README file",
    )

    # Character limits
    parser.add_argument(
        "--parent-total-char-limit",
        type=int,
        default=2000,
        help="Total character limit for parent examples (default: 2000)",
    )
    parser.add_argument(
        "--parent-submit-char-limit",
        type=int,
        default=500,
        help="Character limit for parent submit elements (default: 500)",
    )

    # Web UI
    parser.add_argument(
        "--web-ui-port",
        type=int,
        default=5000,
        help="Port for parent example web UI (default: 5000)",
    )

    # Tree runner parameters
    parser.add_argument("--model", required=True, help="Model name for generation")
    parser.add_argument(
        "--temperature",
        type=float,
        required=True,
        help="Generation temperature (0.0-1.0)",
    )
    parser.add_argument(
        "--max-tokens", type=int, required=True, help="Maximum tokens per generation"
    )

    args = parser.parse_args()

    # Validation
    if args.temperature < 0.0 or args.temperature > 1.0:
        parser.error("temperature must be between 0.0 and 1.0")
    if args.max_tokens <= 0:
        parser.error("max-tokens must be positive")
    if args.leaf_examples_per_iteration < 0:
        parser.error("leaf-examples-per-iteration must be non-negative")
    if args.parent_examples_per_iteration < 0:
        parser.error("parent-examples-per-iteration must be non-negative")
    if args.max_iterations <= 0:
        parser.error("max-iterations must be positive")

    return DataCollectionConfig(
        experiment_id=args.experiment_id,
        leaf_examples_per_iteration=args.leaf_examples_per_iteration,
        parent_examples_per_iteration=args.parent_examples_per_iteration,
        max_parent_examples=args.max_parent_examples,
        max_iterations=args.max_iterations,
        sample_max_depth=args.sample_max_depth,
        parent_max_depth=args.parent_max_depth,
        leaf_max_depth=args.leaf_max_depth,
        writing_prompts_path=args.writing_prompts_path,
        seed_leaf_examples=args.seed_leaf_examples,
        seed_parent_examples=args.seed_parent_examples,
        parent_total_char_limit=args.parent_total_char_limit,
        parent_submit_char_limit=args.parent_submit_char_limit,
        web_ui_port=args.web_ui_port,
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        leaf_readme_path=args.leaf_readme_path,
        parent_readme_path=args.parent_readme_path,
    )
