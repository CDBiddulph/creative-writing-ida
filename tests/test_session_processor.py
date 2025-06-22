"""Tests for SessionProcessor class."""

import unittest
from unittest.mock import Mock
from src.session_processor import SessionProcessor
from src.tree_builder import TreeNode
from src.xml_validator import XmlValidator


class TestSessionProcessor(unittest.TestCase):
    """Test the SessionProcessor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_xml_generator = Mock()
        self.xml_validator = XmlValidator()
        self.max_depth = 2
        self.processor = SessionProcessor(
            xml_generator=self.mock_xml_generator,
            xml_validator=self.xml_validator,
            max_depth=self.max_depth,
            max_retries=3,
        )

    def test_init(self):
        """Test SessionProcessor initialization."""
        self.assertIsInstance(self.processor, SessionProcessor)

    def test_process_session_leaf_node(self):
        """Test processing a leaf node (at max depth)."""
        # Mock generator returns complete leaf XML
        self.mock_xml_generator.generate_leaf.return_value = "<session><prompt>Write a story</prompt><submit>Story content here</submit></session>"

        result = self.processor.process_session("Write a story", depth=2, session_id=0)

        self.assertIsInstance(result, TreeNode)
        self.assertEqual(result.session_id, 0)
        self.assertEqual(result.depth, 2)
        self.assertEqual(len(result.children), 0)  # Leaf should have no children
        self.assertIn("Story content here", result.session_xml)

    def test_process_session_parent_node_no_asks(self):
        """Test processing a parent node that doesn't create any asks."""
        # Mock generator returns parent XML without asks
        self.mock_xml_generator.generate_parent.return_value = (
            "<session><prompt>Simple task</prompt><notes>No need for help</notes>"
            "<submit>Direct answer</submit></session>"
        )

        result = self.processor.process_session("Simple task", depth=0, session_id=0)

        self.assertIsInstance(result, TreeNode)
        self.assertEqual(result.session_id, 0)
        self.assertEqual(result.depth, 0)
        self.assertEqual(len(result.children), 0)  # No asks means no children
        self.assertIn("Direct answer", result.session_xml)

    def test_process_session_parent_node_with_asks(self):
        """Test processing a parent node that creates child sessions via asks."""

        # Mock generator behavior for parent with asks
        def mock_generate_parent(prompt):
            if isinstance(prompt, str) and not prompt.startswith("<session>"):
                # First call: return partial XML stopping at </ask>
                return "<session><prompt>Write a story</prompt><notes>Need ideas</notes><ask>What genre should it be?</ask>"
            else:
                # Continuation calls after response insertion
                return "<submit>Final story based on genre</submit></session>"

        # Mock generator for child leaf
        def mock_generate_leaf(prompt):
            return "<session><prompt>What genre should it be?</prompt><submit>Science fiction</submit></session>"

        self.mock_xml_generator.generate_parent.side_effect = mock_generate_parent
        self.mock_xml_generator.generate_leaf.side_effect = mock_generate_leaf

        result = self.processor.process_session("Write a story", depth=0, session_id=0)

        self.assertIsInstance(result, TreeNode)
        self.assertEqual(result.session_id, 0)
        self.assertEqual(result.depth, 0)
        self.assertEqual(len(result.children), 1)  # Should have one child from the ask

        # Check child node
        child = result.children[0]
        self.assertEqual(child.session_id, 1)  # Next available ID
        self.assertEqual(child.depth, 1)
        self.assertIn("Science fiction", child.session_xml)

    def test_process_session_multiple_asks(self):
        """Test processing a parent node with multiple asks."""
        ask_count = 0

        def mock_generate_parent(prompt):
            if isinstance(prompt, str) and not prompt.startswith("<session>"):
                # First call: return partial XML stopping at first ask
                return "<session><prompt>Complex story</prompt><ask>What's the setting?</ask>"
            elif (
                "<response>Space station</response>" in prompt
                and "<ask>Who's the protagonist?</ask>" not in prompt
            ):
                # Second continuation after first response: return second ask
                return "<ask>Who's the protagonist?</ask>"
            else:
                # Final continuation: complete the session
                return "<submit>Story with setting and protagonist</submit></session>"

        def mock_generate_leaf(prompt):
            if "setting" in prompt:
                return "<session><prompt>What's the setting?</prompt><submit>Space station</submit></session>"
            else:
                return "<session><prompt>Who's the protagonist?</prompt><submit>Robot detective</submit></session>"

        self.mock_xml_generator.generate_parent.side_effect = mock_generate_parent
        self.mock_xml_generator.generate_leaf.side_effect = mock_generate_leaf

        result = self.processor.process_session("Complex story", depth=0, session_id=0)

        self.assertEqual(len(result.children), 2)  # Two asks = two children
        self.assertEqual(result.children[0].session_id, 1)
        self.assertEqual(result.children[1].session_id, 2)

    def test_process_session_nested_tree(self):
        """Test processing that creates a multi-level tree."""

        def mock_generate_parent(prompt):
            if "root task" in prompt:
                return "<session><prompt>root task</prompt><ask>subtask 1</ask>"
            elif "subtask 1" in prompt:
                return "<session><prompt>subtask 1</prompt><ask>leaf task</ask>"
            else:
                return "<submit>Continuing after response</submit></session>"

        def mock_generate_leaf(prompt):
            return f"<session><prompt>{prompt}</prompt><submit>Leaf result</submit></session>"

        self.mock_xml_generator.generate_parent.side_effect = mock_generate_parent
        self.mock_xml_generator.generate_leaf.side_effect = mock_generate_leaf

        result = self.processor.process_session("root task", depth=0, session_id=0)

        # Should have nested structure: root -> child -> grandchild
        self.assertEqual(len(result.children), 1)
        child = result.children[0]
        self.assertEqual(len(child.children), 1)
        grandchild = child.children[0]
        self.assertEqual(len(grandchild.children), 0)  # Leaf node

    def test_process_session_with_retries(self):
        """Test retry logic when XML generation fails."""
        # Fail twice, then succeed
        self.mock_xml_generator.generate_leaf.side_effect = [
            Exception("Network error"),
            Exception("Timeout"),
            "<session><prompt>Test</prompt><submit>Success</submit></session>",
        ]

        result = self.processor.process_session("Test prompt", depth=2, session_id=0)

        self.assertIsInstance(result, TreeNode)
        self.assertIn("Success", result.session_xml)
        self.assertEqual(self.mock_xml_generator.generate_leaf.call_count, 3)

    def test_process_session_max_retries_exceeded(self):
        """Test behavior when max retries are exceeded."""
        # Always fail
        self.mock_xml_generator.generate_leaf.side_effect = Exception("Always fails")

        result = self.processor.process_session("Test prompt", depth=2, session_id=0)

        self.assertIsInstance(result, TreeNode)
        self.assertEqual(result.session_xml, "FAILED")
        self.assertEqual(self.mock_xml_generator.generate_leaf.call_count, 3)

    def test_process_session_invalid_xml(self):
        """Test handling of invalid XML from generator."""
        # Mock validator to reject XML
        self.xml_validator.validate_session_xml = Mock(return_value=False)

        # Should retry when validation fails
        self.mock_xml_generator.generate_leaf.side_effect = [
            "<invalid>Bad XML</invalid>",
            "<session><prompt>Test</prompt><submit>Good XML</submit></session>",
        ]

        result = self.processor.process_session("Test prompt", depth=2, session_id=0)

        self.assertIn("Good XML", result.session_xml)

    def test_session_id_calculation(self):
        """Test that session IDs are calculated correctly for complex trees."""

        def mock_generate_parent(prompt):
            if "root" in prompt:
                return "<session><prompt>root</prompt><ask>child1</ask>"
            return "<submit>Done</submit></session>"

        def mock_generate_leaf(prompt):
            return (
                f"<session><prompt>{prompt}</prompt><submit>Result</submit></session>"
            )

        self.mock_xml_generator.generate_parent.side_effect = mock_generate_parent
        self.mock_xml_generator.generate_leaf.side_effect = mock_generate_leaf

        result = self.processor.process_session("root task", depth=0, session_id=5)

        # Root should have ID 5, child should have ID 6
        self.assertEqual(result.session_id, 5)
        self.assertEqual(result.children[0].session_id, 6)

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
        processor_depth_1 = SessionProcessor(
            xml_generator=self.mock_xml_generator,
            xml_validator=self.xml_validator,
            max_depth=1,
            max_retries=3,
        )
        result = processor_depth_1.process_session("Test prompt", depth=0, session_id=0)

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

        self.assertEqual(generate_parent_calls, expected_generate_parent_calls)
        self.assertEqual(continue_parent_calls, expected_continue_parent_calls)
        self.assertEqual(generate_leaf_calls, expected_generate_leaf_calls)

        # Verify the result
        self.assertEqual(
            result.session_xml,
            "<session>\n<prompt>Test prompt</prompt>\n<ask>Question 1?</ask>\n<response>Answer 1</response>\n<ask>Question 2?</ask>\n<response>Answer 2</response>\n<submit>Final content</submit>\n</session>",
        )


if __name__ == "__main__":
    unittest.main()
