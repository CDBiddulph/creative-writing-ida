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

        return self._generate_session(prompt, readme_content, examples_xml)

    def generate_parent(self, prompt: str) -> str:
        """Generate a parent session using Claude chat model messages API with CLI simulation."""
        # Load content
        readme_content = self._load_readme_content(self.parent_readme_path)
        examples_xml = self._load_examples_xml(self.parent_examples_xml_path)

        return self._generate_session(prompt, readme_content, examples_xml)

    def continue_parent(self, initial_xml: str) -> str:
        """Continue generating a parent session from existing XML."""
        # Load content
        readme_content = self._load_readme_content(self.parent_readme_path)
        examples_xml = self._load_examples_xml(self.parent_examples_xml_path)

        # Build transcript content with the current state
        transcript_content = ""
        if examples_xml:
            transcript_content += examples_xml + "\n\n"

        # Add the opening bracket of the next tag
        prompt_xml = initial_xml + "\n<"
        transcript_content += prompt_xml

        # Create messages showing current state
        messages = [
            {"role": "user", "content": "<cmd>cat README.md</cmd>"},
            {
                "role": "assistant",
                "content": readme_content
                + "\n\nThese transcripts can be found in `transcripts.xml`.",
            },
            {"role": "user", "content": "<cmd>cat transcripts.xml</cmd>"},
            {"role": "assistant", "content": transcript_content},
        ]

        # Call API to continue
        response = call_claude_chat(
            system_prompt=CLI_SIMULATION_SYSTEM_PROMPT,
            messages=messages,
            model=self.model,
            max_tokens=self.max_tokens,
            stop_sequences=self.STOP_SEQUENCES,
            temperature=self.temperature,
        )

        # Combine current XML with continuation
        continuation_xml = response.text + response.stop_sequence

        # If the response ends with </submit>, add </session> to close it
        if response.stop_sequence == "</submit>":
            continuation_xml += "\n</session>"

        # Return the complete session XML
        return prompt_xml + continuation_xml

    def _generate_session(
        self, prompt: str, readme_content: str, examples_xml: str
    ) -> str:
        # Add reference to transcripts.xml to the readme
        readme_content += "\n\nThese transcripts can be found in `transcripts.xml`."

        # Build transcript content
        transcript_content = ""
        if examples_xml:
            transcript_content += examples_xml + "\n\n"
        # Add the start of the session, the prompt, and the opening bracket of the next tag
        session_xml_start = f"<session>\n<prompt>{prompt}</prompt>\n<"
        transcript_content += session_xml_start

        # Create messages
        messages = [
            {"role": "user", "content": "<cmd>cat README.md</cmd>"},
            {"role": "assistant", "content": readme_content},
            {"role": "user", "content": "<cmd>cat transcripts.xml</cmd>"},
            {"role": "assistant", "content": transcript_content},
        ]

        # Call API
        response = call_claude_chat(
            system_prompt=CLI_SIMULATION_SYSTEM_PROMPT,
            messages=messages,
            model=self.model,
            max_tokens=self.max_tokens,
            stop_sequences=self.STOP_SEQUENCES,
            temperature=self.temperature,
        )
        # The response doesn't include the stop sequence, so we need to add it
        # Use the actual stop sequence returned by the API
        result = f"{session_xml_start}{response.text}{response.stop_sequence}"

        # Only add </session> if we ended with </submit>
        if response.stop_sequence == "</submit>":
            result += "\n</session>"

        return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    generator = ClaudeChatSessionXmlGenerator(
        model="claude-3-5-haiku-20241022",
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
