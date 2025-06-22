"""Tests for XmlValidator class."""

import unittest
from src.xml_validator import XmlValidator


class TestXmlValidator(unittest.TestCase):
    """Test the XmlValidator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.validator = XmlValidator()

    def test_validate_leaf_session_valid(self):
        """Test validation of valid leaf session XML."""
        xml = """
        <session>
            <prompt>Write a story about robots</prompt>
            <submit>Once upon a time, there was a robot named Bob...</submit>
        </session>
        """

        self.assertTrue(self.validator.validate_session_xml(xml, is_leaf=True))

    def test_validate_leaf_session_minimal(self):
        """Test validation of minimal valid leaf session."""
        xml = """
        <session>
            <prompt>Test</prompt>
            <submit>Result</submit>
        </session>
        """

        self.assertTrue(self.validator.validate_session_xml(xml, is_leaf=True))

    def test_validate_leaf_session_invalid_tags(self):
        """Test validation fails for leaf with invalid tags."""
        xml = """
        <session>
            <prompt>Write a story</prompt>
            <notes>This shouldn't be in a leaf</notes>
            <submit>Story content</submit>
        </session>
        """

        self.assertFalse(self.validator.validate_session_xml(xml, is_leaf=True))

    def test_validate_leaf_session_missing_required_tags(self):
        """Test validation fails for leaf missing required tags."""
        # Missing submit tag
        xml = """
        <session>
            <prompt>Write a story</prompt>
        </session>
        """

        self.assertFalse(self.validator.validate_session_xml(xml, is_leaf=True))

        # Missing prompt tag
        xml = """
        <session>
            <submit>Story without prompt</submit>
        </session>
        """

        self.assertFalse(self.validator.validate_session_xml(xml, is_leaf=True))

    def test_validate_parent_session_valid(self):
        """Test validation of valid parent session XML."""
        xml = """
        <session>
            <prompt>Write a complex story</prompt>
            <notes>This needs some research first</notes>
            <ask>What genre should it be?</ask>
            <response>Science fiction</response>
            <notes>Now I can write the story</notes>
            <submit>Here's a science fiction story...</submit>
        </session>
        """

        self.assertTrue(self.validator.validate_session_xml(xml, is_leaf=False))

    def test_validate_parent_session_with_multiple_asks(self):
        """Test validation of parent session with multiple asks."""
        xml = """
        <session>
            <prompt>Create a character</prompt>
            <ask>What's their background?</ask>
            <response>Military veteran</response>
            <ask>What's their personality?</ask>
            <response>Stoic but caring</response>
            <submit>Character: A stoic military veteran who cares deeply...</submit>
        </session>
        """

        self.assertTrue(self.validator.validate_session_xml(xml, is_leaf=False))

    def test_validate_parent_session_minimal(self):
        """Test validation of minimal parent session (just prompt and submit)."""
        xml = """
        <session>
            <prompt>Simple task</prompt>
            <submit>Direct answer</submit>
        </session>
        """

        self.assertTrue(self.validator.validate_session_xml(xml, is_leaf=False))

    def test_validate_parent_session_invalid_tags(self):
        """Test validation fails for parent with invalid tags."""
        xml = """
        <session>
            <prompt>Test</prompt>
            <invalid_tag>This shouldn't be here</invalid_tag>
            <submit>Result</submit>
        </session>
        """

        self.assertFalse(self.validator.validate_session_xml(xml, is_leaf=False))

    def test_validate_malformed_xml(self):
        """Test validation handles malformed XML gracefully."""
        xml = """
        <session>
            <prompt>Test</prompt>
            <unclosed_tag>Content
            <submit>Result</submit>
        </session>
        """

        # Should handle malformed XML gracefully (return False)
        self.assertFalse(self.validator.validate_session_xml(xml, is_leaf=True))

    def test_validate_empty_xml(self):
        """Test validation of empty or whitespace-only XML."""
        xml = ""
        self.assertFalse(self.validator.validate_session_xml(xml, is_leaf=True))
        self.assertFalse(self.validator.validate_session_xml(xml, is_leaf=False))

    def test_validate_non_session_root(self):
        """Test validation fails for XML without session root."""
        xml = """
        <different_root>
            <prompt>Test</prompt>
            <submit>Result</submit>
        </different_root>
        """

        self.assertFalse(self.validator.validate_session_xml(xml, is_leaf=True))

    def test_validate_nested_tags(self):
        """Test validation handles nested tags correctly."""
        xml = """
        <session>
            <prompt>Test with <em>nested</em> content</prompt>
            <submit>Result with <strong>formatting</strong></submit>
        </session>
        """

        # Should focus on direct children of session, not nested content
        self.assertTrue(self.validator.validate_session_xml(xml, is_leaf=True))

    def test_validate_tags_with_attributes(self):
        """Test validation handles tags with attributes."""
        xml = """
        <session id="123">
            <prompt type="story">Write a story</prompt>
            <submit format="text">Story content here</submit>
        </session>
        """

        self.assertTrue(self.validator.validate_session_xml(xml, is_leaf=True))

    def test_validate_case_sensitivity(self):
        """Test validation is case sensitive for tag names."""
        xml = """
        <session>
            <Prompt>This should fail</Prompt>
            <Submit>Case matters</Submit>
        </session>
        """

        self.assertFalse(self.validator.validate_session_xml(xml, is_leaf=True))

    def test_validate_tags_no_submit_before_prompt(self):
        """Test that tag order affects validation."""
        xml = """
        <session>
            <submit>Result first</submit>
            <prompt>Prompt second</prompt>
        </session>
        """
        self.assertFalse(self.validator.validate_session_xml(xml, is_leaf=True))
        self.assertFalse(self.validator.validate_session_xml(xml, is_leaf=False))

    def test_response_before_ask_fails(self):
        """Test that tag order affects validation."""
        xml = """
        <session>
            <prompt>Prompt</prompt>
            <response>Response first</response>
            <ask>Ask second</ask>
            <submit>Submission</submit>
        </session>
        """
        self.assertFalse(self.validator.validate_session_xml(xml, is_leaf=False))

    def test_response_no_ask_fails(self):
        """Test that tag order affects validation."""
        xml = """
        <session>
            <prompt>Prompt</prompt>
            <response>Response</response>
            <submit>Submission</submit>
        </session>
        """
        self.assertFalse(self.validator.validate_session_xml(xml, is_leaf=False))

    def test_ask_no_response_fails(self):
        """Test that tag order affects validation."""
        xml = """
        <session>
            <prompt>Prompt</prompt>
            <ask>Ask</ask>
            <submit>Submission</submit>
        </session>
        """
        self.assertFalse(self.validator.validate_session_xml(xml, is_leaf=False))

    def test_partial_xml_validation_succeeds(self):
        """Test that partial XML validation works."""
        xml = """
        <session>
            <prompt>Prompt</prompt>
            <ask>Ask</ask>
        """
        self.assertTrue(
            self.validator.validate_session_xml(xml, is_leaf=False, is_partial=True)
        )

    def test_complete_xml_validation_with_partial_fails(self):
        """Test that complete XML validation with partial XML fails."""
        xml = """
        <session>
            <prompt>Prompt</prompt>
            <ask>Ask</ask>
        """
        self.assertFalse(self.validator.validate_session_xml(xml, is_leaf=False))

    def test_partial_xml_validation_is_leaf_always_fails(self):
        """Test that partial XML validation with a leaf node always fails."""
        xml = """
        <session>
            <prompt>Prompt</prompt>
            <ask>Ask</ask>
        """
        self.assertFalse(
            self.validator.validate_session_xml(xml, is_leaf=True, is_partial=True)
        )

    def test_partial_xml_validation_with_submit_fails(self):
        """Test that partial XML validation that doesn't end in </ask> fails."""
        xml = """
        <session>
            <prompt>Prompt</prompt>
            <ask>Ask</ask>
            <response>Response</response>
            <submit>Submit</submit>
        """
        self.assertFalse(
            self.validator.validate_session_xml(xml, is_leaf=False, is_partial=True)
        )

    def test_partial_xml_validation_complete_fails(self):
        """Test that partial XML validation that isn't partial fails."""
        xml = """
        <session>
            <prompt>Prompt</prompt>
            <ask>Ask</ask>
            <response>Response</response>
            <submit>Submit</submit>
        </session>
        """
        self.assertFalse(
            self.validator.validate_session_xml(xml, is_leaf=False, is_partial=True)
        )

    def test_prompt_not_first_fails(self):
        """Test that <prompt> must be the first tag."""
        # Notes before prompt
        xml = """
        <session>
            <notes>Some notes</notes>
            <prompt>The prompt</prompt>
            <submit>The result</submit>
        </session>
        """
        self.assertFalse(self.validator.validate_session_xml(xml, is_leaf=False))

    def test_non_submit_last_tag_fails(self):
        """Test that non-partial XML must end with <submit>."""
        # Notes after submit
        xml = """
        <session>
            <prompt>The prompt</prompt>
            <submit>The result</submit>
            <notes>Some notes</notes>
        </session>
        """
        self.assertFalse(self.validator.validate_session_xml(xml, is_leaf=False))

    def test_ask_without_response_in_complete_fails(self):
        """Test that <ask> without <response> fails in complete XML."""
        xml = """
        <session>
            <prompt>Prompt</prompt>
            <ask>Question?</ask>
            <ask>Another question?</ask>
            <response>Only one response</response>
            <submit>Result</submit>
        </session>
        """
        self.assertFalse(self.validator.validate_session_xml(xml, is_leaf=False))

    def test_response_without_ask_in_complete_fails(self):
        """Test that <response> without preceding <ask> fails."""
        xml = """
        <session>
            <prompt>Prompt</prompt>
            <ask>Question?</ask>
            <response>Answer</response>
            <response>Another response without ask</response>
            <submit>Result</submit>
        </session>
        """
        self.assertFalse(self.validator.validate_session_xml(xml, is_leaf=False))

    def test_notes_between_ask_response_invalid(self):
        """Test that <notes> cannot appear between <ask> and <response>."""
        xml = """
        <session>
            <prompt>Prompt</prompt>
            <ask>Question?</ask>
            <notes>Thinking about this...</notes>
            <response>Answer</response>
            <submit>Result</submit>
        </session>
        """
        self.assertFalse(self.validator.validate_session_xml(xml, is_leaf=False))

    def test_partial_xml_with_notes_before_ask_valid(self):
        """Test that partial XML can have notes before the final ask."""
        xml = """
        <session>
            <prompt>Prompt</prompt>
            <notes>Thinking...</notes>
            <ask>Question?</ask>
        """
        self.assertTrue(
            self.validator.validate_session_xml(xml, is_leaf=False, is_partial=True)
        )

    def test_multiple_ask_response_pairs_valid(self):
        """Test multiple ask-response pairs in correct order."""
        xml = """
        <session>
            <prompt>Complex task</prompt>
            <ask>First question?</ask>
            <response>First answer</response>
            <notes>Progress note</notes>
            <ask>Second question?</ask>
            <response>Second answer</response>
            <ask>Third question?</ask>
            <response>Third answer</response>
            <submit>Final result</submit>
        </session>
        """
        self.assertTrue(self.validator.validate_session_xml(xml, is_leaf=False))

    def test_leaf_with_ask_response_fails(self):
        """Test that leaf nodes cannot have ask/response tags."""
        xml = """
        <session>
            <prompt>Task</prompt>
            <ask>Question?</ask>
            <response>Answer</response>
            <submit>Result</submit>
        </session>
        """
        self.assertFalse(self.validator.validate_session_xml(xml, is_leaf=True))

    def test_partial_xml_prompt_only_valid(self):
        """Test that partial XML with just prompt is valid."""
        xml = """
        <session>
            <prompt>Just a prompt</prompt>
            <ask>Question?</ask>
        """
        self.assertTrue(
            self.validator.validate_session_xml(xml, is_leaf=False, is_partial=True)
        )

    def test_partial_xml_with_multiple_asks_valid(self):
        """Test that partial XML can have multiple ask-response pairs before final ask."""
        xml = """
        <session>
            <prompt>Complex task</prompt>
            <ask>First question?</ask>
            <response>First answer</response>
            <ask>Second question?</ask>
            <response>Second answer</response>
            <ask>Third question?</ask>
        """
        self.assertTrue(
            self.validator.validate_session_xml(xml, is_leaf=False, is_partial=True)
        )

    def test_get_is_xml_partial_or_fail_leaf_valid_partial(self):
        """Test that get_is_xml_partial_or_fail returns True for valid partial XML."""
        xml = """
        <session>
            <prompt>Prompt</prompt>
            <ask>Ask</ask>
        """
        self.assertTrue(self.validator.get_is_xml_partial_or_fail(xml, is_leaf=True))

    def test_get_is_xml_partial_or_fail_parent_valid_complete(self):
        """Test that get_is_xml_partial_or_fail returns False for valid complete XML in a parent."""
        xml = """
        <session>
            <prompt>Prompt</prompt>
            <ask>Ask</ask>
            <response>Response</response>
            <submit>Submit</submit>
        </session>
        """
        self.assertFalse(self.validator.get_is_xml_partial_or_fail(xml, is_leaf=False))

    def test_get_is_xml_partial_or_fail_leaf_invalid(self):
        """Test that get_is_xml_partial_or_fail raises a ValueError for invalid XML in a leaf."""
        xml = """
        <session>
            <prompt>Prompt</prompt>
            <ask>Ask</ask>
            <response>Response</response>
            <submit>Submit</submit>
        </session>
        """
        with self.assertRaises(ValueError):
            self.validator.get_is_xml_partial_or_fail(xml, is_leaf=True)

    def test_get_is_xml_partial_or_fail_parent_complete(self):
        """Test that get_is_xml_partial_or_fail returns False for valid complete XML."""
        xml = """
        <session>
            <prompt>Prompt</prompt>
            <ask>Ask</ask>
            <response>Response</response>
            <submit>Submit</submit>
        </session>
        """
        self.assertFalse(self.validator.get_is_xml_partial_or_fail(xml, is_leaf=False))

    def test_get_is_xml_partial_or_fail_parent_partial(self):
        """Test that get_is_xml_partial_or_fail returns True for valid partial XML."""
        xml = """
        <session>
            <prompt>Prompt</prompt>
            <ask>Ask</ask>
        """
        self.assertTrue(self.validator.get_is_xml_partial_or_fail(xml, is_leaf=False))

    def test_get_is_xml_partial_or_fail_parent_invalid(self):
        """Test that get_is_xml_partial_or_fail returns False for valid complete XML."""
        xml = """
        <session>
            <prompt>Prompt</prompt>
            <ask>Ask
        """
        with self.assertRaises(ValueError):
            self.validator.get_is_xml_partial_or_fail(xml, is_leaf=False)


if __name__ == "__main__":
    unittest.main()
