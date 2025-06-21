"""Session execution logic for running API calls and managing tree traversal."""

import re
from typing import List
from models import TreeNode, Session
from session_xml_generator import get_session_xml_generator
from config import resolve_model_name


class SessionRunner:
    """Handles execution of sessions and tree traversal."""

    def __init__(
        self,
        model: str,
        max_tokens: int,
        temperature: float,
        parent_readme_path: str,
        leaf_readme_path: str,
        parent_examples_xml_path: str = None,
        leaf_examples_xml_path: str = None,
    ):
        self.session_generator = get_session_xml_generator(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            leaf_readme_path=leaf_readme_path,
            parent_readme_path=parent_readme_path,
            leaf_examples_xml_path=leaf_examples_xml_path,
            parent_examples_xml_path=parent_examples_xml_path,
        )

    def execute_tree(self, root_node: TreeNode) -> None:
        """
        Execute all sessions in the tree, processing from root to leaves.

        Args:
            root_node: The root of the tree to execute
        """
        self._execute_node(root_node)

    def _execute_node(self, node: TreeNode) -> None:
        """
        Execute a single node and its children.

        Args:
            node: The node to execute
        """
        if node.is_leaf:
            self._execute_leaf_session(node.session)
        else:
            self._execute_parent_session(node)

            # Execute children after parent is complete
            for child in node.children:
                self._execute_node(child)

    def _execute_parent_session(self, node: TreeNode) -> None:
        """
        Execute a parent session that should generate asks for children.

        Args:
            node: The parent node to execute
        """
        session_generator = get_session_xml_generator(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            leaf_examples_xml=self.leaf_examples_xml,
            parent_examples_xml=self.parent_examples_xml,
        )

        # Call API with parent configuration
        response_text = session_generator.generate_parent(
            prompt=node.session.prompt,
        )

        # Parse the response to extract asks and update children
        self._parse_parent_response(node, response_text)

    def _execute_leaf_session(self, session: Session) -> None:
        """
        Execute a leaf session that should generate a final submit.

        Args:
            session: The leaf session to execute
        """
        # Call API with leaf configuration
        response_text = self.session_generator.generate_leaf(prompt=session.prompt)

        # Set the final submit
        session.set_final_submit(response_text.strip())

    def _parse_parent_response(self, parent_node: TreeNode, response: str) -> None:
        """
        Parse a parent response to extract notes, asks, and set up children.

        Args:
            parent_node: The parent node whose response to parse
            response: The raw response from the API
        """
        session = parent_node.session

        # Split response into sections
        sections = self._split_response_sections(response)

        # Process each section
        current_child_idx = 0
        for section in sections:
            section_type, content = section

            if section_type == "notes":
                session.add_note(content.strip())
            elif section_type == "ask":
                # Create ask and assign to next child
                if current_child_idx < len(parent_node.children):
                    child_node = parent_node.children[current_child_idx]
                    child_node.session.prompt = content.strip()

                    # For now, we'll simulate the response by creating a placeholder
                    # In a real implementation, this would be the child's response
                    placeholder_response = f"[Response to: {content.strip()[:50]}...]"
                    session.add_ask_response(
                        ask=content.strip(),
                        response=placeholder_response,
                        response_session_id=child_node.session.id,
                    )

                    current_child_idx += 1
            elif section_type == "submit":
                session.set_final_submit(content.strip())

    def _split_response_sections(self, response: str) -> List[tuple[str, str]]:
        """
        Split response into sections based on XML-like tags or content patterns.

        Args:
            response: The raw response to parse

        Returns:
            List of (section_type, content) tuples in order of appearance
        """
        sections = []

        # Combined pattern to find all tags in order
        combined_pattern = r"<(notes|ask|submit)>(.*?)</\1>"

        # Find all matches in order
        matches = re.finditer(combined_pattern, response, re.DOTALL | re.IGNORECASE)

        for match in matches:
            tag_type = match.group(1).lower()
            content = match.group(2).strip()
            sections.append((tag_type, content))

        # If no XML tags found, try to infer structure
        if not sections:
            raise ValueError("No sections found in response")

        return sections
