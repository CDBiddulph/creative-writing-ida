"""Tests for the models module."""

import unittest
from models import Session, TreeNode, SessionIDManager


class TestSession(unittest.TestCase):
    """Test the Session class."""
    
    def test_session_creation(self):
        """Test basic session creation."""
        session = Session(id=1, prompt="Test prompt")
        self.assertEqual(session.id, 1)
        self.assertEqual(session.prompt, "Test prompt")
        self.assertIsNone(session.responding_to_id)
        self.assertEqual(len(session.notes), 0)
        self.assertEqual(len(session.ask_responses), 0)
        self.assertEqual(session.final_submit, "")
    
    def test_add_note(self):
        """Test adding notes to session."""
        session = Session(id=1, prompt="Test")
        session.add_note("First note")
        session.add_note("Second note")
        self.assertEqual(len(session.notes), 2)
        self.assertEqual(session.notes[0], "First note")
        self.assertEqual(session.notes[1], "Second note")
    
    def test_add_ask_response(self):
        """Test adding ask/response pairs."""
        session = Session(id=1, prompt="Test")
        session.add_ask_response("What color?", "Blue", 2)
        self.assertEqual(len(session.ask_responses), 1)
        ask_resp = session.ask_responses[0]
        self.assertEqual(ask_resp.ask, "What color?")
        self.assertEqual(ask_resp.response, "Blue")
        self.assertEqual(ask_resp.response_session_id, 2)
    
    def test_xml_output_simple(self):
        """Test XML output for simple session."""
        session = Session(id=1, prompt="Test prompt")
        session.set_final_submit("Final answer")
        
        xml = session.to_xml()
        self.assertIn("<session>", xml)
        self.assertIn("<prompt>Test prompt</prompt>", xml)
        self.assertIn("<submit>Final answer</submit>", xml)
        self.assertIn("</session>", xml)
    
    def test_xml_output_with_response_id(self):
        """Test XML output with responding_to_id."""
        session = Session(id=2, prompt="Child prompt", responding_to_id=1)
        session.set_final_submit("Child answer")
        
        xml = session.to_xml()
        self.assertIn("<response-id>1</response-id>", xml)
        self.assertIn("<prompt>Child prompt</prompt>", xml)


class TestTreeNode(unittest.TestCase):
    """Test the TreeNode class."""
    
    def test_tree_node_creation(self):
        """Test basic tree node creation."""
        session = Session(id=1, prompt="Root")
        node = TreeNode(session=session, depth=0, is_leaf=True)
        self.assertEqual(node.session.id, 1)
        self.assertEqual(node.depth, 0)
        self.assertTrue(node.is_leaf)
        self.assertEqual(len(node.children), 0)
    
    def test_add_child(self):
        """Test adding child nodes."""
        root_session = Session(id=1, prompt="Root")
        root_node = TreeNode(session=root_session, depth=0)
        
        child_session = Session(id=2, prompt="Child")
        child_node = TreeNode(session=child_session)
        
        root_node.add_child(child_node)
        
        self.assertEqual(len(root_node.children), 1)
        self.assertEqual(child_node.parent, root_node)
        self.assertEqual(child_node.depth, 1)
    
    def test_preorder_traversal(self):
        """Test pre-order traversal of tree."""
        root_session = Session(id=1, prompt="Root")
        root_node = TreeNode(session=root_session, depth=0)
        
        child1_session = Session(id=2, prompt="Child1")
        child1_node = TreeNode(session=child1_session)
        root_node.add_child(child1_node)
        
        child2_session = Session(id=3, prompt="Child2")
        child2_node = TreeNode(session=child2_session)
        root_node.add_child(child2_node)
        
        sessions = root_node.get_all_sessions_preorder()
        self.assertEqual(len(sessions), 3)
        self.assertEqual(sessions[0].id, 1)  # Root first
        self.assertEqual(sessions[1].id, 2)  # Child1 second
        self.assertEqual(sessions[2].id, 3)  # Child2 third


class TestSessionIDManager(unittest.TestCase):
    """Test the SessionIDManager class."""
    
    def test_id_generation(self):
        """Test ID generation."""
        manager = SessionIDManager()
        self.assertEqual(manager.get_next_id(), 0)
        self.assertEqual(manager.get_next_id(), 1)
        self.assertEqual(manager.get_next_id(), 2)
    
    def test_reset(self):
        """Test ID counter reset."""
        manager = SessionIDManager()
        manager.get_next_id()  # 0
        manager.get_next_id()  # 1
        manager.reset()
        self.assertEqual(manager.get_next_id(), 0)


if __name__ == '__main__':
    unittest.main()