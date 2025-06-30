"""Tests for XML utility functions."""

import unittest
import tempfile
from pathlib import Path
from src.xml_utils import xml_are_equivalent, xml_lists_are_equivalent
from src.xml_service import XmlService


class TestXmlUtils(unittest.TestCase):
    """Test the XML utility functions."""

    def test_equal_xml_are_equivalent(self):
        """Test that identical XML strings are equivalent."""
        self.assertTrue(
            xml_are_equivalent(
                "<session><prompt>Test prompt</prompt></session>",
                "<session><prompt>Test prompt</prompt></session>",
            )
        )

    def test_both_failed_are_equivalent(self):
        """Test that when both are FAILED, they are equivalent."""
        self.assertTrue(xml_are_equivalent("FAILED", "FAILED"))

    def test_xml_with_newlines_are_equivalent(self):
        """Test that XML with insignificant whitespace differences are equivalent."""
        self.assertTrue(
            xml_are_equivalent(
                "<session><prompt>Test prompt</prompt>\n</session>",
                "<session><prompt>Test prompt</prompt></session>",
            )
        )

    def test_xml_with_spaces_in_value_are_equivalent(self):
        """Test that XML with trailing spaces in values are equivalent."""
        self.assertTrue(
            xml_are_equivalent(
                "<session><prompt>Test prompt</prompt></session>",
                "<session><prompt>Test prompt </prompt></session>",
            )
        )

    def test_xml_with_different_text_are_not_equivalent(self):
        """Test that XML with different text content are not equivalent."""
        self.assertFalse(
            xml_are_equivalent(
                "<session><prompt>Test prompt</prompt></session>",
                "<session><prompt>Test prompt 2</prompt></session>",
            )
        )

    def test_none_xml_values(self):
        """Test handling of None values."""
        self.assertTrue(xml_are_equivalent(None, None))
        self.assertFalse(xml_are_equivalent(None, "<session></session>"))
        self.assertFalse(xml_are_equivalent("<session></session>", None))

    def test_malformed_xml_not_equivalent(self):
        """Test that malformed XML returns False."""
        self.assertFalse(
            xml_are_equivalent(
                "<session><prompt>Test",
                "<session><prompt>Test prompt</prompt></session>",
            )
        )

    def test_xml_lists_are_equivalent(self):
        """Test that equivalent XML lists are detected."""
        self.assertTrue(
            xml_lists_are_equivalent(
                [
                    "<session><prompt>Test prompt</prompt></session>",
                    "<session><prompt>Test prompt</prompt><ask>Question 1?</ask></session>",
                ],
                [
                    "<session><prompt>Test prompt</prompt></session>",
                    "<session><prompt>Test prompt</prompt><ask>Question 1?</ask></session>",
                ],
            )
        )

    def test_xml_lists_are_not_equivalent(self):
        """Test that non-equivalent XML lists are detected."""
        self.assertFalse(
            xml_lists_are_equivalent(
                [
                    "<session><prompt>Test prompt</prompt></session>",
                    "<session><prompt>Test prompt</prompt><ask>Question 2?</ask></session>",
                ],
                [
                    "<session><prompt>Test prompt 2</prompt></session>",
                    "<session><prompt>Test prompt</prompt><ask>Question 1?</ask></session>",
                ],
            )
        )

    def test_xml_lists_different_lengths_not_equivalent(self):
        """Test that XML lists of different lengths are not equivalent."""
        self.assertFalse(
            xml_lists_are_equivalent(
                ["<session><prompt>Test</prompt></session>"],
                [
                    "<session><prompt>Test</prompt></session>",
                    "<session><prompt>Test 2</prompt></session>",
                ],
            )
        )

    def test_xml_utils_integration_with_xml_service(self):
        """Test that xml_utils functions work with XmlService generated XML."""
        # Create XmlService instance
        xml_service = XmlService()

        # Create some sessions using xml_service
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(
                """<?xml version="1.0" encoding="UTF-8"?>
<sessions>
<session>
<id>0</id>
<prompt>Test prompt</prompt>
<submit>Test result</submit>
</session>
</sessions>"""
            )
            test_file = Path(f.name)

        # Parse sessions using the service
        sessions = xml_service.parse_sessions_file(test_file)

        # Format them back to XML
        formatted_xml = xml_service.format_sessions_to_xml(sessions)

        # The formatted XML should be equivalent to a reference version
        reference_xml = """<?xml version="1.0" encoding="UTF-8"?>
<sessions>
<session>
<id>0</id>
<prompt>Test prompt</prompt>
<submit>Test result</submit>
</session>
</sessions>"""

        # Use our xml_utils function to compare
        self.assertTrue(xml_are_equivalent(formatted_xml, reference_xml))


if __name__ == "__main__":
    unittest.main()
