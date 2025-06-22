import anthropic
from src.session_xml_generator.session_xml_generator import SessionXmlGenerator

CLI_SIMULATION_SYSTEM_PROMPT = "The assistant is in CLI simulation mode, and responds to the user's CLI commands only with the output of the command."


class ClaudeChatSessionXmlGenerator(SessionXmlGenerator):
    """Generate sessions in XML format using Claude Chat model."""

    def generate_leaf(self, prompt: str) -> str:
        """Generate a leaf session using Claude chat model messages API."""
        # Load content
        readme_content = self._load_readme_content(self.leaf_readme_path)
        examples_xml = self._load_examples_xml(self.leaf_examples_xml_path)

        # Build content
        full_content = readme_content + "\n\n## Transcripts\n\n"
        if examples_xml:
            full_content += examples_xml + "\n\n"
        full_content += f"<session>\n<prompt>{prompt}</prompt>\n<submit>"

        # Create messages
        messages = [{"role": "user", "content": full_content}]

        # Call API
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=messages,
            stop_sequences=["</submit>"],
        )

        # Validate response
        if response.stop_reason != "stop_sequence":
            raise RuntimeError(
                f"API call did not complete properly. Stop reason: {response.stop_reason}"
            )

        if len(response.content) != 1:
            raise ValueError(f"Unexpected response format from Claude API: {response}")

        return response.content[0].text

    def generate_parent(self, prompt: str) -> str:
        """Generate a parent session using Claude chat model messages API with CLI simulation."""
        # Load content
        readme_content = self._load_readme_content(self.parent_readme_path)
        examples_xml = self._load_examples_xml(self.parent_examples_xml_path)

        # Build transcript content
        transcript_content = ""
        if examples_xml:
            transcript_content += examples_xml + "\n\n"
        transcript_content += f"<session>\n<prompt>{prompt}</prompt>\n<submit>"

        # Create CLI simulation messages
        messages = [
            {"role": "user", "content": "<cmd>cat README.md</cmd>"},
            {"role": "assistant", "content": readme_content},
            {"role": "user", "content": "<cmd>cat transcripts.xml</cmd>"},
            {"role": "assistant", "content": transcript_content},
        ]

        # Call API
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=CLI_SIMULATION_SYSTEM_PROMPT,
            messages=messages,
            stop_sequences=["</submit>"],
        )

        # Validate response
        if response.stop_reason != "stop_sequence":
            raise RuntimeError(
                f"API call did not complete properly. Stop reason: {response.stop_reason}"
            )

        if len(response.content) != 1:
            raise ValueError(f"Unexpected response format from Claude API: {response}")

        return response.content[0].text

    def _load_readme_content(self, readme_path: str) -> str:
        """Load README content from file."""
        if readme_path is None:
            raise FileNotFoundError("README path is required but was not provided")
        
        with open(readme_path, 'r') as f:
            return f.read()
    
    def _load_examples_xml(self, examples_path: str) -> str:
        """Load examples XML from file or return empty string."""
        if examples_path is None:
            return ""
        
        with open(examples_path, 'r') as f:
            return f.read()
