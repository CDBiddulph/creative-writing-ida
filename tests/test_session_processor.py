"""Tests for SessionProcessor class."""

import unittest
from unittest.mock import Mock
from src.session_processor import SessionProcessor
from src.tree_node import TreeNode
from src.xml_validator import XmlValidator
import xml.etree.ElementTree as ET


def _normalize_text(s):
    """Normalize text by stripping if it consists only of whitespace."""
    if s is None:
        return None
    s = s.strip()
    return None if s == "" else s


def _elements_are_equal(e1, e2):
    if e1.tag != e2.tag:
        return False
    if _normalize_text(e1.text) != _normalize_text(e2.text):
        return False
    if _normalize_text(e1.tail) != _normalize_text(e2.tail):
        return False
    if list(e1.attrib.items()) != list(e2.attrib.items()):  # Order-sensitive
        return False
    if len(e1) != len(e2):
        return False
    return all(_elements_are_equal(c1, c2) for c1, c2 in zip(e1, e2))


def xml_are_equivalent(xml1, xml2):
    """Compare two XML strings for structural and textual equivalence,
    ignoring insignificant whitespace but preserving attribute order.
    """
    try:
        tree1 = ET.fromstring(xml1)
        tree2 = ET.fromstring(xml2)
        return _elements_are_equal(tree1, tree2)
    except ET.ParseError:
        return False


def xml_lists_are_equivalent(xml_list1, xml_list2):
    """Compare two lists of XML strings for equivalence."""
    return len(xml_list1) == len(xml_list2) and all(
        xml_are_equivalent(x, y) for x, y in zip(xml_list1, xml_list2)
    )


class TestXmlAreEquivalent(unittest.TestCase):
    """Test the xml_are_equivalent testing function."""

    def test_equal_xml_are_equivalent(self):
        """Test that the xml_are_equivalent function works."""
        self.assertTrue(
            xml_are_equivalent(
                "<session><prompt>Test prompt</prompt></session>",
                "<session><prompt>Test prompt</prompt></session>",
            )
        )

    def test_xml_with_newlines_are_equivalent(self):
        self.assertTrue(
            xml_are_equivalent(
                "<session><prompt>Test prompt</prompt>\n</session>",
                "<session><prompt>Test prompt</prompt></session>",
            )
        )

    def test_xml_with_spaces_in_value_are_equivalent(self):
        self.assertTrue(
            xml_are_equivalent(
                "<session><prompt>Test prompt</prompt></session>",
                "<session><prompt>Test prompt </prompt></session>",
            )
        )

    def test_xml_with_different_text_are_not_equivalent(self):
        self.assertFalse(
            xml_are_equivalent(
                "<session><prompt>Test prompt</prompt></session>",
                "<session><prompt>Test prompt 2</prompt></session>",
            )
        )

    def test_xml_lists_are_equivalent(self):
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


class TestSessionProcessor(unittest.TestCase):
    """Test the SessionProcessor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_xml_generator = Mock()
        self.xml_validator = XmlValidator()

    def test_process_session_with_multiple_asks(self):
        generate_parent_responses = [
            "<session>\n<prompt>Test prompt</prompt>\n<ask>Question 1?</ask>",
        ]
        continue_parent_responses = [
            "<session>\n<prompt>Test prompt</prompt>\n<ask>Question 1?</ask>\n<response>Answer 1</response>\n<ask>Question 2?</ask>",
            "<session>\n<prompt>Test prompt</prompt>\n<ask>Question 1?</ask>\n<response>Answer 1</response>\n<ask>Question 2?</ask>\n<response>Answer 2</response>\n<submit>Final content</submit>\n</session>",
        ]
        generate_leaf_responses = [
            "<session><prompt>Question 1?</prompt><submit>Answer 1</submit></session>",
            "<session><prompt>Question 2?</prompt><submit>Answer 2</submit></session>",
        ]

        self.mock_xml_generator.generate_parent.side_effect = generate_parent_responses
        self.mock_xml_generator.continue_parent.side_effect = continue_parent_responses
        self.mock_xml_generator.generate_leaf.side_effect = generate_leaf_responses

        # Test with depth 1 so that generate_leaf will be called
        processor = SessionProcessor(
            xml_generator=self.mock_xml_generator,
            xml_validator=self.xml_validator,
            max_depth=1,
            max_retries=3,
        )
        result = processor.process_session("Test prompt")

        # Verify the exact calls made to generate_parent
        generate_parent_calls = [
            call[0][0]
            for call in self.mock_xml_generator.generate_parent.call_args_list
        ]
        continue_parent_calls = [
            call[0][0]
            for call in self.mock_xml_generator.continue_parent.call_args_list
        ]
        generate_leaf_calls = [
            call[0][0] for call in self.mock_xml_generator.generate_leaf.call_args_list
        ]

        expected_generate_parent_calls = ["Test prompt"]
        expected_continue_parent_calls = [
            "<session>\n<prompt>Test prompt</prompt>\n<ask>Question 1?</ask>\n<response>Answer 1</response>\n<submit>Final content</submit>\n<ask></ask>",
        ]
        expected_generate_leaf_calls = ["Question 1?", "Question 2?"]

        # Verify the exact calls made to the XML generator
        self.assertTrue(
            xml_lists_are_equivalent(
                generate_parent_calls, expected_generate_parent_calls
            )
        )
        self.assertTrue(
            xml_lists_are_equivalent(
                continue_parent_calls, expected_continue_parent_calls
            )
        )
        self.assertTrue(
            xml_lists_are_equivalent(generate_leaf_calls, expected_generate_leaf_calls)
        )

        # Create expected TreeNode structure
        expected_root = TreeNode(session_id=0, prompt="Test prompt", depth=0)
        expected_root.session_xml = "<session>\n<prompt>Test prompt</prompt>\n<ask>Question 1?</ask>\n<response>Answer 1</response>\n<ask>Question 2?</ask>\n<response>Answer 2</response>\n<submit>Final content</submit>\n</session>"
        
        # Create expected child nodes
        child1 = TreeNode(session_id=1, prompt="Question 1?", depth=1)
        child1.session_xml = "<session><prompt>Question 1?</prompt><submit>Answer 1</submit></session>"
        
        child2 = TreeNode(session_id=2, prompt="Question 2?", depth=1)
        child2.session_xml = "<session><prompt>Question 2?</prompt><submit>Answer 2</submit></session>"
        
        expected_root.add_child(child1)
        expected_root.add_child(child2)
        
        # Verify the complete TreeNode structure
        self.assertEqual(result, expected_root)


if __name__ == "__main__":
    unittest.main()
