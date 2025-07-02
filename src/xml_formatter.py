"""Handles XML manipulation and formatting for final output."""

import io
import xml.etree.ElementTree as ET
from .tree_node import TreeNode
from .placeholder_replacer import PlaceholderReplacer


class XmlFormatter:
    """Handles XML manipulation and formatting for final output."""

    def __init__(self):
        """Initialize XmlFormatter."""
        self.placeholder_replacer = PlaceholderReplacer()

    def _add_final_response(self, root_node: TreeNode, sessions: ET.Element):
        """Add final-response tag with resolved placeholders if root has a submit."""
        if (
            root_node.session
            and root_node.session.is_complete()
            and not root_node.session.is_failed
        ):
            try:
                submit_text = root_node.session.get_submit_text()
                resolved_text = self.placeholder_replacer.process_text(
                    submit_text, root_node.session
                )
                final_response_elem = ET.SubElement(sessions, "final-response")
                final_response_elem.text = resolved_text
            except ValueError:
                # No submit text found, skip final-response
                pass

    def format_tree_xml(self, root_node: TreeNode) -> str:
        """
        Format complete tree as pretty-printed XML string ready for file output.

        Traverses tree in pre-order, adds session IDs and response IDs, and formats
        as pretty-printed XML with proper XML header.

        Args:
            root_node: Root TreeNode containing the complete tree

        Returns:
            str: Complete XML document with <sessions> root and all session elements
        """
        # Create root sessions element
        sessions = ET.Element("sessions")

        # Add final-response tag with resolved placeholders if root has a submit
        self._add_final_response(root_node, sessions)

        # Get all nodes in pre-order traversal
        all_nodes = root_node.traverse_preorder()

        # Process each node
        for node in all_nodes:
            # Handle FAILED sessions
            if node.session_xml == "FAILED":
                session_elem = ET.SubElement(sessions, "session")
                ET.SubElement(session_elem, "id").text = str(node.session_id)
                ET.SubElement(session_elem, "prompt").text = node.prompt
                ET.SubElement(session_elem, "submit").text = "FAILED"
            else:
                # Parse the session XML
                try:
                    session_root = ET.fromstring(node.session_xml)
                except ET.ParseError:
                    # If parsing fails, create a basic session with FAILED content
                    session_elem = ET.SubElement(sessions, "session")
                    ET.SubElement(session_elem, "id").text = str(node.session_id)
                    ET.SubElement(session_elem, "prompt").text = node.prompt
                    ET.SubElement(session_elem, "submit").text = "FAILED"
                    continue

                # Add ID as first element
                id_elem = ET.Element("id")
                id_elem.text = str(node.session_id)
                session_root.insert(0, id_elem)

                # Add response IDs before response elements
                self._add_response_ids(session_root, node)

                # Add to sessions
                sessions.append(session_root)

        # Create XML string with header and pretty formatting
        self._indent(sessions)

        # Convert to string with custom XML declaration
        output = io.StringIO()

        # Write the XML content without declaration
        tree = ET.ElementTree(sessions)
        tree.write(output, encoding="unicode", xml_declaration=True)

        return output.getvalue()

    def _add_response_ids(self, session_element: ET.Element, node: TreeNode):
        """Add response-id elements before each response element."""
        # Create mapping of response index to child session ID
        response_elements = [elem for elem in session_element if elem.tag == "response"]

        if len(response_elements) == len(node.children):
            # Add response-id before each response
            for i, response_elem in enumerate(response_elements):
                response_id_elem = ET.Element("response-id")
                response_id_elem.text = str(node.children[i].session_id)

                # Find the index of the response element and insert response-id before it
                response_index = list(session_element).index(response_elem)
                session_element.insert(response_index, response_id_elem)

    def _indent(self, elem: ET.Element, level: int = 0):
        """Add whitespace to ElementTree for pretty printing."""
        indent = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent
            for child in elem:
                self._indent(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent
