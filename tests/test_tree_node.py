"""Tests for TreeNode class."""

import unittest
from src.tree_node import TreeNode


class TestTreeNode(unittest.TestCase):
    """Test the TreeNode class."""

    def test_init(self):
        """Test TreeNode initialization."""
        node = TreeNode(session_id=0, prompt="Test prompt", depth=0)

        self.assertEqual(node.session_id, 0)
        self.assertEqual(node.prompt, "Test prompt")
        self.assertEqual(node.depth, 0)
        self.assertEqual(len(node.children), 0)
        self.assertIsNone(node.session_xml)

    def test_add_child(self):
        """Test adding children to a node."""
        parent = TreeNode(session_id=0, prompt="Parent", depth=0)
        child1 = TreeNode(session_id=1, prompt="Child 1", depth=1)
        child2 = TreeNode(session_id=2, prompt="Child 2", depth=1)

        parent.add_child(child1)
        parent.add_child(child2)

        self.assertEqual(len(parent.children), 2)
        self.assertIn(child1, parent.children)
        self.assertIn(child2, parent.children)

    def test_count_nodes_single_node(self):
        """Test counting nodes for a single node."""
        node = TreeNode(session_id=0, prompt="Single", depth=0)

        self.assertEqual(node.count_nodes(), 1)

    def test_count_nodes_with_children(self):
        """Test counting nodes in a tree with children."""
        root = TreeNode(session_id=0, prompt="Root", depth=0)
        child1 = TreeNode(session_id=1, prompt="Child 1", depth=1)
        child2 = TreeNode(session_id=2, prompt="Child 2", depth=1)
        grandchild = TreeNode(session_id=3, prompt="Grandchild", depth=2)

        root.add_child(child1)
        root.add_child(child2)
        child1.add_child(grandchild)

        # Root + 2 children + 1 grandchild = 4 total
        self.assertEqual(root.count_nodes(), 4)
        self.assertEqual(child1.count_nodes(), 2)  # child1 + grandchild
        self.assertEqual(child2.count_nodes(), 1)  # just child2
        self.assertEqual(grandchild.count_nodes(), 1)  # just grandchild

    def test_count_nodes_deep_tree(self):
        """Test counting nodes in a deeper tree structure."""
        # Create a linear chain: root -> child -> grandchild -> great_grandchild
        root = TreeNode(session_id=0, prompt="Root", depth=0)
        child = TreeNode(session_id=1, prompt="Child", depth=1)
        grandchild = TreeNode(session_id=2, prompt="Grandchild", depth=2)
        great_grandchild = TreeNode(session_id=3, prompt="Great-grandchild", depth=3)

        root.add_child(child)
        child.add_child(grandchild)
        grandchild.add_child(great_grandchild)

        self.assertEqual(root.count_nodes(), 4)
        self.assertEqual(child.count_nodes(), 3)
        self.assertEqual(grandchild.count_nodes(), 2)
        self.assertEqual(great_grandchild.count_nodes(), 1)

    def test_traverse_preorder_single_node(self):
        """Test pre-order traversal of a single node."""
        node = TreeNode(session_id=0, prompt="Single", depth=0)

        traversal = node.traverse_preorder()

        self.assertEqual(len(traversal), 1)
        self.assertEqual(traversal[0], node)

    def test_traverse_preorder_with_children(self):
        """Test pre-order traversal with multiple children."""
        root = TreeNode(session_id=0, prompt="Root", depth=0)
        child1 = TreeNode(session_id=1, prompt="Child 1", depth=1)
        child2 = TreeNode(session_id=2, prompt="Child 2", depth=1)

        root.add_child(child1)
        root.add_child(child2)

        traversal = root.traverse_preorder()

        # Should be: root, child1, child2
        self.assertEqual(len(traversal), 3)
        self.assertEqual(traversal[0], root)
        self.assertEqual(traversal[1], child1)
        self.assertEqual(traversal[2], child2)

    def test_traverse_preorder_nested_structure(self):
        """Test pre-order traversal with nested children."""
        root = TreeNode(session_id=0, prompt="Root", depth=0)
        child1 = TreeNode(session_id=1, prompt="Child 1", depth=1)
        child2 = TreeNode(session_id=2, prompt="Child 2", depth=1)
        grandchild1 = TreeNode(session_id=3, prompt="Grandchild 1", depth=2)
        grandchild2 = TreeNode(session_id=4, prompt="Grandchild 2", depth=2)

        root.add_child(child1)
        root.add_child(child2)
        child1.add_child(grandchild1)
        child1.add_child(grandchild2)

        traversal = root.traverse_preorder()

        # Should be: root, child1, grandchild1, grandchild2, child2
        expected_order = [root, child1, grandchild1, grandchild2, child2]
        self.assertEqual(len(traversal), 5)
        self.assertEqual(traversal, expected_order)

    def test_traverse_preorder_deep_tree(self):
        """Test pre-order traversal with a deeper, more complex tree."""
        # Create tree:
        #       0
        #    /     \
        #   1       2
        #  /|\      |
        # 3 4 5     6
        #   |       |
        #   7       8

        nodes = [
            TreeNode(session_id=i, prompt=f"Node {i}", depth=d)
            for i, d in [
                (0, 0),
                (1, 1),
                (2, 1),
                (3, 2),
                (4, 2),
                (5, 2),
                (6, 2),
                (7, 3),
                (8, 3),
            ]
        ]

        nodes[0].add_child(nodes[1])  # 0 -> 1
        nodes[0].add_child(nodes[2])  # 0 -> 2
        nodes[1].add_child(nodes[3])  # 1 -> 3
        nodes[1].add_child(nodes[4])  # 1 -> 4
        nodes[1].add_child(nodes[5])  # 1 -> 5
        nodes[2].add_child(nodes[6])  # 2 -> 6
        nodes[4].add_child(nodes[7])  # 4 -> 7
        nodes[6].add_child(nodes[8])  # 6 -> 8

        traversal = nodes[0].traverse_preorder()

        # Pre-order: 0, 1, 3, 4, 7, 5, 2, 6, 8
        expected_session_ids = [0, 1, 3, 4, 7, 5, 2, 6, 8]
        actual_session_ids = [node.session_id for node in traversal]

        self.assertEqual(actual_session_ids, expected_session_ids)

    def test_session_xml_storage(self):
        """Test that session XML can be stored and retrieved."""
        node = TreeNode(session_id=0, prompt="Test", depth=0)

        # Initially None
        self.assertIsNone(node.session_xml)

        # Can be set
        test_xml = "<session><prompt>Test</prompt><submit>Result</submit></session>"
        node.session_xml = test_xml

        # Should be pretty-printed
        expected_xml = "<session>\n<prompt>Test</prompt>\n<submit>Result</submit>\n</session>"
        self.assertEqual(node.session_xml, expected_xml)

    def test_tree_consistency(self):
        """Test that tree structure remains consistent after operations."""
        root = TreeNode(session_id=0, prompt="Root", depth=0)
        child = TreeNode(session_id=1, prompt="Child", depth=1)

        # Add child
        root.add_child(child)

        # Verify counts and traversals are consistent
        self.assertEqual(root.count_nodes(), 2)
        self.assertEqual(len(root.traverse_preorder()), 2)
        self.assertEqual(root.traverse_preorder()[0], root)
        self.assertEqual(root.traverse_preorder()[1], child)

    def test_empty_children_list(self):
        """Test behavior with empty children list."""
        node = TreeNode(session_id=0, prompt="Test", depth=0)

        # Should handle empty children gracefully
        self.assertEqual(node.count_nodes(), 1)
        self.assertEqual(len(node.traverse_preorder()), 1)
        self.assertEqual(node.traverse_preorder()[0], node)


if __name__ == "__main__":
    unittest.main()
