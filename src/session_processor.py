"""Handles incremental processing of sessions with recursive tree building."""

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
        return self._process_node(prompt, 0)

    def _process_node(self, prompt: str, depth: int) -> TreeNode:
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
        
        if is_leaf:
            # Generate leaf content
            session_xml = self._generate_with_retry(
                lambda: self.xml_generator.generate_leaf(prompt), is_leaf=True
            )
            node.session_xml = session_xml
        else:
            # Generate parent content
            session_xml = self._generate_with_retry(
                lambda: self.xml_generator.generate_parent(prompt), is_leaf=False
            )
            
            if session_xml == "FAILED":
                node.session_xml = "FAILED"
                return node
            
            # Process this parent node incrementally
            node = self._process_parent_node(node, session_xml)
        
        return node

    def _process_parent_node(self, node: TreeNode, initial_xml: str) -> TreeNode:
        """
        Process a parent node by handling asks and responses incrementally.
        
        Args:
            node: The TreeNode being processed
            initial_xml: Initial XML from generate_parent
            
        Returns:
            TreeNode: Updated node with children and final XML
        """
        current_xml = initial_xml
        
        while True:
            # Check if current XML ends with an ask (partial)
            if self._xml_ends_with_ask(current_xml):
                # Extract the ask text and create child
                ask_text = self._extract_last_ask_text(current_xml)
                child_node = self._process_node(ask_text, node.depth + 1)
                node.add_child(child_node)
                
                # Get response text (either child's content or "FAILED")
                response_text = self._extract_response_from_child(child_node)
                
                # continue_parent handles adding the response internally
                continued_xml = self._generate_with_retry(
                    lambda: self.xml_generator.continue_parent(current_xml), 
                    is_leaf=False
                )
                
                if continued_xml == "FAILED":
                    node.session_xml = "FAILED"
                    return node
                
                current_xml = continued_xml
            else:
                # XML is complete (ends with submit)
                node.session_xml = current_xml
                break
                
        return node

    def _generate_with_retry(self, generate_func, is_leaf: bool) -> str:
        """
        Generate content with retry logic for validation failures.
        
        Args:
            generate_func: Function that generates XML content
            is_leaf: Whether this is for a leaf node
            
        Returns:
            str: Generated XML or "FAILED" if max retries exceeded
        """
        for attempt in range(self.max_retries + 1):
            try:
                xml_content = generate_func()
                
                # Validate the XML
                if is_leaf:
                    # For leaf nodes, should be complete
                    if self.xml_validator.validate_session_xml(xml_content, is_leaf=True, is_partial=False):
                        return xml_content
                else:
                    # For parent nodes, check if partial or complete
                    try:
                        is_partial = self.xml_validator.get_is_xml_partial_or_fail(xml_content, is_leaf=False)
                        if self.xml_validator.validate_session_xml(xml_content, is_leaf=False, is_partial=is_partial):
                            return xml_content
                    except ValueError:
                        # Invalid XML, will retry
                        pass
                        
            except Exception:
                # Generation failed, will retry
                pass
        
        return "FAILED"

    def _xml_ends_with_ask(self, xml_content: str) -> bool:
        """Check if XML ends with an ask tag (is partial)."""
        try:
            # Try parsing as-is first
            try:
                root = ET.fromstring(xml_content)
                # If it parses as-is, check if last child is ask
                children = list(root)
                return children and children[-1].tag == "ask"
            except ET.ParseError:
                # Try adding closing session tag
                xml_to_parse = xml_content.strip()
                if not xml_to_parse.endswith("</session>"):
                    xml_to_parse += "\n</session>"
                root = ET.fromstring(xml_to_parse)
                children = list(root)
                return children and children[-1].tag == "ask"
        except ET.ParseError:
            return False

    def _extract_last_ask_text(self, xml_content: str) -> str:
        """Extract the text content of the last ask tag."""
        try:
            # Try parsing as-is first
            try:
                root = ET.fromstring(xml_content)
            except ET.ParseError:
                # Try adding closing session tag
                xml_to_parse = xml_content.strip()
                if not xml_to_parse.endswith("</session>"):
                    xml_to_parse += "\n</session>"
                root = ET.fromstring(xml_to_parse)
                
            children = list(root)
            if children and children[-1].tag == "ask":
                return children[-1].text or ""
            return ""
        except ET.ParseError:
            return ""

    def _extract_response_from_child(self, child_node: TreeNode) -> str:
        """Extract response text from a child node's session_xml."""
        if child_node.session_xml == "FAILED":
            return "FAILED"
        
        try:
            root = ET.fromstring(child_node.session_xml)
            children = list(root)
            for child in children:
                if child.tag == "submit":
                    return child.text or ""
            return ""
        except ET.ParseError:
            return "FAILED"

    def _add_response_to_xml(self, xml_content: str, response_text: str) -> str:
        """Add a response tag to the XML after the last ask."""
        # Simple string-based approach to preserve exact formatting
        if xml_content.endswith("</session>"):
            # Complete XML - insert before closing tag
            insertion_point = xml_content.rfind("</session>")
            response_tag = f"\n<response>{response_text}</response>"
            return xml_content[:insertion_point] + response_tag + xml_content[insertion_point:]
        else:
            # Partial XML - just append
            return xml_content + f"\n<response>{response_text}</response>"
