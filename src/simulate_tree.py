#!/usr/bin/env python3
"""Hierarchical tree simulation for fiction writing experiments."""

import argparse
import logging
import os
from config import (
    DEFAULT_MODEL, DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE, DEFAULT_TREE_DEPTH,
    DEFAULT_PARENT_README, DEFAULT_LEAF_README, DEFAULT_OUTPUT_DIR
)
from tree_builder import TreeBuilder
from session_runner import SessionRunner
from file_manager import FileManager

def main():
    parser = argparse.ArgumentParser(description="Hierarchical tree simulation for fiction writing experiments")
    
    # Core arguments
    parser.add_argument("--prompt", required=True, help="The initial prompt for the root session")
    parser.add_argument("--model", default=DEFAULT_MODEL, 
                       help=f"Model to use. Can be short name (opus, sonnet, haiku, big-base, little-base) or full model name (default: {DEFAULT_MODEL})")
    parser.add_argument("--max-tokens", type=int, default=DEFAULT_MAX_TOKENS, 
                       help=f"Maximum tokens to generate (default: {DEFAULT_MAX_TOKENS})")
    parser.add_argument("--temperature", type=float, default=DEFAULT_TEMPERATURE, 
                       help=f"Temperature for generation (default: {DEFAULT_TEMPERATURE})")
    
    # Tree structure arguments
    parser.add_argument("--tree-depth", type=int, default=DEFAULT_TREE_DEPTH,
                       help=f"Number of levels in the tree (default: {DEFAULT_TREE_DEPTH})")
    
    # File path arguments
    parser.add_argument("--parent-readme-file", default=DEFAULT_PARENT_README,
                       help=f"Path to README file for parent nodes (default: {DEFAULT_PARENT_README})")
    parser.add_argument("--leaf-readme-file", default=DEFAULT_LEAF_README,
                       help=f"Path to README file for leaf nodes (default: {DEFAULT_LEAF_README})")
    parser.add_argument("--parent-examples-file", 
                       help="Path to XML file containing example transcripts for parent nodes")
    parser.add_argument("--leaf-examples-file", 
                       help="Path to XML file containing example transcripts for leaf nodes")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR,
                       help=f"Directory to save session XML files (default: {DEFAULT_OUTPUT_DIR})")
    
    # Mode overrides
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set up logging
    if args.verbose:
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    else:
        logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')

    try:
        # Load README content for parent and leaf nodes
        parent_readme_content = FileManager.load_readme_content(args.parent_readme_file)
        leaf_readme_content = FileManager.load_readme_content(args.leaf_readme_file)
        
        # Load examples XML if provided
        parent_examples_xml = FileManager.load_examples_xml(args.parent_examples_file)
        leaf_examples_xml = FileManager.load_examples_xml(args.leaf_examples_file)
        
        # Build the tree structure
        builder = TreeBuilder()
        root_node = builder.build_tree(args.prompt, args.tree_depth)
        
        print(f"Built tree with {args.tree_depth} levels")
        print(f"Root session ID: {root_node.session.id}")
        
        # Create session runner
        runner = SessionRunner(
            model=args.model,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            parent_readme_content=parent_readme_content,
            leaf_readme_content=leaf_readme_content,
            parent_examples_xml=parent_examples_xml,
            leaf_examples_xml=leaf_examples_xml
        )
        
        print(f"Using model: {runner.model} in {runner.api_mode} mode")
        
        # Execute the tree
        print("Executing tree...")
        runner.execute_tree(root_node)
        
        # Get all sessions in pre-order
        all_sessions = builder.get_all_sessions_preorder(root_node)
        
        # Save to XML file
        filename = FileManager.save_session_xml(all_sessions, args.output_dir)
        
        print(f"Completed tree execution with {len(all_sessions)} sessions")
        print(f"Results saved to: {os.path.join(args.output_dir, filename)}")
        
        # Print final result for quick viewing
        if all_sessions:
            final_session = all_sessions[-1]  # Last session in pre-order should be a leaf
            if final_session.final_submit:
                print("\nFinal result:")
                print("-" * 40)
                print(final_session.final_submit)
                print("-" * 40)
        
    except Exception as e:
        logging.error(f"Error during execution: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())