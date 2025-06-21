"""Interface for different API implementations (Claude or Human)."""

import sys
from abc import ABC, abstractmethod
from typing import List, Dict
import anthropic
import logging
import json
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class APIInterface(ABC):
    """Abstract interface for API implementations."""
    
    @abstractmethod
    def call(self, prompt: str, model: str, max_tokens: int, temperature: float = 0.7, examples_xml: str = "") -> str:
        """
        Call the API with a raw prompt string.
        
        Args:
            prompt: Raw prompt string
            model: Model to use (may be ignored for human interface)
            max_tokens: Maximum tokens to generate (may be ignored for human interface)
            temperature: Temperature for generation (may be ignored for human interface)
            examples_xml: Optional XML examples to include
            
        Returns:
            Generated response text
        """
        pass

def _shorten_for_logging(text: str, max_length: int = 500) -> str:
    """Shorten text to show beginning and end, return as JSON string."""
    if len(text) <= max_length:
        return json.dumps(text)
    
    # Show beginning and end with ellipsis in middle
    half_length = (max_length - 5) // 2  # Reserve 5 chars for " ... "
    beginning = text[:half_length]
    ending = text[-half_length:]
    new_text = beginning + " ... " + ending
    return json.dumps(new_text)

class ClaudeCompletionsAPI(APIInterface):
    """Claude Completions API implementation (raw string prompts)."""
    
    def __init__(self, readme_content: str = ""):
        """Initialize Claude Completions API."""
        self.readme_content = readme_content
    
    def call(self, prompt: str, model: str, max_tokens: int, temperature: float = 0.7, examples_xml: str = "") -> str:
        """Call the Claude Completions API with constructed prompt."""
        # Construct the full prompt with README and XML transcript
        readme_content = self.readme_content or "# Fiction Leaf Experiments\n\nTranscripts of delegated microfiction experiments."
        
        # Build the transcripts section
        transcripts_section = "## Transcripts\n\n"
        
        # Add examples if provided
        if examples_xml:
            transcripts_section += examples_xml + "\n\n"
        
        # Add the current session
        transcripts_section += f"""<session>
<prompt>{prompt}</prompt>
<submit>"""
        
        full_prompt = readme_content + "\n\n" + transcripts_section
        
        logging.info(f"Sending request to Claude Completions API...")
        shortened_prompt = _shorten_for_logging(full_prompt)
        logging.info(f"  Full prompt: {shortened_prompt}")
        logging.info(f"  Model: {model}")
        logging.info(f"  Max tokens: {max_tokens}")
        logging.info(f"  Temperature: {temperature}")

        client = anthropic.Anthropic()
        
        response = client.completions.create(
            model=model,
            max_tokens_to_sample=max_tokens,
            temperature=temperature,
            prompt=full_prompt
        )
        
        response_text = response.completion

        shortened_response_text = _shorten_for_logging(response_text)
        logging.info(f"Claude Completions API response: {shortened_response_text}")
        
        return response_text


