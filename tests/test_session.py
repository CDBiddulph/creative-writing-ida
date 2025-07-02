"""Tests for Session and SessionEvent classes."""

import unittest
import xml.etree.ElementTree as ET
from src.session import (
    Session,
    PromptEvent,
    AskEvent,
    ResponseEvent,
    SubmitEvent,
    FAILED_STR,
)


class TestSession(unittest.TestCase):
    """Test the Session class."""

    def test_session_creation(self):
        """Test basic session creation."""
        session = Session(session_id=1)

        self.assertEqual(session.session_id, 1)
        self.assertEqual(session.events, [])
        self.assertFalse(session.is_failed)

    def test_add_event(self):
        """Test adding events to a session."""
        session = Session(session_id=0)

        prompt_event = PromptEvent(text="Hello")
        session.add_event(prompt_event)

        self.assertEqual(len(session.events), 1)
        self.assertEqual(session.events[0], prompt_event)

    def test_add_multiple_events(self):
        """Test adding multiple events in order."""
        session = Session(session_id=0)

        events = [
            PromptEvent(text="Write a story"),
            AskEvent(text="What genre?"),
            ResponseEvent(text="Fantasy"),
            SubmitEvent(text="Once upon a time..."),
        ]

        for event in events:
            session.add_event(event)

        self.assertEqual(session.events, events)

    def test_cannot_add_event_to_failed_session(self):
        """Test that events cannot be added to failed sessions."""
        session = Session(session_id=0, is_failed=True)

        with self.assertRaises(ValueError) as cm:
            session.add_event(PromptEvent(text="Test"))

        self.assertIn("Cannot add an event to a failed session", str(cm.exception))

    def test_cannot_add_event_after_submit(self):
        """Test that events cannot be added after a submit event."""
        session = Session(session_id=0)
        session.add_event(PromptEvent(text="Test"))
        session.add_event(SubmitEvent(text="Done"))

        with self.assertRaises(ValueError) as cm:
            session.add_event(AskEvent(text="Another question?"))

        self.assertIn("Cannot add an event after a submit event", str(cm.exception))

    def test_to_xml_normal_session(self):
        """Test XML generation for normal session."""
        session = Session(session_id=0)
        session.add_event(PromptEvent(text="Write a story"))
        session.add_event(AskEvent(text="What genre?"))
        session.add_event(ResponseEvent(text="Fantasy"))
        session.add_event(SubmitEvent(text="Once upon a time..."))

        xml = session.to_xml()
        expected = (
            "<session>\n"
            "<prompt>Write a story</prompt>\n"
            "<ask>What genre?</ask>\n"
            "<response>Fantasy</response>\n"
            "<submit>Once upon a time...</submit>\n"
            "</session>"
        )

        self.assertEqual(xml, expected)

    def test_to_xml_failed_session(self):
        """Test XML generation for failed session."""
        session = Session(session_id=0, is_failed=True)

        xml = session.to_xml()
        self.assertEqual(xml, FAILED_STR)

    def test_to_xml_empty_session(self):
        """Test XML generation for empty session."""
        session = Session(session_id=0)

        xml = session.to_xml()
        expected = "<session>\n</session>"

        self.assertEqual(xml, expected)

    def test_from_xml_complete_session(self):
        """Test creating session from complete XML."""
        xml_string = (
            "<session>"
            "<prompt>Write a story</prompt>"
            "<ask>What genre?</ask>"
            "<response>Fantasy</response>"
            "<submit>Once upon a time...</submit>"
            "</session>"
        )

        session = Session.from_xml(xml_string, session_id=5)

        self.assertEqual(session.session_id, 5)
        self.assertFalse(session.is_failed)
        self.assertEqual(len(session.events), 4)

        self.assertIsInstance(session.events[0], PromptEvent)
        self.assertEqual(session.events[0].text, "Write a story")

        self.assertIsInstance(session.events[1], AskEvent)
        self.assertEqual(session.events[1].text, "What genre?")

        self.assertIsInstance(session.events[2], ResponseEvent)
        self.assertEqual(session.events[2].text, "Fantasy")

        self.assertIsInstance(session.events[3], SubmitEvent)
        self.assertEqual(session.events[3].text, "Once upon a time...")

    def test_from_xml_partial_session(self):
        """Test creating session from partial XML."""
        xml_string = (
            "<session>"
            "<prompt>Test prompt</prompt>"
            "<ask>Question?</ask>"
            "</session>"
        )

        session = Session.from_xml(xml_string, session_id=2)

        self.assertEqual(session.session_id, 2)
        self.assertEqual(len(session.events), 2)

        self.assertIsInstance(session.events[0], PromptEvent)
        self.assertEqual(session.events[0].text, "Test prompt")

        self.assertIsInstance(session.events[1], AskEvent)
        self.assertEqual(session.events[1].text, "Question?")

    def test_from_xml_empty_session(self):
        """Test creating session from empty XML."""
        xml_string = "<session></session>"

        session = Session.from_xml(xml_string, session_id=3)

        self.assertEqual(session.session_id, 3)
        self.assertEqual(len(session.events), 0)

    def test_round_trip_conversion(self):
        """Test XML -> Session -> XML conversion preserves content."""
        original_xml = (
            "<session>"
            "<prompt>Hello</prompt>"
            "<ask>Question?</ask>"
            "<response>Answer</response>"
            "<submit>Done</submit>"
            "</session>"
        )

        session = Session.from_xml(original_xml, session_id=0)
        regenerated_xml = session.to_xml()

        # Parse both XMLs to compare content
        original_root = ET.fromstring(original_xml)
        regenerated_root = ET.fromstring(regenerated_xml)

        # Compare structure and content
        self.assertEqual(len(original_root), len(regenerated_root))

        for orig_elem, regen_elem in zip(original_root, regenerated_root):
            self.assertEqual(orig_elem.tag, regen_elem.tag)
            self.assertEqual(orig_elem.text, regen_elem.text)

    def test_is_complete_with_submit(self):
        """Test is_complete returns True when session has submit event."""
        session = Session(session_id=0)
        session.add_event(PromptEvent(text="Test"))
        session.add_event(SubmitEvent(text="Done"))

        self.assertTrue(session.is_complete())

    def test_is_complete_without_submit(self):
        """Test is_complete returns False when session has no submit event."""
        session = Session(session_id=0)
        session.add_event(PromptEvent(text="Test"))
        session.add_event(AskEvent(text="Question?"))

        self.assertFalse(session.is_complete())

    def test_is_complete_failed_session(self):
        """Test is_complete returns True for failed sessions."""
        session = Session(session_id=0, is_failed=True)

        self.assertTrue(session.is_complete())

    def test_get_ask_text_success(self):
        """Test get_ask_text returns correct text when last event is ask."""
        session = Session(session_id=0)
        session.add_event(PromptEvent(text="Test"))
        session.add_event(AskEvent(text="What should I do?"))

        self.assertEqual(session.get_ask_text(), "What should I do?")

    def test_get_ask_text_wrong_last_event(self):
        """Test get_ask_text raises error when last event is not ask."""
        session = Session(session_id=0)
        session.add_event(PromptEvent(text="Test"))
        session.add_event(SubmitEvent(text="Done"))

        with self.assertRaises(ValueError) as cm:
            session.get_ask_text()

        self.assertIn("Last event is not a AskEvent event", str(cm.exception))

    def test_get_ask_text_empty_session(self):
        """Test get_ask_text raises error for empty session."""
        session = Session(session_id=0)

        with self.assertRaises(ValueError) as cm:
            session.get_ask_text()

        self.assertEqual(str(cm.exception), "No events in session")

    def test_get_ask_text_failed_session(self):
        """Test get_ask_text returns FAILED for failed session."""
        session = Session(session_id=0, is_failed=True)

        self.assertEqual(session.get_ask_text(), FAILED_STR)

    def test_get_submit_text_success(self):
        """Test get_submit_text returns correct text when last event is submit."""
        session = Session(session_id=0)
        session.add_event(PromptEvent(text="Test"))
        session.add_event(SubmitEvent(text="Final result"))

        self.assertEqual(session.get_submit_text(), "Final result")

    def test_get_submit_text_wrong_last_event(self):
        """Test get_submit_text raises error when last event is not submit."""
        session = Session(session_id=0)
        session.add_event(PromptEvent(text="Test"))
        session.add_event(AskEvent(text="Question?"))

        with self.assertRaises(ValueError) as cm:
            session.get_submit_text()

        self.assertIn("Last event is not a SubmitEvent event", str(cm.exception))

    def test_get_submit_text_empty_session(self):
        """Test get_submit_text raises error for empty session."""
        session = Session(session_id=0)

        with self.assertRaises(ValueError) as cm:
            session.get_submit_text()

        self.assertEqual(str(cm.exception), "No events in session")

    def test_get_submit_text_failed_session(self):
        """Test get_submit_text returns FAILED for failed session."""
        session = Session(session_id=0, is_failed=True)

        self.assertEqual(session.get_submit_text(), FAILED_STR)

    def test_get_prompt_text_success(self):
        """Test get_prompt_text returns correct text when first event is prompt."""
        session = Session(session_id=0)
        session.add_event(PromptEvent(text="Test"))
        session.add_event(AskEvent(text="Question?"))
        session.add_event(ResponseEvent(text="Answer"))
        session.add_event(SubmitEvent(text="Done"))

        self.assertEqual(session.get_prompt_text(), "Test")

    def test_get_prompt_text_wrong_first_event(self):
        """Test get_prompt_text raises error when first event is not prompt."""
        session = Session(session_id=0)
        session.add_event(AskEvent(text="Question?"))
        session.add_event(PromptEvent(text="Test"))

        with self.assertRaises(ValueError) as cm:
            session.get_prompt_text()

        self.assertIn("First event is not a prompt event", str(cm.exception))

    def test_to_xml_with_include_closing_tag(self):
        """Test to_xml with include_closing_tag parameter."""
        session = Session(session_id=0)
        session.add_event(PromptEvent(text="Test"))
        session.add_event(AskEvent(text="Question?"))

        # Test with closing tag (default)
        full_xml = session.to_xml()
        expected_full = (
            "<session>\n<prompt>Test</prompt>\n<ask>Question?</ask>\n</session>"
        )
        self.assertEqual(full_xml, expected_full)

        # Test without closing tag
        partial_xml = session.to_xml(include_closing_tag=False)
        expected_partial = "<session>\n<prompt>Test</prompt>\n<ask>Question?</ask>"
        self.assertEqual(partial_xml, expected_partial)

    def test_copy_session(self):
        """Test copying a session."""
        session = Session(session_id=0)
        session.add_event(PromptEvent(text="Test"))
        session.add_event(AskEvent(text="Question?"))
        session.add_event(ResponseEvent(text="Answer"))
        session.add_event(SubmitEvent(text="Done"))

        copied_session = session.copy()

        self.assertEqual(copied_session.session_id, session.session_id)
        self.assertEqual(copied_session.events, session.events)


if __name__ == "__main__":
    unittest.main()
