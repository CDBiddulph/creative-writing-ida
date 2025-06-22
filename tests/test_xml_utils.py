"""Tests for XML utility functions."""

import unittest
from src.xml_utils import xml_are_equivalent, xml_lists_are_equivalent


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


if __name__ == "__main__":
    unittest.main()
