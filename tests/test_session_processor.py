"""Tests for SessionProcessor class."""

import unittest
from unittest.mock import Mock
from src.session_processor import SessionProcessor
from src.tree_node import TreeNode
from src.xml_validator import XmlValidator


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
            "<session>\n<prompt>Question 1?</prompt>\n<submit>Answer 1</submit>\n</session>",
            "<session>\n<prompt>Question 2?</prompt>\n<submit>Answer 2</submit>\n</session>",
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
            "<session>\n<prompt>Test prompt</prompt>\n<ask>Question 1?</ask>\n<response>Answer 1</response>",
            "<session>\n<prompt>Test prompt</prompt>\n<ask>Question 1?</ask>\n<response>Answer 1</response>\n<ask>Question 2?</ask>\n<response>Answer 2</response>",
        ]
        expected_generate_leaf_calls = ["Question 1?", "Question 2?"]

        # Verify the exact calls made to the XML generator
        self.assertEqual(generate_parent_calls, expected_generate_parent_calls)
        self.assertEqual(continue_parent_calls, expected_continue_parent_calls)
        self.assertEqual(generate_leaf_calls, expected_generate_leaf_calls)

        # Create expected TreeNode structure
        expected_root = TreeNode(session_id=0, prompt="Test prompt", depth=0)
        expected_root.session_xml = "<session>\n<prompt>Test prompt</prompt>\n<ask>Question 1?</ask>\n<response>Answer 1</response>\n<ask>Question 2?</ask>\n<response>Answer 2</response>\n<submit>Final content</submit>\n</session>"

        # Create expected child nodes
        child1 = TreeNode(session_id=1, prompt="Question 1?", depth=1)
        child1.session_xml = "<session>\n<prompt>Question 1?</prompt>\n<submit>Answer 1</submit>\n</session>"

        child2 = TreeNode(session_id=2, prompt="Question 2?", depth=1)
        child2.session_xml = "<session>\n<prompt>Question 2?</prompt>\n<submit>Answer 2</submit>\n</session>"

        expected_root.add_child(child1)
        expected_root.add_child(child2)

        # Verify the complete TreeNode structure
        self.assertEqual(result, expected_root)

    def test_mixed_leaf_and_parent_children(self):
        """Test when only some children hit max depth."""
        # Parent response with two asks
        generate_parent_responses = [
            # Root parent - starts by asking a question to its first child
            "<session>\n<prompt>Root prompt</prompt>\n<ask>Deep question?</ask>",
            # First child parent - asks a question
            "<session>\n<prompt>Deep question?</prompt>\n<ask>Nested question?</ask>",
            # Second child parent - doesn't ask a question
            # Is still called with generate_parent because it's at depth 1
            "<session>\n<prompt>Shallow question?</prompt>\n<submit>Shallow answer</submit>\n</session>",
        ]
        continue_parent_responses = [
            # Deep child - continues after processing nested child
            "<session>\n<prompt>Deep question?</prompt>\n<ask>Nested question?</ask>\n<response>Nested answer</response>\n<submit>Deep answer</submit>\n</session>",
            # Root parent - continues by asking a question to its second child
            "<session>\n<prompt>Root prompt</prompt>\n<ask>Deep question?</ask>\n<response>Deep answer</response>\n<ask>Shallow question?</ask>",
            # Root parent - finishes by submitting the final answer
            "<session>\n<prompt>Root prompt</prompt>\n<ask>Deep question?</ask>\n<response>Deep answer</response>\n<ask>Shallow question?</ask>\n<response>Shallow answer</response>\n<submit>Root complete</submit>\n</session>",
        ]
        generate_leaf_responses = [
            # Child of first child parent - submits an answer immediately
            "<session>\n<prompt>Nested question?</prompt>\n<submit>Nested answer</submit>\n</session>",
        ]

        self.mock_xml_generator.generate_parent.side_effect = generate_parent_responses
        self.mock_xml_generator.continue_parent.side_effect = continue_parent_responses
        self.mock_xml_generator.generate_leaf.side_effect = generate_leaf_responses

        # Test with max_depth=2, so depth 0->1 uses parent logic, depth 1->2 uses leaf logic
        processor = SessionProcessor(
            xml_generator=self.mock_xml_generator,
            xml_validator=self.xml_validator,
            max_depth=2,
            max_retries=3,
        )
        result = processor.process_session("Root prompt")

        # Create expected structure
        expected_root = TreeNode(session_id=0, prompt="Root prompt", depth=0)
        expected_root.session_xml = "<session>\n<prompt>Root prompt</prompt>\n<ask>Deep question?</ask>\n<response>Deep answer</response>\n<ask>Shallow question?</ask>\n<response>Shallow answer</response>\n<submit>Root complete</submit>\n</session>"

        # First child is a parent (has nested child)
        deep_child = TreeNode(session_id=1, prompt="Deep question?", depth=1)
        deep_child.session_xml = "<session>\n<prompt>Deep question?</prompt>\n<ask>Nested question?</ask>\n<response>Nested answer</response>\n<submit>Deep answer</submit>\n</session>"

        # Nested child (grandchild of root)
        nested_child = TreeNode(session_id=2, prompt="Nested question?", depth=2)
        nested_child.session_xml = "<session>\n<prompt>Nested question?</prompt>\n<submit>Nested answer</submit>\n</session>"
        deep_child.add_child(nested_child)

        # Second child is a leaf (no children) even though it was called using generate_parent
        shallow_child = TreeNode(session_id=3, prompt="Shallow question?", depth=1)
        shallow_child.session_xml = "<session>\n<prompt>Shallow question?</prompt>\n<submit>Shallow answer</submit>\n</session>"

        expected_root.add_child(deep_child)
        expected_root.add_child(shallow_child)

        self.assertEqual(result, expected_root)

    def test_xml_validation_failure_retry(self):
        """Test retry logic on invalid XML."""
        # First attempt returns invalid XML, second attempt succeeds
        generate_parent_responses = [
            "<session>\n<prompt>Test prompt</prompt>\n<ask>Question?",  # Missing closing </ask> tag - invalid
            "<session>\n<prompt>Test prompt</prompt>\n<ask>Question?</ask>",  # Valid partial XML ending at </ask>
        ]
        continue_parent_responses = [
            "<session>\n<prompt>Test prompt</prompt>\n<ask>Question?</ask>\n<response>Answer</response>\n<submit>Final</submit>\n</session>",
        ]
        generate_leaf_responses = [
            "<session>\n<prompt>Question?</prompt>\n<submit>Answer</submit>\n</session>",
        ]

        self.mock_xml_generator.generate_parent.side_effect = generate_parent_responses
        self.mock_xml_generator.continue_parent.side_effect = continue_parent_responses
        self.mock_xml_generator.generate_leaf.side_effect = generate_leaf_responses

        processor = SessionProcessor(
            xml_generator=self.mock_xml_generator,
            xml_validator=self.xml_validator,
            max_depth=1,
            max_retries=3,
        )
        result = processor.process_session("Test prompt")

        # Should have called generate_parent twice due to retry
        self.assertEqual(len(self.mock_xml_generator.generate_parent.call_args_list), 2)

        # Final result should be successful
        expected_root = TreeNode(session_id=0, prompt="Test prompt", depth=0)
        expected_root.session_xml = "<session>\n<prompt>Test prompt</prompt>\n<ask>Question?</ask>\n<response>Answer</response>\n<submit>Final</submit>\n</session>"

        child = TreeNode(session_id=1, prompt="Question?", depth=1)
        child.session_xml = (
            "<session>\n<prompt>Question?</prompt>\n<submit>Answer</submit>\n</session>"
        )
        expected_root.add_child(child)

        self.assertEqual(result, expected_root)

    def test_max_retries_exceeded_returns_failed(self):
        """Test failure after max retries."""
        # All attempts return invalid XML
        generate_parent_responses = [
            "<session>\n<prompt>Test prompt</prompt>\n<ask>Question?",  # Invalid - missing closing tags
            "<session>\n<prompt>Test prompt</prompt>\n<ask>Question?",  # Invalid - missing closing tags
            "<session>\n<prompt>Test prompt</prompt>\n<ask>Question?",  # Invalid - missing closing tags
            "<session>\n<prompt>Test prompt</prompt>\n<ask>Question?",  # Invalid - missing closing tags (max_retries + 1)
        ]

        self.mock_xml_generator.generate_parent.side_effect = generate_parent_responses

        processor = SessionProcessor(
            xml_generator=self.mock_xml_generator,
            xml_validator=self.xml_validator,
            max_depth=1,
            max_retries=3,
        )
        result = processor.process_session("Test prompt")

        # Should have called generate_parent max_retries + 1 times (initial + 3 retries)
        self.assertEqual(len(self.mock_xml_generator.generate_parent.call_args_list), 4)

        # Result should have "FAILED" as session_xml
        expected_root = TreeNode(session_id=0, prompt="Test prompt", depth=0)
        expected_root.session_xml = "FAILED"

        self.assertEqual(result, expected_root)

    def test_max_retries_exceeded_in_child_returns_failed(self):
        """Test that when a child fails after max retries, only that child has FAILED, not the entire tree."""
        # Root parent generates two asks successfully
        generate_parent_responses = [
            "<session>\n<prompt>Root task</prompt>\n<ask>First child task?</ask>",
        ]
        continue_parent_responses = [
            "<session>\n<prompt>Root task</prompt>\n<ask>First child task?</ask>\n<response>FAILED</response>\n<ask>Second child task?</ask>",
            "<session>\n<prompt>Root task</prompt>\n<ask>First child task?</ask>\n<response>FAILED</response>\n<ask>Second child task?</ask>\n<response>Second child succeeded</response>\n<submit>Root completed with one failed child</submit>\n</session>",
        ]

        generate_leaf_responses = [
            # First child fails after max retries (all invalid XML) - uses generate_leaf since depth=1
            "<session>\n<prompt>First child task?</prompt>\n<submit>Result",  # Invalid - missing closing tags
            "<session>\n<prompt>First child task?</prompt>\n<submit>Result",  # Invalid - retry 1
            "<session>\n<prompt>First child task?</prompt>\n<submit>Result",  # Invalid - retry 2
            "<session>\n<prompt>First child task?</prompt>\n<submit>Result",  # Invalid - retry 3
            # Second child succeeds normally
            "<session>\n<prompt>Second child task?</prompt>\n<submit>Second child succeeded</submit>\n</session>",
        ]

        # Set up the mocks
        self.mock_xml_generator.generate_parent.side_effect = generate_parent_responses
        self.mock_xml_generator.generate_leaf.side_effect = generate_leaf_responses
        self.mock_xml_generator.continue_parent.side_effect = continue_parent_responses

        processor = SessionProcessor(
            xml_generator=self.mock_xml_generator,
            xml_validator=self.xml_validator,
            max_depth=1,
            max_retries=3,
        )
        result = processor.process_session("Root task")

        # Create expected tree structure
        expected_root = TreeNode(session_id=0, prompt="Root task", depth=0)
        expected_root.session_xml = "<session>\n<prompt>Root task</prompt>\n<ask>First child task?</ask>\n<response>FAILED</response>\n<ask>Second child task?</ask>\n<response>Second child succeeded</response>\n<submit>Root completed with one failed child</submit>\n</session>"

        # First child has FAILED
        failed_child = TreeNode(session_id=1, prompt="First child task?", depth=1)
        failed_child.session_xml = "FAILED"

        # Second child succeeded
        successful_child = TreeNode(session_id=2, prompt="Second child task?", depth=1)
        successful_child.session_xml = "<session>\n<prompt>Second child task?</prompt>\n<submit>Second child succeeded</submit>\n</session>"

        expected_root.add_child(failed_child)
        expected_root.add_child(successful_child)

        # Verify the tree structure
        self.assertEqual(result, expected_root)

        # Verify that generate_parent was called only once (for the root)
        self.assertEqual(len(self.mock_xml_generator.generate_parent.call_args_list), 1)

        # Verify that generate_leaf was called 5 times (4 for failed child + 1 for successful child)
        self.assertEqual(len(self.mock_xml_generator.generate_leaf.call_args_list), 5)

    def test_continue_parent_fails_returns_failed(self):
        """Test that when continue_parent fails after max retries, the parent node is FAILED."""
        # Root parent generates three asks successfully
        generate_parent_responses = [
            "<session>\n<prompt>Root task</prompt>\n<ask>First child task?</ask>",
        ]

        # First child succeeds, second child is never called
        generate_leaf_responses = [
            "<session>\n<prompt>First child task?</prompt>\n<submit>First child succeeded</submit>\n</session>",
        ]

        # Continue parent responses - fails after processing first child
        continue_parent_responses = [
            "<session>\n<prompt>Root task</prompt>\n<ask>First child task?</ask>\n<response>First child succeeded</response>\n<ask>Second child task?",  # Invalid - no </ask> tag
            "<session>\n<prompt>Root task</prompt>\n<ask>First child task?</ask>\n<response>First child succeeded</response>\n<ask>Second child task?",  # Invalid - retry 1
            "<session>\n<prompt>Root task</prompt>\n<ask>First child task?</ask>\n<response>First child succeeded</response>\n<ask>Second child task?",  # Invalid - retry 2
            "<session>\n<prompt>Root task</prompt>\n<ask>First child task?</ask>\n<response>First child succeeded</response>\n<ask>Second child task?",  # Invalid - retry 3
        ]

        # Set up the mocks
        self.mock_xml_generator.generate_parent.side_effect = generate_parent_responses
        self.mock_xml_generator.generate_leaf.side_effect = generate_leaf_responses
        self.mock_xml_generator.continue_parent.side_effect = continue_parent_responses

        processor = SessionProcessor(
            xml_generator=self.mock_xml_generator,
            xml_validator=self.xml_validator,
            max_depth=1,
            max_retries=3,
        )
        result = processor.process_session("Root task")

        # Create expected tree structure
        expected_root = TreeNode(session_id=0, prompt="Root task", depth=0)
        # The root should have FAILED because continue_parent failed
        expected_root.session_xml = "FAILED"

        # First child succeeded before the failure
        first_child = TreeNode(session_id=1, prompt="First child task?", depth=1)
        first_child.session_xml = "<session>\n<prompt>First child task?</prompt>\n<submit>First child succeeded</submit>\n</session>"

        expected_root.add_child(first_child)

        # Verify the tree structure
        self.assertEqual(result, expected_root)

        # Verify that generate_parent was called once (for the root)
        self.assertEqual(len(self.mock_xml_generator.generate_parent.call_args_list), 1)

        # Verify that generate_leaf was called only 1 time (first child)
        self.assertEqual(len(self.mock_xml_generator.generate_leaf.call_args_list), 1)

        # Verify that continue_parent was called 4 times (initial + 3 retries)
        self.assertEqual(len(self.mock_xml_generator.continue_parent.call_args_list), 4)


if __name__ == "__main__":
    unittest.main()
