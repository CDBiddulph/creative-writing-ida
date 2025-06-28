"""Tests for SessionProcessor class."""

import unittest
from unittest.mock import Mock
from src.session_processor import SessionProcessor
from src.tree_node import TreeNode
from src.session import Session, ResponseEvent


class TestSessionProcessor(unittest.TestCase):
    """Test the SessionProcessor class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_session_generator = Mock()

    def test_process_session_with_multiple_asks(self):
        # Create Session objects that the mock generator will return
        initial_parent_session = Session.from_xml(
            "<session>\n<prompt>Test prompt</prompt>\n<ask>Question 1?</ask>", 0
        )
        
        continued_parent_session_1 = Session.from_xml(
            "<session>\n<prompt>Test prompt</prompt>\n<ask>Question 1?</ask>\n<response>Answer 1</response>\n<ask>Question 2?</ask>", 0
        )
        
        final_parent_session = Session.from_xml(
            "<session>\n<prompt>Test prompt</prompt>\n<ask>Question 1?</ask>\n<response>Answer 1</response>\n<ask>Question 2?</ask>\n<response>Answer 2</response>\n<submit>Final content</submit>\n</session>", 0
        )
        
        leaf_session_1 = Session.from_xml(
            "<session>\n<prompt>Question 1?</prompt>\n<submit>Answer 1</submit>\n</session>", 1
        )
        
        leaf_session_2 = Session.from_xml(
            "<session>\n<prompt>Question 2?</prompt>\n<submit>Answer 2</submit>\n</session>", 2
        )

        # Set up mock returns
        self.mock_session_generator.generate_parent.return_value = initial_parent_session
        self.mock_session_generator.continue_parent.side_effect = [continued_parent_session_1, final_parent_session]
        self.mock_session_generator.generate_leaf.side_effect = [leaf_session_1, leaf_session_2]

        # Test with depth 1 so that generate_leaf will be called
        processor = SessionProcessor(
            session_generator=self.mock_session_generator,
            max_depth=1,
            max_retries=3,
        )
        result = processor.process_session("Test prompt")

        # Verify the calls made to the session generator
        self.mock_session_generator.generate_parent.assert_called_once_with("Test prompt", 0, 3)
        
        # Check generate_leaf calls
        leaf_calls = self.mock_session_generator.generate_leaf.call_args_list
        self.assertEqual(len(leaf_calls), 2)
        self.assertEqual(leaf_calls[0][0], ("Question 1?", 1, 3))  # prompt, session_id, max_retries
        self.assertEqual(leaf_calls[1][0], ("Question 2?", 2, 3))

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
        # Create Session objects for the mock
        root_parent_session = Session.from_xml(
            "<session>\n<prompt>Root prompt</prompt>\n<ask>Deep question?</ask>", 0
        )
        
        deep_child_parent_session = Session.from_xml(
            "<session>\n<prompt>Deep question?</prompt>\n<ask>Nested question?</ask>", 1
        )
        
        shallow_child_parent_session = Session.from_xml(
            "<session>\n<prompt>Shallow question?</prompt>\n<submit>Shallow answer</submit>\n</session>", 3
        )
        
        deep_child_continued_session = Session.from_xml(
            "<session>\n<prompt>Deep question?</prompt>\n<ask>Nested question?</ask>\n<response>Nested answer</response>\n<submit>Deep answer</submit>\n</session>", 1
        )
        
        root_continued_session_1 = Session.from_xml(
            "<session>\n<prompt>Root prompt</prompt>\n<ask>Deep question?</ask>\n<response>Deep answer</response>\n<ask>Shallow question?</ask>", 0
        )
        
        root_final_session = Session.from_xml(
            "<session>\n<prompt>Root prompt</prompt>\n<ask>Deep question?</ask>\n<response>Deep answer</response>\n<ask>Shallow question?</ask>\n<response>Shallow answer</response>\n<submit>Root complete</submit>\n</session>", 0
        )
        
        nested_leaf_session = Session.from_xml(
            "<session>\n<prompt>Nested question?</prompt>\n<submit>Nested answer</submit>\n</session>", 2
        )

        # Set up mock returns
        self.mock_session_generator.generate_parent.side_effect = [
            root_parent_session,
            deep_child_parent_session, 
            shallow_child_parent_session
        ]
        self.mock_session_generator.continue_parent.side_effect = [
            deep_child_continued_session,
            root_continued_session_1,
            root_final_session
        ]
        self.mock_session_generator.generate_leaf.return_value = nested_leaf_session

        # Test with max_depth=2, so depth 0->1 uses parent logic, depth 1->2 uses leaf logic
        processor = SessionProcessor(
            session_generator=self.mock_session_generator,
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

        # Second child is a parent that completes immediately (no children)
        shallow_child = TreeNode(session_id=3, prompt="Shallow question?", depth=1)
        shallow_child.session_xml = "<session>\n<prompt>Shallow question?</prompt>\n<submit>Shallow answer</submit>\n</session>"

        expected_root.add_child(deep_child)
        expected_root.add_child(shallow_child)

        self.assertEqual(result, expected_root)

    def test_xml_validation_failure_retry(self):
        """Test retry logic when SessionGenerator handles internal validation and retries."""
        # Create Session objects that the mock generator will return
        initial_parent_session = Session.from_xml(
            "<session>\n<prompt>Test prompt</prompt>\n<ask>Question?</ask>", 0
        )
        
        final_parent_session = Session.from_xml(
            "<session>\n<prompt>Test prompt</prompt>\n<ask>Question?</ask>\n<response>Answer</response>\n<submit>Final</submit>\n</session>", 0
        )
        
        leaf_session = Session.from_xml(
            "<session>\n<prompt>Question?</prompt>\n<submit>Answer</submit>\n</session>", 1
        )

        # Set up mock returns - SessionGenerator handles retries internally
        self.mock_session_generator.generate_parent.return_value = initial_parent_session
        self.mock_session_generator.continue_parent.return_value = final_parent_session
        self.mock_session_generator.generate_leaf.return_value = leaf_session

        processor = SessionProcessor(
            session_generator=self.mock_session_generator,
            max_depth=1,
            max_retries=3,
        )
        result = processor.process_session("Test prompt")

        # Verify the calls made to the session generator
        self.mock_session_generator.generate_parent.assert_called_once_with("Test prompt", 0, 3)
        self.mock_session_generator.generate_leaf.assert_called_once_with("Question?", 1, 3)

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
        # Create a failed Session object that the mock generator will return
        failed_session = Session(session_id=0, events=[], is_failed=True)

        self.mock_session_generator.generate_parent.return_value = failed_session

        processor = SessionProcessor(
            session_generator=self.mock_session_generator,
            max_depth=1,
            max_retries=3,
        )
        result = processor.process_session("Test prompt")

        # Should have called generate_parent once (SessionGenerator handles retries internally)
        self.mock_session_generator.generate_parent.assert_called_once_with("Test prompt", 0, 3)

        # Result should have "FAILED" as session_xml
        expected_root = TreeNode(session_id=0, prompt="Test prompt", depth=0)
        expected_root.session_xml = "FAILED"

        self.assertEqual(result, expected_root)

    def test_max_retries_exceeded_in_child_returns_failed(self):
        """Test that when a child fails after max retries, only that child has FAILED, not the entire tree."""
        # Create Session objects for the mock
        initial_parent_session = Session.from_xml(
            "<session>\n<prompt>Root task</prompt>\n<ask>First child task?</ask>", 0
        )
        
        continued_parent_session_1 = Session.from_xml(
            "<session>\n<prompt>Root task</prompt>\n<ask>First child task?</ask>\n<response>FAILED</response>\n<ask>Second child task?</ask>", 0
        )
        
        final_parent_session = Session.from_xml(
            "<session>\n<prompt>Root task</prompt>\n<ask>First child task?</ask>\n<response>FAILED</response>\n<ask>Second child task?</ask>\n<response>Second child succeeded</response>\n<submit>Root completed with one failed child</submit>\n</session>", 0
        )

        # First child fails (SessionGenerator returns failed Session)
        failed_child_session = Session(session_id=1, events=[], is_failed=True)
        
        # Second child succeeds
        successful_child_session = Session.from_xml(
            "<session>\n<prompt>Second child task?</prompt>\n<submit>Second child succeeded</submit>\n</session>", 2
        )

        # Set up the mocks
        self.mock_session_generator.generate_parent.return_value = initial_parent_session
        self.mock_session_generator.generate_leaf.side_effect = [failed_child_session, successful_child_session]
        self.mock_session_generator.continue_parent.side_effect = [continued_parent_session_1, final_parent_session]

        processor = SessionProcessor(
            session_generator=self.mock_session_generator,
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
        self.mock_session_generator.generate_parent.assert_called_once_with("Root task", 0, 3)

        # Verify that generate_leaf was called 2 times (failed child + successful child)
        leaf_calls = self.mock_session_generator.generate_leaf.call_args_list
        self.assertEqual(len(leaf_calls), 2)
        self.assertEqual(leaf_calls[0][0], ("First child task?", 1, 3))
        self.assertEqual(leaf_calls[1][0], ("Second child task?", 2, 3))

    def test_continue_parent_fails_returns_failed(self):
        """Test that when continue_parent fails after max retries, the parent node is FAILED."""
        # Create Session objects for the mock
        initial_parent_session = Session.from_xml(
            "<session>\n<prompt>Root task</prompt>\n<ask>First child task?</ask>", 0
        )

        # First child succeeds
        successful_child_session = Session.from_xml(
            "<session>\n<prompt>First child task?</prompt>\n<submit>First child succeeded</submit>\n</session>", 1
        )

        # Continue parent fails (SessionGenerator returns failed Session)
        failed_continue_session = Session(session_id=0, events=[], is_failed=True)

        # Set up the mocks
        self.mock_session_generator.generate_parent.return_value = initial_parent_session
        self.mock_session_generator.generate_leaf.return_value = successful_child_session
        self.mock_session_generator.continue_parent.return_value = failed_continue_session

        processor = SessionProcessor(
            session_generator=self.mock_session_generator,
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
        self.mock_session_generator.generate_parent.assert_called_once_with("Root task", 0, 3)

        # Verify that generate_leaf was called only 1 time (first child)
        self.mock_session_generator.generate_leaf.assert_called_once_with("First child task?", 1, 3)

        # Verify that continue_parent was called once (SessionGenerator handles retries internally)
        self.mock_session_generator.continue_parent.assert_called_once()

    def test_placeholder_replacement_in_ask(self):
        """Test that placeholders in ask text are replaced before processing child."""
        # Create Session objects with placeholders
        initial_parent_session = Session.from_xml(
            '<session>\n<prompt>Write a story about cats</prompt>\n<ask>Based on $PROMPT, give me ideas</ask>', 0
        )
        
        continued_parent_session = Session.from_xml(
            '<session>\n<prompt>Write a story about cats</prompt>\n<ask>Based on $PROMPT, give me ideas</ask>\n<response>Fluffy cats playing</response>\n<ask>Expand on $RESPONSE1</ask>', 0
        )
        
        final_parent_session = Session.from_xml(
            '<session>\n<prompt>Write a story about cats</prompt>\n<ask>Based on $PROMPT, give me ideas</ask>\n<response>Fluffy cats playing</response>\n<ask>Expand on $RESPONSE1</ask>\n<response>A detailed story about fluffy cats</response>\n<submit>Final story combining $PROMPT with $RESPONSE1 and $RESPONSE2</submit>\n</session>', 0
        )
        
        # Child sessions should receive resolved text
        leaf_session_1 = Session.from_xml(
            '<session>\n<prompt>Based on Write a story about cats, give me ideas</prompt>\n<submit>Fluffy cats playing</submit>\n</session>', 1
        )
        
        leaf_session_2 = Session.from_xml(
            '<session>\n<prompt>Expand on Fluffy cats playing</prompt>\n<submit>A detailed story about fluffy cats</submit>\n</session>', 2
        )

        # Set up mock returns
        self.mock_session_generator.generate_parent.return_value = initial_parent_session
        self.mock_session_generator.continue_parent.side_effect = [continued_parent_session, final_parent_session]
        self.mock_session_generator.generate_leaf.side_effect = [leaf_session_1, leaf_session_2]

        processor = SessionProcessor(
            session_generator=self.mock_session_generator,
            max_depth=1,
            max_retries=3,
        )
        result = processor.process_session("Write a story about cats")

        # Verify that children received resolved prompts
        self.assertEqual(result.children[0].prompt, "Based on Write a story about cats, give me ideas")
        self.assertEqual(result.children[1].prompt, "Expand on Fluffy cats playing")
        
        # Verify the generate_leaf calls received resolved text
        leaf_calls = self.mock_session_generator.generate_leaf.call_args_list
        self.assertEqual(leaf_calls[0][0], ("Based on Write a story about cats, give me ideas", 1, 3))
        self.assertEqual(leaf_calls[1][0], ("Expand on Fluffy cats playing", 2, 3))

    def test_nested_placeholder_resolution_in_child_submit(self):
        """Test that placeholders in child's submit are resolved when added to parent's response."""
        # Test scenario: Parent delegates to child, child delegates to grandchildren,
        # and child's submit contains placeholders referencing grandchildren responses
        
        # Parent session starts with initial ask
        initial_parent_session = Session.from_xml(
            '<session>\n<prompt>Main task</prompt>\n<ask>Subtask A</ask>', 0
        )
        
        # Child session that will delegate to its own children
        child_session_initial = Session.from_xml(
            '<session>\n<prompt>Subtask A</prompt>\n<ask>Subtask A1</ask>', 1
        )
        
        # First grandchild completes immediately
        grandchild_1 = Session.from_xml(
            '<session>\n<prompt>Subtask A1</prompt>\n<submit>Result A1</submit>\n</session>', 2
        )
        
        # Child continues after receiving first response
        child_session_continued = Session.from_xml(
            '<session>\n<prompt>Subtask A</prompt>\n<ask>Subtask A1</ask>\n<response>Result A1</response>\n<ask>Subtask A2 based on $RESPONSE1</ask>', 1
        )
        
        # Second grandchild receives resolved prompt and completes
        grandchild_2 = Session.from_xml(
            '<session>\n<prompt>Subtask A2 based on Result A1</prompt>\n<submit>Result A2</submit>\n</session>', 3
        )
        
        # Child completes with placeholder in submit
        child_session_final = Session.from_xml(
            '<session>\n<prompt>Subtask A</prompt>\n<ask>Subtask A1</ask>\n<response>Result A1</response>\n<ask>Subtask A2 based on $RESPONSE1</ask>\n<response>Result A2</response>\n<submit>$RESPONSE2</submit>\n</session>', 1
        )
        
        # Parent continues and completes after receiving the resolved child response
        continued_parent_session = Session.from_xml(
            '<session>\n<prompt>Main task</prompt>\n<ask>Subtask A</ask>\n<response>Result A2</response>\n<submit>Final result</submit>\n</session>', 0
        )

        # Set up mock returns for nested structure
        self.mock_session_generator.generate_parent.side_effect = [initial_parent_session, child_session_initial]
        self.mock_session_generator.generate_leaf.side_effect = [grandchild_1, grandchild_2]
        self.mock_session_generator.continue_parent.side_effect = [
            child_session_continued,
            child_session_final,
            continued_parent_session
        ]

        processor = SessionProcessor(
            session_generator=self.mock_session_generator,
            max_depth=2,
            max_retries=3,
        )
        result = processor.process_session("Main task")
        
        # Verify the parent's response contains the resolved text
        parent_session = result.session
        response_events = [e for e in parent_session.events if isinstance(e, ResponseEvent)]
        
        # The response should contain "Result A2" (the resolved value of $RESPONSE2 from the child's context)
        self.assertEqual(response_events[0].text, "Result A2",
                        "Child's submit placeholders should be resolved before adding to parent's response")


if __name__ == "__main__":
    unittest.main()
