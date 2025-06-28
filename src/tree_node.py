"""Tree node representation for session tree structure."""

from typing import List, Optional
from .xml_utils import xml_are_equivalent
from .session import Session, FAILED_STR


class TreeNode:
    """Represents a session in the tree with XML content and children."""

    def __init__(self, session_id: int, prompt: str, depth: int):
        """
        Initialize a tree node.

        Args:
            session_id: Unique integer ID for this session (0, 1, 2, ...)
            prompt: The prompt text for this session
            depth: Depth level in tree (root = 0)
        """
        self.session_id = session_id
        self.prompt = prompt
        self.depth = depth
        self.children: List["TreeNode"] = []
        self.session: Optional[Session] = None

    def add_child(self, child_node: "TreeNode"):
        """
        Add a child node to this node.

        Args:
            child_node: TreeNode to add as a child

        Maintains parent-child relationships for tree traversal.
        """
        self.children.append(child_node)

    @property
    def session_xml(self) -> Optional[str]:
        """Get the session XML, generated from Session object."""
        if self.session:
            return self.session.to_xml()
        return None

    @session_xml.setter
    def session_xml(self, value: Optional[str]) -> None:
        """Set the session from XML string or FAILED state."""
        if value == FAILED_STR:
            # Create a failed session
            self.session = Session(session_id=self.session_id, is_failed=True)
        elif value is not None:
            # Parse XML into Session object
            self.session = Session.from_xml(value, self.session_id)

    def count_nodes(self) -> int:
        """
        Count total number of nodes in this subtree (including self).

        Returns:
            int: Total node count for this node and all descendants

        Used for calculating session IDs of subsequent children and tree statistics.
        """
        count = 1  # Count self
        for child in self.children:
            count += child.count_nodes()
        return count

    def traverse_preorder(self) -> List["TreeNode"]:
        """
        Return this node and all descendants in pre-order traversal.

        Returns:
            list[TreeNode]: Nodes in pre-order (self first, then children depth-first)

        Used for generating the final XML output where sessions appear in execution order.
        """
        result = [self]
        for child in self.children:
            result.extend(child.traverse_preorder())
        return result

    def __eq__(self, other) -> bool:
        """
        Compare two TreeNode instances for equality.

        Args:
            other: Another TreeNode to compare against

        Returns:
            bool: True if all attributes and children are equal
        """
        if not isinstance(other, TreeNode):
            return False

        return (
            self.session_id == other.session_id
            and self.prompt == other.prompt
            and self.depth == other.depth
            and xml_are_equivalent(self.session_xml, other.session_xml)
            and self.children == other.children
        )

    def __repr__(self) -> str:
        """Return string representation for debugging."""
        return f"TreeNode(session_id={self.session_id}, prompt='{self.prompt}', depth={self.depth}, children_count={len(self.children)})"
