"""Tests for PlaceholderReplacer class."""

import unittest
from src.placeholder_replacer import PlaceholderReplacer
from src.session import Session, PromptEvent, ResponseEvent, AskEvent


class TestPlaceholderReplacer(unittest.TestCase):
    """Test the PlaceholderReplacer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.replacer = PlaceholderReplacer()

    def test_extract_placeholders(self):
        """Test extraction of placeholders from text."""
        text = "This uses $PROMPT and $RESPONSE1 and $RESPONSE2 again $RESPONSE1"
        placeholders = self.replacer.extract_placeholders(text)
        self.assertEqual(set(placeholders), {"$PROMPT", "$RESPONSE1", "$RESPONSE2"})

    def test_extract_placeholders_empty(self):
        """Test extraction from text without placeholders."""
        text = "This has no placeholders"
        placeholders = self.replacer.extract_placeholders(text)
        self.assertEqual(placeholders, [])

    def test_build_replacement_map_with_prompt(self):
        """Test building replacement map with prompt event."""
        session = Session(session_id=0)
        session.add_event(PromptEvent(text="Original prompt"))

        replacement_map = self.replacer.build_replacement_map(session)
        self.assertEqual(replacement_map, {"$PROMPT": "Original prompt"})

    def test_build_replacement_map_with_responses(self):
        """Test building replacement map with multiple responses."""
        session = Session(session_id=0)
        session.add_event(PromptEvent(text="Test prompt"))
        session.add_event(AskEvent(text="First ask"))
        session.add_event(ResponseEvent(text="First response"))
        session.add_event(AskEvent(text="Second ask"))
        session.add_event(ResponseEvent(text="Second response"))

        replacement_map = self.replacer.build_replacement_map(session)
        expected = {
            "$PROMPT": "Test prompt",
            "$RESPONSE1": "First response",
            "$RESPONSE2": "Second response",
        }
        self.assertEqual(replacement_map, expected)

    def test_replace_placeholders(self):
        """Test replacement of placeholders in text."""
        text = "Based on $PROMPT, combine $RESPONSE1 with $RESPONSE2."
        replacement_map = {
            "$PROMPT": "Write a story",
            "$RESPONSE1": "idea one",
            "$RESPONSE2": "idea two",
        }

        result = self.replacer.replace_placeholders(text, replacement_map)
        expected = "Based on Write a story, combine idea one with idea two."
        self.assertEqual(result, expected)

    def test_replace_placeholders_with_longer_numbers(self):
        """Test replacement handles multi-digit response numbers correctly."""
        text = "$RESPONSE10 before $RESPONSE1"
        replacement_map = {"$RESPONSE1": "first", "$RESPONSE10": "tenth"}

        result = self.replacer.replace_placeholders(text, replacement_map)
        expected = "tenth before first"
        self.assertEqual(result, expected)

    def test_process_text_complete_flow(self):
        """Test complete text processing flow."""
        session = Session(session_id=0)
        session.add_event(PromptEvent(text="Write about cats"))
        session.add_event(AskEvent(text="Give me ideas"))
        session.add_event(ResponseEvent(text="Fluffy cats"))
        session.add_event(AskEvent(text="More ideas"))
        session.add_event(ResponseEvent(text="Playful kittens"))

        text = "Combine $PROMPT with $RESPONSE1 and $RESPONSE2"
        result = self.replacer.process_text(text, session)
        expected = "Combine Write about cats with Fluffy cats and Playful kittens"
        self.assertEqual(result, expected)

    def test_process_text_no_placeholders(self):
        """Test processing text without placeholders."""
        session = Session(session_id=0)
        session.add_event(PromptEvent(text="Test"))

        text = "No placeholders here"
        result = self.replacer.process_text(text, session)
        self.assertEqual(result, text)

    def test_process_text_missing_placeholder(self):
        """Test processing text with placeholder not in session."""
        session = Session(session_id=0)
        session.add_event(PromptEvent(text="Test"))

        text = "Using $PROMPT and $RESPONSE1"
        result = self.replacer.process_text(text, session)
        # $RESPONSE1 not in session, so it remains unchanged
        expected = "Using Test and $RESPONSE1"
        self.assertEqual(result, expected)

    def test_process_text_empty_input(self):
        """Test processing empty text."""
        session = Session(session_id=0)

        result = self.replacer.process_text("", session)
        self.assertEqual(result, "")


if __name__ == "__main__":
    unittest.main()
