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
        valid_leaf_xml = """
        <session>
            <prompt>Write a story about robots</prompt>
            <submit>Once upon a time, there was a robot named Bob...</submit>
        </session>
        """
        
        self.assertTrue(self.validator.validate_session_xml(valid_leaf_xml, is_leaf=True))

    def test_validate_leaf_session_minimal(self):
        """Test validation of minimal valid leaf session."""
        minimal_leaf_xml = """
        <session>
            <prompt>Test</prompt>
            <submit>Result</submit>
        </session>
        """
        
        self.assertTrue(self.validator.validate_session_xml(minimal_leaf_xml, is_leaf=True))

    def test_validate_leaf_session_invalid_tags(self):
        """Test validation fails for leaf with invalid tags."""
        invalid_leaf_xml = """
        <session>
            <prompt>Write a story</prompt>
            <notes>This shouldn't be in a leaf</notes>
            <submit>Story content</submit>
        </session>
        """
        
        self.assertFalse(self.validator.validate_session_xml(invalid_leaf_xml, is_leaf=True))

    def test_validate_leaf_session_missing_required_tags(self):
        """Test validation fails for leaf missing required tags."""
        # Missing submit tag
        missing_submit_xml = """
        <session>
            <prompt>Write a story</prompt>
        </session>
        """
        
        self.assertFalse(self.validator.validate_session_xml(missing_submit_xml, is_leaf=True))
        
        # Missing prompt tag
        missing_prompt_xml = """
        <session>
            <submit>Story without prompt</submit>
        </session>
        """
        
        self.assertFalse(self.validator.validate_session_xml(missing_prompt_xml, is_leaf=True))

    def test_validate_parent_session_valid(self):
        """Test validation of valid parent session XML."""
        valid_parent_xml = """
        <session>
            <prompt>Write a complex story</prompt>
            <notes>This needs some research first</notes>
            <ask>What genre should it be?</ask>
            <response>Science fiction</response>
            <notes>Now I can write the story</notes>
            <submit>Here's a science fiction story...</submit>
        </session>
        """
        
        self.assertTrue(self.validator.validate_session_xml(valid_parent_xml, is_leaf=False))

    def test_validate_parent_session_with_multiple_asks(self):
        """Test validation of parent session with multiple asks."""
        multiple_asks_xml = """
        <session>
            <prompt>Create a character</prompt>
            <ask>What's their background?</ask>
            <response>Military veteran</response>
            <ask>What's their personality?</ask>
            <response>Stoic but caring</response>
            <submit>Character: A stoic military veteran who cares deeply...</submit>
        </session>
        """
        
        self.assertTrue(self.validator.validate_session_xml(multiple_asks_xml, is_leaf=False))

    def test_validate_parent_session_minimal(self):
        """Test validation of minimal parent session (just prompt and submit)."""
        minimal_parent_xml = """
        <session>
            <prompt>Simple task</prompt>
            <submit>Direct answer</submit>
        </session>
        """
        
        self.assertTrue(self.validator.validate_session_xml(minimal_parent_xml, is_leaf=False))

    def test_validate_parent_session_invalid_tags(self):
        """Test validation fails for parent with invalid tags."""
        invalid_parent_xml = """
        <session>
            <prompt>Test</prompt>
            <invalid_tag>This shouldn't be here</invalid_tag>
            <submit>Result</submit>
        </session>
        """
        
        self.assertFalse(self.validator.validate_session_xml(invalid_parent_xml, is_leaf=False))

    def test_validate_malformed_xml(self):
        """Test validation handles malformed XML gracefully."""
        malformed_xml = """
        <session>
            <prompt>Test</prompt>
            <unclosed_tag>Content
            <submit>Result</submit>
        </session>
        """
        
        # Should handle malformed XML gracefully (return False)
        self.assertFalse(self.validator.validate_session_xml(malformed_xml, is_leaf=True))

    def test_validate_empty_xml(self):
        """Test validation of empty or whitespace-only XML."""
        self.assertFalse(self.validator.validate_session_xml("", is_leaf=True))
        self.assertFalse(self.validator.validate_session_xml("   ", is_leaf=True))
        self.assertFalse(self.validator.validate_session_xml("\n\t", is_leaf=False))

    def test_validate_non_session_root(self):
        """Test validation fails for XML without session root."""
        non_session_xml = """
        <different_root>
            <prompt>Test</prompt>
            <submit>Result</submit>
        </different_root>
        """
        
        self.assertFalse(self.validator.validate_session_xml(non_session_xml, is_leaf=True))

    def test_validate_nested_tags(self):
        """Test validation handles nested tags correctly."""
        nested_xml = """
        <session>
            <prompt>Test with <em>nested</em> content</prompt>
            <submit>Result with <strong>formatting</strong></submit>
        </session>
        """
        
        # Should focus on direct children of session, not nested content
        self.assertTrue(self.validator.validate_session_xml(nested_xml, is_leaf=True))

    def test_validate_tags_with_attributes(self):
        """Test validation handles tags with attributes."""
        attributed_xml = """
        <session id="123">
            <prompt type="story">Write a story</prompt>
            <submit format="text">Story content here</submit>
        </session>
        """
        
        self.assertTrue(self.validator.validate_session_xml(attributed_xml, is_leaf=True))

    def test_validate_case_sensitivity(self):
        """Test validation is case sensitive for tag names."""
        case_sensitive_xml = """
        <session>
            <Prompt>This should fail</Prompt>
            <Submit>Case matters</Submit>
        </session>
        """
        
        self.assertFalse(self.validator.validate_session_xml(case_sensitive_xml, is_leaf=True))

    def test_allowed_tags_constants(self):
        """Test that the validator has the correct allowed tags defined."""
        # These should be defined as class constants
        self.assertTrue(hasattr(XmlValidator, 'LEAF_ALLOWED_TAGS'))
        self.assertTrue(hasattr(XmlValidator, 'PARENT_ALLOWED_TAGS'))
        
        # Leaf tags should be subset of parent tags
        self.assertTrue(XmlValidator.LEAF_ALLOWED_TAGS.issubset(XmlValidator.PARENT_ALLOWED_TAGS))

    def test_validate_tags_order_independence(self):
        """Test that tag order doesn't affect validation."""
        reordered_xml = """
        <session>
            <submit>Result first</submit>
            <prompt>Prompt second</prompt>
        </session>
        """
        
        self.assertTrue(self.validator.validate_session_xml(reordered_xml, is_leaf=True))


if __name__ == "__main__":
    unittest.main()