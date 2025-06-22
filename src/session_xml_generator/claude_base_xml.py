import logging
from ..llms.claude_base import call_claude_base
from .session_xml_generator import SessionXmlGenerator


class ClaudeBaseSessionXmlGenerator(SessionXmlGenerator):
    """Generate sessions in XML format using Claude Base model."""

    def generate_leaf(self, prompt: str) -> str:
        """Generate a leaf session using Claude base model completions API."""
        # Load content
        readme_content = self._load_readme_content(self.leaf_readme_path)
        examples_xml = self._load_examples_xml(self.leaf_examples_xml_path)

        return self._generate_session(prompt, readme_content, examples_xml)

    def generate_parent(self, prompt: str) -> str:
        """Generate a parent session using Claude base model completions API."""
        # Load content
        readme_content = self._load_readme_content(self.parent_readme_path)
        examples_xml = self._load_examples_xml(self.parent_examples_xml_path)

        return self._generate_session(prompt, readme_content, examples_xml)

    def _generate_session(
        self, prompt: str, readme_content: str, examples_xml: str
    ) -> str:
        # Build prompt
        full_prompt = readme_content + "\n\n## Transcripts\n\n"
        if examples_xml:
            full_prompt += examples_xml + "\n\n"
        session_xml_start = f"<session>\n<prompt>{prompt}</prompt>\n<"
        full_prompt += session_xml_start

        # Call API
        response = call_claude_base(
            prompt=full_prompt,
            model=self.model,
            max_tokens=self.max_tokens,
            stop_sequences=self.STOP_SEQUENCES,
            temperature=self.temperature,
        )
        # The response doesn't include the stop sequence, so we need to add it
        # Use the actual stop sequence returned by the API
        return f"{session_xml_start}{response.text}{response.stop_sequence}\n</session>"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    generator = ClaudeBaseSessionXmlGenerator(
        model="as-hackathon-little-base-rollout",
        max_tokens=500,
        temperature=0.7,
        leaf_readme_path="prompts/fiction_leaf_readme.md",
        parent_readme_path="prompts/fiction_parent_readme.md",
        leaf_examples_xml_path="examples/fiction_leaf_examples.xml",
        parent_examples_xml_path="examples/fiction_parent_examples.xml",
    )
    print("Leaf:")
    print(generator.generate_leaf("Write a story about a cat"))
    print("Parent:")
    print(generator.generate_parent("Write a story about a cat"))
