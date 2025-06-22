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
        self.session_id = session_id
        self.prompt = prompt
        self.depth = depth
        self.children: List['TreeNode'] = []
        self.session_xml: Optional[str] = None
    
    def add_child(self, child_node: 'TreeNode'):
        """
        Add a child node to this node.
        
        Args:
            child_node: TreeNode to add as a child
            
        Maintains parent-child relationships for tree traversal.
        """
        self.children.append(child_node)
    
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
    
    def traverse_preorder(self) -> List['TreeNode']:
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