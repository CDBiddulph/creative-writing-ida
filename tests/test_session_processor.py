"""Tests for SessionProcessor class."""

import unittest
from unittest.mock import Mock
from src.session_processor import SessionProcessor
from src.tree_node import TreeNode
from src.xml_validator import XmlValidator
from src.xml_utils import xml_are_equivalent, xml_lists_are_equivalent



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
