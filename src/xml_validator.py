"""Validates generated XML contains only allowed tags."""


class XmlValidator:
    """Validates generated XML contains only allowed tags."""
    
    def validate_session_xml(self, session_xml: str, is_leaf: bool) -> bool:
        """
        Validate that session XML contains only allowed tags for node type.
        
        Args:
            session_xml: XML string to validate
            is_leaf: True if this is a leaf node, False if parent node
            
        Returns:
            bool: True if XML is valid, False otherwise
            
        Leaf nodes allow: prompt, submit
        Parent nodes allow: prompt, submit, notes, ask, response
        """
        pass