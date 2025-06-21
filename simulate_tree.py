#!/usr/bin/env python3
"""Simple script to test API interfaces with command line arguments."""

import argparse
import logging
import os
from api_interface import get_api_interface

def main():
    parser = argparse.ArgumentParser(description="Test API interface with a prompt")
    parser.add_argument("--prompt", required=True, help="The prompt to send to the API")
    parser.add_argument("--max-tokens", type=int, default=2048, help="Maximum tokens to generate (default: 2048)")
    parser.add_argument("--temperature", type=float, default=0.7, help="Temperature for generation (default: 0.7)")
    parser.add_argument("--mode", choices=["human", "dry-run"], 
                       help="API mode to use (claude mode auto-determined by model name)")
    parser.add_argument("--model", default="claude-3-5-haiku-20241022", 
                       help="Model to use (default: claude-3-5-haiku-20241022)")
    parser.add_argument("--raw-prompt", action="store_true",
                       help="Use the prompt directly instead of the fiction_leaf_prompt.md template")
    parser.add_argument("--readme-file", default="prompts/fiction_leaf_readme.md",
                       help="Path to README file for base model mode (default: prompts/fiction_leaf_readme.md)")
    parser.add_argument("--examples-file", 
                       help="Path to XML file containing example transcripts to include")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set up logging
    if args.verbose:
        logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    else:
        logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
    
    # Determine Claude API mode based on model name
    if args.mode:
        # Use explicitly set mode (human or dry-run)
        claude_mode = args.mode
    elif args.model.startswith("as-hackathon"):
        # Use completions for as-hackathon models
        claude_mode = "claude-completions"
    else:
        # Use base model CLI simulation for other models
        claude_mode = "claude-base"
    
    # Load README content for both Claude modes
    readme_content = ""
    if claude_mode in ["claude-base", "claude-completions"]:
        try:
            with open(args.readme_file, 'r', encoding='utf-8') as f:
                readme_content = f.read()
        except FileNotFoundError:
            print(f"Warning: README file {args.readme_file} not found. Using default content.")
            readme_content = "# Fiction Leaf Experiments\n\nTranscripts of delegated microfiction experiments."
    
    # Load examples XML if provided
    examples_xml = ""
    if args.examples_file:
        try:
            with open(args.examples_file, 'r', encoding='utf-8') as f:
                examples_xml = f.read().strip()
        except FileNotFoundError:
            print(f"Warning: Examples file {args.examples_file} not found. Continuing without examples.")
    
    # Get API interface
    api = get_api_interface(claude_mode, readme_content=readme_content)
    
    # Prepare the prompt
    if args.raw_prompt or claude_mode in ["claude-base", "claude-completions"]:
        # For raw prompt, base model mode, or completions mode, use the prompt directly
        final_prompt = args.prompt
    else:
        # Load and format the fiction_leaf_prompt.md template
        template_path = "fiction_leaf_prompt.md"
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
            
            # Format the template with the prompt and empty example_sessions
            final_prompt = template.format(
                prompt=args.prompt,
                example_sessions=""
            )
        except FileNotFoundError:
            print(f"Warning: Template file {template_path} not found. Using raw prompt.")
            final_prompt = args.prompt
        except Exception as e:
            print(f"Warning: Error loading template: {e}. Using raw prompt.")
            final_prompt = args.prompt
    
    try:
        # Call the API with raw prompt and examples
        result = api.call(
            prompt=final_prompt,
            model=args.model,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            examples_xml=examples_xml
        )
        
        # Print the result
        print(result)
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())