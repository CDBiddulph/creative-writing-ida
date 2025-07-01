"""Claude Base implementation of SessionGenerator with validation logic."""

import logging
from ..llms.claude_base import call_claude_base
from ..session import Session
from ..xml_service import XmlService
from .session_generator import SessionGenerator


class ClaudeBaseSessionGenerator(SessionGenerator):
    """Generate sessions using Claude Base model."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.xml_service = XmlService()

    def generate_leaf(
        self, prompt: str, session_id: int, max_retries: int = 3
    ) -> Session:
        """Generate a leaf session using Claude base model completions API."""
        try:
            # Load content
            readme_content = self._load_readme_content(self.leaf_readme_path)
            examples_xml = self._load_examples_xml(self.leaf_examples_xml_path)

            return self._generate_session_with_validation(
                prompt,
                session_id,
                readme_content,
                examples_xml,
                is_leaf=True,
                max_retries=max_retries,
            )
        except Exception as e:
            logging.warning(f"Failed to load files for leaf generation: {e}")
            return Session(session_id=session_id, is_failed=True)

    def generate_parent(
        self, prompt: str, session_id: int, max_retries: int = 3
    ) -> Session:
        """Generate a parent session using Claude base model completions API."""
        try:
            # Load content
            readme_content = self._load_readme_content(self.parent_readme_path)
            examples_xml = self._load_examples_xml(self.parent_examples_xml_path)

            return self._generate_session_with_validation(
                prompt,
                session_id,
                readme_content,
                examples_xml,
                is_leaf=False,
                max_retries=max_retries,
            )
        except Exception as e:
            logging.warning(f"Failed to load files for parent generation: {e}")
            return Session(session_id=session_id, is_failed=True)

    def continue_parent(
        self, current_session: Session, max_retries: int = 3
    ) -> Session:
        """Continue generating a parent session from existing Session."""
        try:
            # Load content
            readme_content = self._load_readme_content(self.parent_readme_path)
            examples_xml = self._load_examples_xml(self.parent_examples_xml_path)
        except Exception as e:
            logging.warning(f"Failed to load files for continue_parent: {e}")
            return Session(session_id=current_session.session_id, is_failed=True)

        # Convert session to XML for the LLM
        current_xml = current_session.to_xml(include_closing_tag=False)

        # Build prompt with current XML state
        full_prompt = readme_content + "\n\n## Transcripts\n\n"
        if examples_xml:
            full_prompt += examples_xml + "\n\n"
        full_prompt += current_xml

        # Generate continuation with validation
        for attempt in range(max_retries + 1):
            try:
                # Call API to continue
                response = call_claude_base(
                    prompt=full_prompt,
                    model=self.model,
                    max_tokens=self.max_tokens,
                    stop_sequences=self.STOP_SEQUENCES,
                    temperature=self.temperature,
                )

                # Combine current XML with continuation
                continuation_text = "\n<" + response.text + response.stop_sequence

                # If the response ends with </submit>, add </session> to close it
                if response.stop_sequence == "</submit>":
                    continuation_text += "\n</session>"

                # Get complete session XML
                complete_xml = current_xml + continuation_text

                # Validate the XML
                self.xml_service.validate_session_xml(complete_xml, is_leaf=False)

                # Convert to Session object
                return Session.from_xml(complete_xml, current_session.session_id)

            except Exception as e:
                logging.warning(
                    f"Attempt {attempt + 1} failed for continue_parent: {e}"
                )
                if attempt == max_retries:  # Last attempt
                    # Return failed session
                    failed_session = Session(
                        session_id=current_session.session_id, is_failed=True
                    )
                    return failed_session

    def _generate_session_with_validation(
        self,
        prompt: str,
        session_id: int,
        readme_content: str,
        examples_xml: str,
        is_leaf: bool,
        max_retries: int,
    ) -> Session:
        """Generate session with validation and retry logic."""
        for attempt in range(max_retries + 1):
            try:
                xml_content = self._generate_session_xml(
                    prompt, readme_content, examples_xml
                )

                # Validate the XML
                self.xml_service.validate_session_xml(xml_content, is_leaf=is_leaf)

                # Convert to Session object
                return Session.from_xml(xml_content, session_id)

            except Exception as e:
                logging.warning(
                    f"Attempt {attempt + 1} failed for {'leaf' if is_leaf else 'parent'}: {e}"
                )
                if attempt == max_retries:  # Last attempt
                    # Return failed session
                    failed_session = Session(session_id=session_id, is_failed=True)
                    return failed_session

    def _generate_session_xml(
        self, prompt: str, readme_content: str, examples_xml: str
    ) -> str:
        """Generate session XML using Claude API."""
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

        # Build complete XML
        result = f"{session_xml_start}{response.text}{response.stop_sequence}"

        # Only add </session> if we ended with </submit>
        if response.stop_sequence == "</submit>":
            result += "\n</session>"

        return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    generator = ClaudeBaseSessionGenerator(
        model="as-hackathon-little-base-rollout",
        max_tokens=500,
        temperature=0.7,
        leaf_readme_path="prompts/fiction_leaf_readme.md",
        parent_readme_path="prompts/fiction_parent_readme.md",
        leaf_examples_xml_path="examples/fiction_leaf_examples.xml",
        parent_examples_xml_path="examples/fiction_parent_examples.xml",
    )
    print("Leaf:")
    leaf_session = generator.generate_leaf("Write a story about a cat", 0)
    print(leaf_session.to_xml())
    print("Parent:")
    parent_session = generator.generate_parent("Write a story about a cat", 1)
    print(parent_session.to_xml())
