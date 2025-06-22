import logging
from ..llms.claude_chat import call_claude_chat
from .session_xml_generator import SessionXmlGenerator

CLI_SIMULATION_SYSTEM_PROMPT = "The assistant is in CLI simulation mode, and responds to the user's CLI commands only with the output of the command."


class ClaudeChatSessionXmlGenerator(SessionXmlGenerator):
    """Generate sessions in XML format using Claude Chat model."""

    def generate_leaf(self, prompt: str) -> str:
        """Generate a leaf session using Claude chat model messages API."""
        # Load content
        readme_content = self._load_readme_content(self.leaf_readme_path)
        examples_xml = self._load_examples_xml(self.leaf_examples_xml_path)

        # Build transcript content
        transcript_content = ""
        if examples_xml:
            transcript_content += examples_xml + "\n\n"
        transcript_content += f"<session>\n<prompt>{prompt}</prompt>\n<submit>"

        # Create messages
        messages = [
            {"role": "user", "content": "<cmd>cat README.md</cmd>"},
            {"role": "assistant", "content": readme_content},
            {"role": "user", "content": "<cmd>cat transcripts.xml</cmd>"},
            {"role": "assistant", "content": transcript_content},
        ]

        # Call API
        return call_claude_chat(
            system_prompt="",
            messages=messages,
            model=self.model,
            max_tokens=self.max_tokens,
            stop_sequences=["</submit>"],
            temperature=self.temperature,
        )

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
        return call_claude_chat(
            system_prompt=CLI_SIMULATION_SYSTEM_PROMPT,
            messages=messages,
            model=self.model,
            max_tokens=self.max_tokens,
            stop_sequences=["</submit>"],
            temperature=self.temperature,
        )

    def _load_readme_content(self, readme_path: str) -> str:
        """Load README content from file."""
        with open(readme_path, "r") as f:
            return f.read()

    def _load_examples_xml(self, examples_path: str | None) -> str:
        """Load examples XML from file or return empty string."""
        if examples_path is None:
            return ""

        with open(examples_path, "r") as f:
            return f.read()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    generator = ClaudeChatSessionXmlGenerator(
        model="claude-3-5-haiku-20241022",
        max_tokens=1000,
        temperature=0.7,
        leaf_readme_path="prompts/fiction_leaf_readme.md",
        leaf_examples_xml_path="examples/fiction_leaf_examples.xml",
    )
    print(generator.generate_leaf("Write a story about a cat"))
