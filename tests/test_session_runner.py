"""Tests for the session_runner module."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from unittest.mock import patch, MagicMock
from session_runner import SessionRunner
from models import Session, TreeNode
from api_interface import APIInterface


class MockAPIInterface(APIInterface):
    """Mock API interface for testing."""
    
    def __init__(self, response="Test response"):
        self.response = response
        self.call_count = 0
        self.last_prompt = None
        self.last_model = None
        self.last_examples_xml = None
    
    def call(self, prompt, model, max_tokens, temperature=0.7, examples_xml=""):
        self.call_count += 1
        self.last_prompt = prompt
        self.last_model = model
        self.last_examples_xml = examples_xml
        return self.response


class TestSessionRunner(unittest.TestCase):
    """Test the SessionRunner class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.runner = SessionRunner(
            model="haiku",
            max_tokens=1000,
            temperature=0.5,
            parent_readme_content="Parent README",
            leaf_readme_content="Leaf README",
            parent_examples_xml="<parent>examples</parent>",
            leaf_examples_xml="<leaf>examples</leaf>"
        )
    
    def test_initialization(self):
        """Test SessionRunner initialization."""
        self.assertEqual(self.runner.model, "claude-3-5-haiku-20241022")
        self.assertEqual(self.runner.max_tokens, 1000)
        self.assertEqual(self.runner.temperature, 0.5)
        self.assertEqual(self.runner.parent_readme_content, "Parent README")
        self.assertEqual(self.runner.leaf_readme_content, "Leaf README")
        self.assertEqual(self.runner.api_mode, "claude-base")
    
    def test_initialization_with_hackathon_model(self):
        """Test initialization with as-hackathon model."""
        runner = SessionRunner(
            model="big-base",
            max_tokens=1000,
            temperature=0.5,
            parent_readme_content="Parent",
            leaf_readme_content="Leaf"
        )
        self.assertEqual(runner.model, "as-hackathon-big-base-rollout")
        self.assertEqual(runner.api_mode, "claude-completions")
    
    @patch('session_runner.get_api_interface')
    def test_execute_leaf_session(self, mock_get_api):
        """Test executing a leaf session."""
        # Create mock API
        mock_api = MockAPIInterface("Final submission text")
        mock_get_api.return_value = mock_api
        
        # Create leaf session
        session = Session(id=1, prompt="Leaf prompt")
        
        # Execute
        self.runner._execute_leaf_session(session)
        
        # Check API was called correctly
        self.assertEqual(mock_api.call_count, 1)
        self.assertEqual(mock_api.last_prompt, "Leaf prompt")
        self.assertEqual(mock_api.last_examples_xml, "<leaf>examples</leaf>")
        
        # Check session was updated
        self.assertEqual(session.final_submit, "Final submission text")
    
    def test_split_response_sections_with_tags(self):
        """Test parsing response with XML tags."""
        response = """
        <notes>Initial thoughts</notes>
        <ask>What color should it be?</ask>
        <notes>More thoughts</notes>
        <submit>Final answer</submit>
        """
        
        sections = self.runner._split_response_sections(response)
        
        self.assertEqual(len(sections), 4)
        self.assertEqual(sections[0], ('notes', 'Initial thoughts'))
        self.assertEqual(sections[1], ('ask', 'What color should it be?'))
        self.assertEqual(sections[2], ('notes', 'More thoughts'))
        self.assertEqual(sections[3], ('submit', 'Final answer'))
    
    def test_split_response_sections_no_tags(self):
        """Test parsing response without XML tags."""
        response = "Just plain text response"
        
        sections = self.runner._split_response_sections(response)
        
        self.assertEqual(len(sections), 1)
        self.assertEqual(sections[0], ('submit', response))
    
    @patch('session_runner.get_api_interface')
    def test_execute_parent_session(self, mock_get_api):
        """Test executing a parent session."""
        # Create mock API that returns asks
        mock_api = MockAPIInterface("<ask>First question?</ask>")
        mock_get_api.return_value = mock_api
        
        # Create parent node with child
        parent_session = Session(id=0, prompt="Parent prompt")
        parent_node = TreeNode(session=parent_session, is_leaf=False)
        
        child_session = Session(id=1, prompt="", responding_to_id=0)
        child_node = TreeNode(session=child_session, is_leaf=True)
        parent_node.add_child(child_node)
        
        # Execute
        self.runner._execute_parent_session(parent_node)
        
        # Check API was called
        self.assertEqual(mock_api.call_count, 1)
        self.assertEqual(mock_api.last_prompt, "Parent prompt")
        self.assertEqual(mock_api.last_examples_xml, "<parent>examples</parent>")
        
        # Check child prompt was set
        self.assertEqual(child_node.session.prompt, "First question?")
        
        # Check ask/response was recorded
        self.assertEqual(len(parent_session.ask_responses), 1)
        self.assertEqual(parent_session.ask_responses[0].ask, "First question?")
    
    @patch('session_runner.get_api_interface')
    def test_execute_tree_simple(self, mock_get_api):
        """Test executing a simple tree."""
        # Create different responses for parent and leaf
        responses = ["<ask>Child task</ask>", "Leaf response"]
        mock_api = MagicMock()
        mock_api.call.side_effect = responses
        mock_get_api.return_value = mock_api
        
        # Create simple tree: root -> leaf
        root_session = Session(id=0, prompt="Root prompt")
        root_node = TreeNode(session=root_session, is_leaf=False)
        
        leaf_session = Session(id=1, prompt="", responding_to_id=0)
        leaf_node = TreeNode(session=leaf_session, is_leaf=True)
        root_node.add_child(leaf_node)
        
        # Execute tree
        self.runner.execute_tree(root_node)
        
        # Check both nodes were executed
        self.assertEqual(mock_api.call.call_count, 2)
        
        # Check leaf got prompt from parent's ask
        self.assertEqual(leaf_node.session.prompt, "Child task")
        self.assertEqual(leaf_node.session.final_submit, "Leaf response")


if __name__ == '__main__':
    unittest.main()