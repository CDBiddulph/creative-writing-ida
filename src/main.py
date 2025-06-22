"""Main entry point for the tree generation system."""

import sys
import logging
from .tree_config import parse_args
from .tree_runner import TreeRunner


def main():
    """
    Main entry point for the tree generation system.
    
    Parses command line arguments, creates TreeRunner, and executes the generation
    process. Handles top-level error reporting and logging setup.
    """
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Parse command line arguments
        config = parse_args()
        
        # Get initial prompt from command line arguments
        # All remaining arguments after parsing are treated as the prompt
        if len(sys.argv) < 2:
            print("Error: No prompt provided")
            sys.exit(1)
        
        # Find where the prompt starts (after all option arguments)
        prompt_start_index = 1
        for i, arg in enumerate(sys.argv[1:], 1):
            if not arg.startswith('-'):
                prompt_start_index = i
                break
        
        # Join all remaining arguments as the prompt
        initial_prompt = ' '.join(sys.argv[prompt_start_index:])
        
        # Create and run the tree generation
        runner = TreeRunner(config)
        
        # Run the generation process
        output_filename = runner.run(initial_prompt)
        
        print(f"Session saved to: {output_filename}")
        
    except KeyboardInterrupt:
        print("\nGeneration interrupted by user")
        sys.exit(1)
    except SystemExit:
        # Re-raise SystemExit (from argparse or explicit sys.exit calls)
        raise
    except Exception as e:
        print(f"Error during tree generation: {e}")
        raise


if __name__ == "__main__":
    main()