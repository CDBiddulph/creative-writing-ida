"""Handles incremental processing of sessions with recursive tree building."""

import logging
from .tree_node import TreeNode
from .session import Session, ResponseEvent
from .placeholder_replacer import PlaceholderReplacer


class SessionProcessor:
    """Handles incremental processing of sessions with recursive tree building."""

    def __init__(
        self, session_generator, max_depth: int, max_retries: int = 3
    ):
        """
        Initialize SessionProcessor with dependencies and constraints.

        Args:
            session_generator: SessionGenerator instance for generating content
            max_depth: Maximum allowed depth for tree (used for leaf/parent decisions)
            max_retries: Maximum number of retry attempts before returning "FAILED"
        """
        self.session_generator = session_generator
        self.max_depth = max_depth
        self.max_retries = max_retries
        self.next_session_id = 0
        self.placeholder_replacer = PlaceholderReplacer()

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

    def _process_new_node(self, prompt: str, depth: int, parent_session: Session = None) -> TreeNode:
        """
        Process a single node recursively.

        Args:
            prompt: The prompt for this node
            depth: Current depth in the tree
            parent_session: Parent session for placeholder replacement (optional)

        Returns:
            TreeNode: Processed node with all children
        """
        session_id = self.next_session_id
        self.next_session_id += 1

        # Replace placeholders in prompt if parent session is provided
        if parent_session:
            prompt = self.placeholder_replacer.process_text(prompt, parent_session)

        node = TreeNode(session_id=session_id, prompt=prompt, depth=depth)

        # Determine if this should be a leaf node
        is_leaf = depth >= self.max_depth

        if is_leaf:
            # Generate leaf content
            session = self.session_generator.generate_leaf(prompt, node.session_id, self.max_retries)
            node.session = session
            return node

        # Generate initial parent content
        session = self.session_generator.generate_parent(prompt, node.session_id, self.max_retries)
        return self._continue_parent_node(node, session=session)

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

            new_child_node = self._process_new_node(last_ask_text, node.depth + 1, parent_session=session)
            node.children.append(new_child_node)

            # Get response from child and add to session
            child_response = self._get_submit_text(new_child_node)
            session.add_event(ResponseEvent(text=child_response))

            # Call continue_parent to get the next part of the session
            session = self.session_generator.continue_parent(session, self.max_retries)


    def _get_submit_text(self, node: TreeNode) -> str:
        """Get the submission text from a node with placeholders resolved."""
        submit_text = node.session.get_submit_text()
        # Resolve any placeholders in the submit text using the child's session context
        return self.placeholder_replacer.process_text(submit_text, node.session)
