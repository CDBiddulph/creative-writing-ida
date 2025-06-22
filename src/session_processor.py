"""Handles incremental processing of sessions with recursive tree building."""

import re
from .tree_builder import TreeNode


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
        pass
