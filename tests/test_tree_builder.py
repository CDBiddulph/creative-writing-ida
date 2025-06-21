"""Tests for the tree_builder module."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from tree_builder import TreeBuilder
from models import Session, TreeNode


class TestTreeBuilder(unittest.TestCase):
    """Test the TreeBuilder class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.builder = TreeBuilder()
    
    def test_build_tree_depth_1(self):
        """Test building a tree with depth 1 (just root)."""
        root = self.builder.build_tree("Root prompt", tree_depth=1)
        
        self.assertEqual(root.session.prompt, "Root prompt")
        self.assertEqual(root.session.id, 0)
        self.assertEqual(root.depth, 0)
        self.assertTrue(root.is_leaf)
        self.assertEqual(len(root.children), 0)
    
    def test_build_tree_depth_2(self):
        """Test building a tree with depth 2 (root + child)."""
        root = self.builder.build_tree("Root prompt", tree_depth=2)
        
        self.assertEqual(root.session.prompt, "Root prompt")
        self.assertEqual(root.session.id, 0)
        self.assertEqual(root.depth, 0)
        self.assertFalse(root.is_leaf)
        self.assertEqual(len(root.children), 1)
        
        child = root.children[0]
        self.assertEqual(child.session.id, 1)
        self.assertEqual(child.session.responding_to_id, 0)
        self.assertEqual(child.depth, 1)
        self.assertTrue(child.is_leaf)
        self.assertEqual(len(child.children), 0)
    
    def test_build_tree_depth_3(self):
        """Test building a tree with depth 3."""
        root = self.builder.build_tree("Root prompt", tree_depth=3)
        
        # Check root
        self.assertEqual(root.session.id, 0)
        self.assertFalse(root.is_leaf)
        self.assertEqual(len(root.children), 1)
        
        # Check middle node
        middle = root.children[0]
        self.assertEqual(middle.session.id, 1)
        self.assertEqual(middle.depth, 1)
        self.assertFalse(middle.is_leaf)
        self.assertEqual(len(middle.children), 1)
        
        # Check leaf
        leaf = middle.children[0]
        self.assertEqual(leaf.session.id, 2)
        self.assertEqual(leaf.depth, 2)
        self.assertTrue(leaf.is_leaf)
        self.assertEqual(len(leaf.children), 0)
    
    def test_get_all_sessions_preorder(self):
        """Test getting all sessions in pre-order traversal."""
        root = self.builder.build_tree("Root", tree_depth=3)
        sessions = self.builder.get_all_sessions_preorder(root)
        
        self.assertEqual(len(sessions), 3)
        self.assertEqual([s.id for s in sessions], [0, 1, 2])
    
    def test_get_leaf_nodes(self):
        """Test getting all leaf nodes."""
        root = self.builder.build_tree("Root", tree_depth=3)
        leaves = self.builder.get_leaf_nodes(root)
        
        self.assertEqual(len(leaves), 1)
        self.assertEqual(leaves[0].session.id, 2)
        self.assertTrue(leaves[0].is_leaf)
    
    def test_get_leaf_nodes_single_node(self):
        """Test getting leaf nodes when root is the only node."""
        root = self.builder.build_tree("Root", tree_depth=1)
        leaves = self.builder.get_leaf_nodes(root)
        
        self.assertEqual(len(leaves), 1)
        self.assertEqual(leaves[0].session.id, 0)
        self.assertTrue(leaves[0].is_leaf)
    
    def test_get_nodes_by_depth(self):
        """Test getting nodes at specific depth."""
        root = self.builder.build_tree("Root", tree_depth=3)
        
        # Depth 0 - just root
        depth_0 = self.builder.get_nodes_by_depth(root, 0)
        self.assertEqual(len(depth_0), 1)
        self.assertEqual(depth_0[0].session.id, 0)
        
        # Depth 1 - middle node
        depth_1 = self.builder.get_nodes_by_depth(root, 1)
        self.assertEqual(len(depth_1), 1)
        self.assertEqual(depth_1[0].session.id, 1)
        
        # Depth 2 - leaf
        depth_2 = self.builder.get_nodes_by_depth(root, 2)
        self.assertEqual(len(depth_2), 1)
        self.assertEqual(depth_2[0].session.id, 2)
        
        # Depth 3 - no nodes
        depth_3 = self.builder.get_nodes_by_depth(root, 3)
        self.assertEqual(len(depth_3), 0)
    
    def test_reset_id_counter(self):
        """Test resetting the ID counter."""
        # Build first tree
        root1 = self.builder.build_tree("First", tree_depth=2)
        self.assertEqual(root1.session.id, 0)
        self.assertEqual(root1.children[0].session.id, 1)
        
        # Reset and build second tree
        self.builder.reset_id_counter()
        root2 = self.builder.build_tree("Second", tree_depth=2)
        self.assertEqual(root2.session.id, 0)
        self.assertEqual(root2.children[0].session.id, 1)


if __name__ == '__main__':
    unittest.main()