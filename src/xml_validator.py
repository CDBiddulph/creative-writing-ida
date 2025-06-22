"""Validates generated XML contains only allowed tags."""

import xml.etree.ElementTree as ET
import logging


class XmlValidator:
    """Validates generated XML contains only allowed tags."""

    LEAF_ALLOWED_TAGS = {"prompt", "submit"}
    PARENT_ALLOWED_TAGS = {"prompt", "submit", "notes", "ask", "response"}

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
        if not session_xml or not session_xml.strip():
            return False

        try:
            # Parse the XML
            root = ET.fromstring(session_xml)

            # Check that root is 'session'
            if root.tag != "session":
                logging.error("Root tag is not 'session': %s", session_xml)
                return False

            # Extract tags from direct children of session
            found_tags = self._extract_tags(root)

            # Determine allowed tags based on node type
            allowed_tags = (
                self.LEAF_ALLOWED_TAGS if is_leaf else self.PARENT_ALLOWED_TAGS
            )

            # Check if all found tags are allowed
            if not found_tags.issubset(allowed_tags):
                logging.error(
                    "Invalid tags: %s. Allowed tags: %s", found_tags, allowed_tags
                )
                return False

            # For leaf nodes, both prompt and submit are required
            if is_leaf:
                if "prompt" not in found_tags or "submit" not in found_tags:
                    logging.error("Leaf node missing prompt or submit: %s", session_xml)
                    return False
            else:
                # For parent nodes, at least prompt is required
                if "prompt" not in found_tags:
                    logging.error("Parent node missing prompt: %s", session_xml)
                    return False

            return True

        except ET.ParseError:
            logging.error("Invalid XML: %s", session_xml)
            return False

    def _extract_tags(self, root_element) -> set[str]:
        """Extract all XML tag names from direct children of root element."""
        return {child.tag for child in root_element}
