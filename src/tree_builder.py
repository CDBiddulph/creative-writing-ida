"""Tree node representation for session tree structure."""

from typing import List, Optional


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
        pass
    
    def add_child(self, child_node: 'TreeNode'):
        """
        Add a child node to this node.
        
        Args:
            child_node: TreeNode to add as a child
            
        Maintains parent-child relationships for tree traversal.
        """
        pass
    
    def count_nodes(self) -> int:
        """
        Count total number of nodes in this subtree (including self).
        
        Returns:
            int: Total node count for this node and all descendants
            
        Used for calculating session IDs of subsequent children and tree statistics.
        """
        pass
    
    def traverse_preorder(self) -> List['TreeNode']:
        """
        Return this node and all descendants in pre-order traversal.
        
        Returns:
            list[TreeNode]: Nodes in pre-order (self first, then children depth-first)
            
        Used for generating the final XML output where sessions appear in execution order.
        """
        pass