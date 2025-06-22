"""Handles XML manipulation and formatting for final output."""

import xml.etree.ElementTree as ET
from .tree_node import TreeNode


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
        # Create root sessions element
        sessions = ET.Element("sessions")

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
        import io

        output = io.StringIO()
        output.write('<?xml version="1.0" encoding="UTF-8"?>\n')

        # Write the XML content without declaration
        tree = ET.ElementTree(sessions)
        tree.write(output, encoding="unicode", xml_declaration=False)

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