class ClaudeBaseModelAPI(APIInterface):
    """Claude API implementation that simulates base model behavior using CLI prompting."""
    
    def __init__(self, readme_content: str = ""):
        """Initialize Claude Base Model API (uses messages API only)."""
        self.readme_content = readme_content
    
    def call(self, prompt: str, model: str, max_tokens: int, temperature: float = 0.7, examples_xml: str = "") -> str:
        """Call the Claude API in base model mode using CLI simulation."""
        logging.info(f"Sending request to Claude Base Model API...")
        shortened_prompt = _shorten_for_logging(prompt)
        logging.info(f"  Prompt: {shortened_prompt}")
        logging.info(f"  Model: {model}")
        logging.info(f"  Max tokens: {max_tokens}")
        logging.info(f"  Temperature: {temperature}")

        client = anthropic.Anthropic()
        
        # Create CLI simulation messages
        # The system prompt tells Claude it's in CLI mode
        system_prompt = "The assistant is in CLI simulation mode, and responds to the user's CLI commands only with the output of the command."
        
        # Use the README content passed in during initialization
        readme_content = self.readme_content or "# Fiction Leaf Experiments\n\nTranscripts of delegated microfiction experiments."
        
        # Create the transcript XML with examples and user's prompt
        transcript_xml = ""
        if examples_xml:
            transcript_xml += examples_xml + "\n\n"
        
        transcript_xml += f"""<session>
<prompt>{prompt}</prompt>
<submit>"""
        
        # Create multi-file CLI simulation
        messages = [
            {"role": "user", "content": "<cmd>cat README.md</cmd>"},
            {"role": "assistant", "content": readme_content},
            {"role": "user", "content": "<cmd>cat transcripts.xml</cmd>"},
            {"role": "assistant", "content": transcript_xml}
        ]
        
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=messages
        )
        
        if len(response.content) != 1:
            raise ValueError(f"Unexpected response format from Claude API: {response}")
        
        response_text = response.content[0].text

        shortened_response_text = _shorten_for_logging(response_text)
        logging.info(f"Claude Base Model API response: {shortened_response_text}")
        
        return response_text


class HumanAPI(APIInterface):
    """Human input implementation for testing."""
    
    def call(self, prompt: str, model: str, max_tokens: int, temperature: float = 0.7, examples_xml: str = "") -> str:
        """Get human input through CLI."""
        print("\n" + "=" * 80)
        print("HUMAN INPUT MODE")
        print("=" * 80)
        print(f"Model: {model}")
        print(f"Max tokens: {max_tokens}")
        print(f"Temperature: {temperature}")
        print("\nPrompt:")
        print("-" * 40)
        print(prompt)
        print("-" * 40)
        
        print("\nYour response (end with two newlines):")
        print(">>> ", end="", flush=True)
        
        # Read input until two consecutive newlines
        lines = []
        consecutive_empty = 0
        
        while True:
            try:
                line = input()
                if line == "":
                    consecutive_empty += 1
                    if consecutive_empty >= 2:
                        break
                    lines.append(line)
                else:
                    consecutive_empty = 0
                    lines.append(line)
                    
                if consecutive_empty == 0:
                    print(">>> ", end="", flush=True)
                    
            except (EOFError, KeyboardInterrupt):
                print("\nInput interrupted. Exiting.")
                sys.exit(1)
        
        # Remove trailing empty lines
        while lines and lines[-1] == "":
            lines.pop()
        
        response = "\n".join(lines)
        print(f"\nResponse captured ({len(response)} characters)")
        print("=" * 80)
        
        return response


class DryRunAPI(APIInterface):
    """Dry run implementation that shows the prompt without calling any API."""
    
    def call(self, prompt: str, model: str, max_tokens: int, temperature: float = 0.7, examples_xml: str = "") -> str:
        """Show the prompt that would be sent."""
        print("=== DRY RUN: Showing the prompt that would be sent to Claude ===")
        print(f"Model: {model}")
        print(f"Max tokens: {max_tokens}")
        print(f"Temperature: {temperature}")
        print("\nPrompt:")
        print("-" * 50)
        print(prompt)
        print("-" * 50)
        return ""


def get_api_interface(mode: str, readme_content: str = "") -> APIInterface:
    """
    Get the appropriate API interface based on mode.
    
    Args:
        mode: 'claude-completions', 'claude-base', 'human', or 'dry-run'
        readme_content: README content string for claude modes
        
    Returns:
        Appropriate API interface instance
    """
    if mode == "claude-completions":
        return ClaudeCompletionsAPI(readme_content=readme_content)
    elif mode == "claude-base":
        return ClaudeBaseModelAPI(readme_content=readme_content)
    elif mode == "human":
        return HumanAPI()
    elif mode == "dry-run":
        return DryRunAPI()
    else:
        raise ValueError(f"Unknown API mode: {mode}")