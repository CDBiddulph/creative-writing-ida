"""Tree building logic for hierarchical session structure."""

from typing import List
from models import Session, TreeNode, SessionIDManager


class TreeBuilder:
    """Builds hierarchical tree structures for sessions."""
    
    def __init__(self):
        self.id_manager = SessionIDManager()
    
    def build_tree(self, root_prompt: str, tree_depth: int) -> TreeNode:
        """
        Build a tree structure with the given depth.
        
        Args:
            root_prompt: The initial prompt for the root session
            tree_depth: Number of levels in the tree (1 = just root, 2 = root + children, etc.)
            
        Returns:
            Root TreeNode with children attached
        """
        # Create root session
        root_session = Session(
            id=self.id_manager.get_next_id(),
            prompt=root_prompt
        )
        
        root_node = TreeNode(
            session=root_session,
            depth=0,
            is_leaf=(tree_depth == 1)
        )
        
        # Build children recursively if depth > 1
        if tree_depth > 1:
            self._build_children(root_node, tree_depth - 1)
        
        return root_node
    
    def _build_children(self, parent_node: TreeNode, remaining_depth: int) -> None:
        """
        Recursively build children for a given node.
        
        Args:
            parent_node: The parent node to add children to
            remaining_depth: How many more levels to build
        """
        # For now, create a single child per parent
        # This can be extended to create multiple children based on asks
        
        # Create a placeholder child session
        # The actual prompt will be filled in when the parent generates asks
        child_session = Session(
            id=self.id_manager.get_next_id(),
            prompt="",  # Will be set from parent's ask
            responding_to_id=parent_node.session.id
        )
        
        child_node = TreeNode(
            session=child_session,
            depth=parent_node.depth + 1,
            is_leaf=(remaining_depth == 1)
        )
        
        parent_node.add_child(child_node)
        
        # Recursively build children if we have more depth
        if remaining_depth > 1:
            self._build_children(child_node, remaining_depth - 1)
    
    def get_all_sessions_preorder(self, root_node: TreeNode) -> List[Session]:
        """Get all sessions from the tree in pre-order traversal."""
        return root_node.get_all_sessions_preorder()
    
    def get_leaf_nodes(self, root_node: TreeNode) -> List[TreeNode]:
        """Get all leaf nodes from the tree."""
        if root_node.is_leaf:
            return [root_node]
        
        leaf_nodes = []
        for child in root_node.children:
            leaf_nodes.extend(self.get_leaf_nodes(child))
        
        return leaf_nodes
    
    def get_nodes_by_depth(self, root_node: TreeNode, target_depth: int) -> List[TreeNode]:
        """Get all nodes at a specific depth level."""
        if root_node.depth == target_depth:
            return [root_node]
        
        nodes = []
        for child in root_node.children:
            nodes.extend(self.get_nodes_by_depth(child, target_depth))
        
        return nodes
    
    def reset_id_counter(self) -> None:
        """Reset the session ID counter."""
        self.id_manager.reset()