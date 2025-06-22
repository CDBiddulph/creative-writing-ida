"""Handles XML manipulation and formatting for final output."""

from .tree_builder import TreeNode


class XmlFormatter:
    """Handles XML manipulation and formatting for final output."""
    
    def format_tree_xml(self, root_node: TreeNode) -> str:
        """
        Format complete tree as pretty-printed XML string ready for file output.
        
        Args:
            root_node: Root TreeNode containing the complete tree
            
        Returns:
            str: Complete XML document with <sessions> root and all session elements
            
        Traverses tree in pre-order, adds session IDs and response IDs, and formats 
        as pretty-printed XML with proper <?xml version="1.0" encoding="UTF-8"?> header.
        """
        pass