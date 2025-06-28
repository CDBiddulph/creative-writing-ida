"""Claude Chat implementation of SessionGenerator with validation logic."""

import logging
from ..llms.claude_chat import call_claude_chat
from ..session import Session
from ..xml_validator import XmlValidator
from .session_generator import SessionGenerator

CLI_SIMULATION_SYSTEM_PROMPT = "The assistant is in CLI simulation mode, and responds to the user's CLI commands only with the output of the command."


class ClaudeChatSessionGenerator(SessionGenerator):
    """Generate sessions using Claude Chat model."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.xml_validator = XmlValidator()

    def generate_leaf(
        self, prompt: str, session_id: int, max_retries: int = 3
    ) -> Session:
        """Generate a leaf session using Claude chat model messages API."""
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
        """Generate a parent session using Claude chat model messages API with CLI simulation."""
        try:
            # Load content
            readme_content = self._load_readme_content(self.parent_readme_path)
            examples_xml = self._load_examples_xml(self.parent_examples_xml_path)
        except Exception as e:
            logging.warning(f"Failed to load files for parent generation: {e}")
            return Session(session_id=session_id, is_failed=True)

        return self._generate_session_with_validation(
            prompt,
            session_id,
            readme_content,
            examples_xml,
            is_leaf=False,
            max_retries=max_retries,
        )

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
        initial_xml = current_session.to_xml(include_closing_tag=False)

        # Generate continuation with validation
        for attempt in range(max_retries + 1):
            try:
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

                logging.info(f"RESULT (continue parent): {continuation_xml}")

                # Get complete session XML
                complete_xml = prompt_xml + continuation_xml

                # Validate the XML
                self.xml_validator.get_is_xml_partial_or_fail(
                    complete_xml, is_leaf=False
                )

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
                self.xml_validator.get_is_xml_partial_or_fail(
                    xml_content, is_leaf=is_leaf
                )

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
        """Generate session XML using Claude Chat API."""
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

        logging.info(f"PROMPT: {prompt}")

        # Call API
        response = call_claude_chat(
            system_prompt=CLI_SIMULATION_SYSTEM_PROMPT,
            messages=messages,
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

        logging.info(f"RESULT (generate session): {result}")

        return result


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    generator = ClaudeChatSessionGenerator(
        model="claude-3-5-haiku-20241022",
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
