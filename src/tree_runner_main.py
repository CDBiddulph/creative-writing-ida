"""Main entry point for the tree generation system."""

import logging
from .tree_runner_config import parse_args
from .tree_runner import TreeRunner


def main():
    """
    Main entry point for the tree generation system.

    Parses command line arguments, creates TreeRunner, and executes the generation
    process. Handles top-level error reporting and logging setup.
    """
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Parse command line arguments
    config, prompt = parse_args()

    # Create and run the tree generation
    runner = TreeRunner(config)

    # Run the generation process using the prompt
    output_filename = runner.run(prompt)

    print(f"Session saved to: {output_filename}")


if __name__ == "__main__":
    main()
