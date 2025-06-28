"""Handles incremental processing of sessions with recursive tree building."""

import logging
from .tree_node import TreeNode
from .session import Session, ResponseEvent


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
            TreeNode: Complete node with session populated and all children built recursively.
            The root node has a session_id of 0 and a depth of 0.

        Generates content incrementally, stopping at </ask> tags to recursively create
        child sessions. Child session IDs are generated in pre-order (0, 1, 2, ...).
        If any child fails after retrying for max_retries, that child's `session` is set to
        "FAILED" and the session continues as normal.
        The final session may contain <ask> and <response> tags, and it must end with a <submit>
        tag. The entire session will be wrapped in a <session> tag.
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
                session = self._generate_session_with_retry(
                    lambda: self.xml_generator.generate_leaf(prompt),
                    node.session_id,
                    is_leaf=True,
                )
                node.session = session
                return node

            # Generate initial parent content
            session = self._generate_session_with_retry(
                lambda: self.xml_generator.generate_parent(prompt),
                node.session_id,
                is_leaf=False,
            )
            return self._continue_parent_node(node, session=session)
        except Exception as e:
            logging.error(f"Error processing node {node.session_id}: {e}")
            node.session = Session(session_id=node.session_id, is_failed=True)
            return node

    def _continue_parent_node(self, node: TreeNode, session: Session) -> TreeNode:
        """
        Continue a partially generated parent node by handling asks and responses incrementally.

        Uses continue_parent to generate the next part of the session until it is complete.

        Args:
            node: The TreeNode being processed
            session: Initial Session from generate_parent or continue_parent

        Returns:
            TreeNode: Updated node with children and final session
        """
        while True:
            # Check if current session is complete
            if session.is_complete():
                node.session = session
                return node

            # Extract the last ask text and create child
            try:
                last_ask_text = session.get_ask_text()
            except ValueError as e:
                raise RuntimeError(
                    f"Expected ask event but found none in session {session.session_id}: {e}"
                )

            new_child_node = self._process_new_node(last_ask_text, node.depth + 1)
            node.children.append(new_child_node)

            # Get response from child and add to session
            child_response = self._get_submit_text(new_child_node)
            session.add_event(ResponseEvent(text=child_response))

            # Call continue_parent to get the next part of the session
            session = self._generate_session_with_retry(
                lambda: self.xml_generator.continue_parent(
                    session.to_xml(include_closing_tag=False)
                ),
                node.session_id,
                is_leaf=False,
            )

    def _generate_session_with_retry(
        self, generate_func, session_id: int, is_leaf: bool
    ) -> Session:
        """
        Generate Session with retry logic for validation failures.

        Args:
            generate_func: Function that generates XML content
            session_id: ID for the session
            is_leaf: Whether this is for a leaf node

        Returns:
            Session: Generated Session object.

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
                # Convert to Session object
                return Session.from_xml(xml_content, session_id)
            except Exception as e:
                last_exception = e
                logging.warning(
                    f"Attempt {attempt + 1} failed. Invalid XML generated. Error: {e}"
                )

        logging.error(f"Failed to generate XML after {self.max_retries + 1} attempts")
        if last_exception is None:
            raise RuntimeError(f"Error message not set. This should never happen.")
        raise last_exception

    def _get_submit_text(self, node: TreeNode) -> str:
        """Get the submission text from a node."""
        return node.session.get_submit_text()
