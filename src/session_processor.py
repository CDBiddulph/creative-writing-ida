"""Handles incremental processing of sessions with recursive tree building."""

import logging
import xml.etree.ElementTree as ET
from .tree_node import TreeNode


class SessionProcessor:
    """Handles incremental processing of sessions with recursive tree building."""

    def __init__(
        self, xml_generator, xml_validator, max_depth: int, max_retries: int = 3
    ):
        """
        Initialize SessionProcessor with dependencies and constraints.

        Args:
            xml_generator: SessionXmlGenerator instance for generating content
            xml_validator: XmlValidator instance for validating generated XML
            max_depth: Maximum allowed depth for tree (used for leaf/parent decisions)
            max_retries: Maximum number of retry attempts before returning "FAILED"
        """
        self.xml_generator = xml_generator
        self.xml_validator = xml_validator
        self.max_depth = max_depth
        self.max_retries = max_retries
        self.next_session_id = 0

    def process_session(self, prompt: str) -> TreeNode:
        """
        Process a root-level session recursively, building complete subtree with all children.

        Args:
            prompt: The root prompt text for this session.

        Returns:
            TreeNode: Complete node with session_xml populated and all children built recursively.
            The root node has a session_id of 0 and a depth of 0.

        Generates content incrementally, stopping at </ask> tags to recursively create
        child sessions. Child session IDs are generated in pre-order (0, 1, 2, ...).
        If any child fails after retrying for max_retries, that child's `session_xml` is set to
        "FAILED" and the session continues as normal.
        The final session_xml may contain <ask> and <response> tags, and it must end with a <submit>
        tag. The entire session_xml will be wrapped in a <session> tag.
        """
        self.next_session_id = 0
        return self._process_new_node(prompt, 0)

    def _process_new_node(self, prompt: str, depth: int) -> TreeNode:
        """
        Process a single node recursively.

        Args:
            prompt: The prompt for this node
            depth: Current depth in the tree

        Returns:
            TreeNode: Processed node with all children
        """
        session_id = self.next_session_id
        self.next_session_id += 1

        node = TreeNode(session_id=session_id, prompt=prompt, depth=depth)

        # Determine if this should be a leaf node
        is_leaf = depth >= self.max_depth

        try:
            if is_leaf:
                # Generate leaf content
                session_xml = self._generate_with_retry(
                    lambda: self.xml_generator.generate_leaf(prompt), is_leaf=True
                )
                node.session_xml = session_xml
                return node

            # Generate initial parent content
            session_xml = self._generate_with_retry(
                lambda: self.xml_generator.generate_parent(prompt), is_leaf=False
            )
            return self._continue_parent_node(node, xml=session_xml)
        except Exception as e:
            logging.error(f"Error processing node {node.session_id}: {e}")
            node.session_xml = "FAILED"
            return node

    def _continue_parent_node(self, node: TreeNode, xml: str) -> TreeNode:
        """
        Continue a partially generated parent node by handling asks and responses incrementally.

        Uses continue_parent to generate the next part of the XML until it is complete.

        Args:
            node: The TreeNode being processed
            xml: Initial XML from generate_parent or continue_parent

        Returns:
            TreeNode: Updated node with children and final XML
        """
        while True:
            # Check if current XML is complete
            is_partial = self.xml_validator.get_is_xml_partial_or_fail(
                xml, is_leaf=False
            )

            # If complete, return the node now
            if not is_partial:
                node.session_xml = xml
                return node

            # Extract the last ask text and create child
            last_ask_text = self._extract_last_ask_text(xml)
            new_child_node = self._process_new_node(last_ask_text, node.depth + 1)
            node.children.append(new_child_node)

            # Get response from child and add to XML
            child_response = self._get_submit_text(new_child_node)
            xml_with_response = self._add_response_to_xml(xml, child_response)

            # Call continue_parent to get the next part of the XML
            xml = self._generate_with_retry(
                lambda: self.xml_generator.continue_parent(xml_with_response),
                is_leaf=False,
            )

    def _generate_with_retry(self, generate_func, is_leaf: bool) -> str:
        """
        Generate content with retry logic for validation failures.

        Args:
            generate_func: Function that generates XML content
            is_leaf: Whether this is for a leaf node

        Returns:
            str: Generated XML.

        Raises:
            RuntimeError: If the XML is invalid after max retries.
        """
        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                xml_content = generate_func()
                # Validate the XML
                _ = self.xml_validator.get_is_xml_partial_or_fail(
                    xml_content, is_leaf=is_leaf
                )
                return xml_content
            except Exception as e:
                last_exception = e
                logging.warning(
                    f"Attempt {attempt + 1} failed. Invalid XML generated. Error: {e}"
                )

        logging.error(f"Failed to generate XML after {self.max_retries + 1} attempts")
        if last_exception is None:
            raise RuntimeError(f"Error message not set. This should never happen.")
        raise last_exception

    def _extract_last_ask_text(self, xml_content: str) -> str:
        """Extract the text content of the last ask tag."""
        # Add closing session tag, since it currently ends with </ask>.
        xml_to_parse = xml_content + "\n</session>"
        root = ET.fromstring(xml_to_parse)

        children = list(root)
        assert (
            children
        ), f"No children found in {xml_to_parse}. This should never happen."
        assert (
            children[-1].tag == "ask"
        ), f"Last child is not an <ask>: {children[-1].tag}. This should never happen."

        result = children[-1].text
        assert result, f"No text found in {xml_to_parse}. This should never happen."
        return result

    def _get_submit_text(self, node: TreeNode) -> str:
        """Get the submission text from a node."""
        return node.session.get_submit_text()

    def _add_response_to_xml(self, xml_content: str, response_text: str) -> str:
        """Add a response tag to the XML after the last ask."""
        # Simple string-based approach to preserve exact formatting
        if xml_content.endswith("</session>"):
            # Complete XML - insert before closing tag
            insertion_point = xml_content.rfind("</session>")
            response_tag = f"\n<response>{response_text}</response>"
            return (
                xml_content[:insertion_point]
                + response_tag
                + xml_content[insertion_point:]
            )
        else:
            # Partial XML - just append
            return xml_content + f"\n<response>{response_text}</response>"
