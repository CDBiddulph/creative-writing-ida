import anthropic
from src.session_xml_generator.session_xml_generator import SessionXmlGenerator


class ClaudeBaseSessionXmlGenerator(SessionXmlGenerator):
    """Generate sessions in XML format using Claude Base model."""

    def generate_leaf(self, prompt: str) -> str:
        """Generate a leaf session using Claude base model completions API."""
        # Load content
        readme_content = self._load_readme_content(self.leaf_readme_path)
        examples_xml = self._load_examples_xml(self.leaf_examples_xml_path)

        # Build prompt
        full_prompt = readme_content + "\n\n## Transcripts\n\n"
        if examples_xml:
            full_prompt += examples_xml + "\n\n"
        full_prompt += f"<session>\n<prompt>{prompt}</prompt>\n<submit>"

        # Call API
        client = anthropic.Anthropic()
        response = client.completions.create(
            model=self.model,
            max_tokens_to_sample=self.max_tokens,
            temperature=self.temperature,
            prompt=full_prompt,
            stop_sequences=["</submit>"],
        )

        # Validate response
        if response.stop_reason != "stop_sequence":
            raise RuntimeError(
                f"API call did not complete properly. Stop reason: {response.stop_reason}"
            )

        return response.completion

    def generate_parent(self, prompt: str) -> str:
        """Generate a parent session using Claude base model completions API."""
        # Load content
        readme_content = self._load_readme_content(self.parent_readme_path)
        examples_xml = self._load_examples_xml(self.parent_examples_xml_path)

        # Build prompt
        full_prompt = readme_content + "\n\n## Transcripts\n\n"
        if examples_xml:
            full_prompt += examples_xml + "\n\n"
        full_prompt += f"<session>\n<prompt>{prompt}</prompt>\n<submit>"

        # Call API
        client = anthropic.Anthropic()
        response = client.completions.create(
            model=self.model,
            max_tokens_to_sample=self.max_tokens,
            temperature=self.temperature,
            prompt=full_prompt,
            stop_sequences=["</submit>"],
        )

        # Validate response
        if response.stop_reason != "stop_sequence":
            raise RuntimeError(
                f"API call did not complete properly. Stop reason: {response.stop_reason}"
            )

        return response.completion

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
