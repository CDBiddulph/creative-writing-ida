"""Tests for XmlFormatter class."""

import unittest
from src.xml_formatter import XmlFormatter
from src.tree_node import TreeNode


class TestXmlFormatter(unittest.TestCase):
    """Test the XmlFormatter class."""

    def setUp(self):
        """Set up test fixtures."""
        self.formatter = XmlFormatter()

    def test_format_single_node_tree(self):
        """Test formatting a tree with a single node."""
        root = TreeNode(session_id=0, prompt="Simple task", depth=0)
        root.session_xml = "<session><prompt>Simple task</prompt><submit>Simple result</submit></session>"

        result = self.formatter.format_tree_xml(root)

        # Should be valid XML
        self.assertIn('<?xml version="1.0" encoding="UTF-8"?>', result)
        self.assertIn("<sessions>", result)
        self.assertIn("</sessions>", result)
        self.assertIn("<id>0</id>", result)
        self.assertIn("Simple task", result)
        self.assertIn("Simple result", result)

    def test_format_tree_with_children(self):
        """Test formatting a tree with parent and child nodes."""
        # Create tree structure
        root = TreeNode(session_id=0, prompt="Write a story", depth=0)
        child = TreeNode(session_id=1, prompt="What genre?", depth=1)

        root.session_xml = """<session>
            <prompt>Write a story</prompt>
            <notes>Need to decide on genre</notes>
            <ask>What genre?</ask>
            <response>Science fiction</response>
            <submit>A science fiction story...</submit>
        </session>"""

        child.session_xml = """<session>
            <prompt>What genre?</prompt>
            <submit>Science fiction</submit>
        </session>"""

        root.add_child(child)

        result = self.formatter.format_tree_xml(root)

        # Should contain both sessions
        self.assertIn("<id>0</id>", result)
        self.assertIn("<id>1</id>", result)
        self.assertIn("Write a story", result)
        self.assertIn("What genre?", result)

    def test_format_tree_preorder_traversal(self):
        """Test that sessions appear in pre-order traversal order."""
        # Create tree: root(0) -> child1(1) -> grandchild(3), child2(2)
        root = TreeNode(session_id=0, prompt="Root", depth=0)
        child1 = TreeNode(session_id=1, prompt="Child 1", depth=1)
        child2 = TreeNode(session_id=2, prompt="Child 2", depth=1)
        grandchild = TreeNode(session_id=3, prompt="Grandchild", depth=2)

        root.session_xml = (
            "<session><prompt>Root</prompt><submit>Root result</submit></session>"
        )
        child1.session_xml = (
            "<session><prompt>Child 1</prompt><submit>Child 1 result</submit></session>"
        )
        child2.session_xml = (
            "<session><prompt>Child 2</prompt><submit>Child 2 result</submit></session>"
        )
        grandchild.session_xml = "<session><prompt>Grandchild</prompt><submit>Grandchild result</submit></session>"

        root.add_child(child1)
        root.add_child(child2)
        child1.add_child(grandchild)

        result = self.formatter.format_tree_xml(root)

        # Find positions of session IDs in the output
        id0_pos = result.find("<id>0</id>")
        id1_pos = result.find("<id>1</id>")
        id2_pos = result.find("<id>2</id>")
        id3_pos = result.find("<id>3</id>")

        # Pre-order should be: 0, 1, 3, 2
        self.assertLess(id0_pos, id1_pos)
        self.assertLess(id1_pos, id3_pos)
        self.assertLess(id3_pos, id2_pos)

    def test_format_tree_response_ids(self):
        """Test that response-id elements are correctly inserted."""
        root = TreeNode(session_id=0, prompt="Parent task", depth=0)
        child = TreeNode(session_id=1, prompt="Child task", depth=1)

        root.session_xml = """<session>
            <prompt>Parent task</prompt>
            <ask>Child task</ask>
            <response>Child response</response>
            <submit>Final result</submit>
        </session>"""

        child.session_xml = """<session>
            <prompt>Child task</prompt>
            <submit>Child response</submit>
        </session>"""

        root.add_child(child)

        result = self.formatter.format_tree_xml(root)

        # Should have response-id before response
        self.assertIn("<response-id>1</response-id>", result)
        # Response-id should come before the actual response
        response_id_pos = result.find("<response-id>1</response-id>")
        response_pos = result.find("<response>Child response</response>")
        self.assertLess(response_id_pos, response_pos)

    def test_format_tree_multiple_responses(self):
        """Test formatting with multiple asks and responses."""
        root = TreeNode(session_id=0, prompt="Complex task", depth=0)
        child1 = TreeNode(session_id=1, prompt="Subtask 1", depth=1)
        child2 = TreeNode(session_id=2, prompt="Subtask 2", depth=1)

        root.session_xml = """<session>
            <prompt>Complex task</prompt>
            <ask>Subtask 1</ask>
            <response>Response 1</response>
            <ask>Subtask 2</ask>
            <response>Response 2</response>
            <submit>Combined result</submit>
        </session>"""

        child1.session_xml = """<session>
            <prompt>Subtask 1</prompt>
            <submit>Response 1</submit>
        </session>"""

        child2.session_xml = """<session>
            <prompt>Subtask 2</prompt>
            <submit>Response 2</submit>
        </session>"""

        root.add_child(child1)
        root.add_child(child2)

        result = self.formatter.format_tree_xml(root)

        # Should have both response IDs
        self.assertIn("<response-id>1</response-id>", result)
        self.assertIn("<response-id>2</response-id>", result)

    def test_format_tree_pretty_printing(self):
        """Test that output is properly formatted and indented."""
        root = TreeNode(session_id=0, prompt="Test", depth=0)
        root.session_xml = (
            "<session><prompt>Test</prompt><submit>Result</submit></session>"
        )

        result = self.formatter.format_tree_xml(root)

        # Should have proper indentation
        lines = result.split("\n")
        self.assertTrue(
            any("  <session>" in line for line in lines)
        )  # Indented session
        self.assertTrue(
            any("    <id>0</id>" in line for line in lines)
        )  # Deeper indentation

    def test_format_tree_xml_header(self):
        """Test that XML has proper header and encoding."""
        root = TreeNode(session_id=0, prompt="Test", depth=0)
        root.session_xml = (
            "<session><prompt>Test</prompt><submit>Result</submit></session>"
        )

        result = self.formatter.format_tree_xml(root)

        self.assertTrue(result.startswith('<?xml version="1.0" encoding="UTF-8"?>'))

    def test_format_tree_with_special_characters(self):
        """Test formatting handles special XML characters properly."""
        root = TreeNode(
            session_id=0, prompt='Test with <special> & "characters"', depth=0
        )
        root.session_xml = """<session>
            <prompt>Test with &lt;special&gt; &amp; "characters"</prompt>
            <submit>Result with &lt;tags&gt;</submit>
        </session>"""

        result = self.formatter.format_tree_xml(root)

        # Should be valid XML (no unescaped special characters breaking structure)
        self.assertIn("<sessions>", result)
        self.assertIn("</sessions>", result)
        self.assertIn("&lt;special&gt;", result)

    def test_format_tree_empty_content(self):
        """Test formatting handles empty or minimal content."""
        root = TreeNode(session_id=0, prompt="", depth=0)
        root.session_xml = "<session><prompt></prompt><submit></submit></session>"

        result = self.formatter.format_tree_xml(root)

        # Should still produce valid XML structure
        self.assertIn('<?xml version="1.0" encoding="UTF-8"?>', result)
        self.assertIn("<sessions>", result)
        self.assertIn("<id>0</id>", result)

    def test_format_tree_failed_session(self):
        """Test formatting handles FAILED session content."""
        root = TreeNode(session_id=0, prompt="Failed task", depth=0)
        root.session_xml = "FAILED"

        result = self.formatter.format_tree_xml(root)

        # Should still create valid XML structure, possibly with FAILED content
        self.assertIn('<?xml version="1.0" encoding="UTF-8"?>', result)
        self.assertIn("<sessions>", result)
        self.assertIn("<id>0</id>", result)
        self.assertIn("FAILED", result)

    def test_format_tree_large_tree(self):
        """Test formatting performance with a larger tree structure."""
        # Create a tree with multiple levels and many nodes
        root = TreeNode(session_id=0, prompt="Root", depth=0)
        root.session_xml = (
            "<session><prompt>Root</prompt><submit>Root result</submit></session>"
        )

        # Add 10 children, each with 2 grandchildren
        for i in range(10):
            child = TreeNode(session_id=i + 1, prompt=f"Child {i}", depth=1)
            child.session_xml = f"<session><prompt>Child {i}</prompt><submit>Child {i} result</submit></session>"
            root.add_child(child)

            for j in range(2):
                grandchild = TreeNode(
                    session_id=10 + (i * 2) + j + 1,
                    prompt=f"Grandchild {i}-{j}",
                    depth=2,
                )
                grandchild.session_xml = f"<session><prompt>Grandchild {i}-{j}</prompt><submit>Grandchild result</submit></session>"
                child.add_child(grandchild)

        result = self.formatter.format_tree_xml(root)

        # Should contain all 31 nodes (1 root + 10 children + 20 grandchildren)
        session_count = result.count("<session>")
        self.assertEqual(session_count, 31)


if __name__ == "__main__":
    unittest.main()
