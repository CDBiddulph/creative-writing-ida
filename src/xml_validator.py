"""Validates generated XML contains only allowed tags."""

import xml.etree.ElementTree as ET
import logging


class XmlValidator:
    """Validates generated XML contains only allowed tags."""

    LEAF_ALLOWED_TAGS = {"prompt", "submit"}
    PARENT_ALLOWED_TAGS = {"prompt", "submit", "notes", "ask", "response"}

    def get_is_xml_partial_or_fail(self, session_xml: str, is_leaf: bool) -> bool:
        """
        If the XML is valid and partial, return True. If it is valid and complete, return False.
        If the XML is invalid, raise a ValueError.

        Args:
            session_xml: XML string to validate.
            is_leaf: True if we want to validate this as a leaf node, False if parent node. If
            `is_leaf` is True, the XML should never be partial, so it will either raise a
            ValueError or return False.

        Returns:
            bool: True if XML is partial, False if XML is complete or invalid
        """
        if not session_xml or not session_xml.strip():
            raise ValueError("Empty or whitespace-only XML")

        # For leaf nodes, check if it's a valid partial or complete format
        if is_leaf:
            # First, try to parse as-is to see if it's complete XML
            try:
                root = ET.fromstring(session_xml)
                is_complete_xml = True
            except ET.ParseError:
                # Try adding closing session tag for partial XML
                xml_to_parse = session_xml.strip()
                if not xml_to_parse.endswith("</session>"):
                    xml_to_parse += "\n</session>"
                try:
                    root = ET.fromstring(xml_to_parse)
                    is_complete_xml = False
                except ET.ParseError:
                    raise ValueError(f"Invalid XML: {session_xml}")

            # Check that root is 'session'
            if root.tag != "session":
                raise ValueError(f"Root tag is not 'session': {session_xml}")

            children = list(root)
            if not children:
                raise ValueError(f"Empty session: {session_xml}")

            tag_sequence = [child.tag for child in children]
            found_tags = set(tag_sequence)

            # Rule 1: <prompt> must be first
            if tag_sequence[0] != "prompt":
                raise ValueError(f"First tag must be 'prompt': {session_xml}")

            if is_complete_xml:
                # This is complete XML - validate as leaf
                # Check if all found tags are allowed for leaf
                if not found_tags.issubset(self.LEAF_ALLOWED_TAGS):
                    raise ValueError(f"Invalid tags for leaf: {found_tags}. Allowed tags: {self.LEAF_ALLOWED_TAGS}")

                # For complete leaf nodes, must end with submit
                if tag_sequence[-1] != "submit":
                    raise ValueError(f"Complete leaf XML must end with 'submit': {session_xml}")

                # For complete leaf nodes, both prompt and submit are required
                if "prompt" not in found_tags or "submit" not in found_tags:
                    raise ValueError(f"Leaf node missing prompt or submit: {session_xml}")

                return False  # Complete and valid
            else:
                # This is partial XML - for leaf nodes, this is valid and returns True
                # but only if it doesn't contain invalid leaf tags or violate basic rules
                return True  # Partial and valid

        # For parent nodes, determine if partial or complete
        try:
            # First try to parse as-is to see if it's already complete
            try:
                root = ET.fromstring(session_xml)
                is_complete_xml = True
            except ET.ParseError:
                # Try adding closing session tag
                xml_to_parse = session_xml.strip()
                if not xml_to_parse.endswith("</session>"):
                    xml_to_parse += "\n</session>"
                try:
                    root = ET.fromstring(xml_to_parse)
                    is_complete_xml = False
                except ET.ParseError:
                    raise ValueError(f"Invalid XML: {session_xml}")

            # Check that root is 'session'
            if root.tag != "session":
                raise ValueError(f"Root tag is not 'session': {session_xml}")

            children = list(root)
            if not children:
                raise ValueError(f"Empty session: {session_xml}")

            tag_sequence = [child.tag for child in children]
            found_tags = set(tag_sequence)

            # Check if all found tags are allowed
            if not found_tags.issubset(self.PARENT_ALLOWED_TAGS):
                raise ValueError(f"Invalid tags: {found_tags}. Allowed tags: {self.PARENT_ALLOWED_TAGS}")

            # Rule 1: <prompt> must be first
            if tag_sequence[0] != "prompt":
                raise ValueError(f"First tag must be 'prompt': {session_xml}")

            # Determine if this should be treated as partial or complete
            if is_complete_xml:
                # This is complete XML - check if it ends with submit
                if tag_sequence[-1] != "submit":
                    raise ValueError(f"Complete XML must end with 'submit': {session_xml}")

                # Validate ask/response pairing for complete XML
                if not self._validate_ask_response_pairing_or_fail(tag_sequence):
                    # Error already raised by helper method
                    pass

                return False  # Complete and valid
            else:
                # This is partial XML - must end with ask
                if tag_sequence[-1] != "ask":
                    raise ValueError(f"Partial XML must end at 'ask': {session_xml}")

                # Cannot have submit in partial XML
                if "submit" in found_tags:
                    raise ValueError(f"Partial XML cannot contain submit: {session_xml}")

                # Validate ask/response pairing up to the last ask
                if not self._validate_ask_response_pairing_or_fail(tag_sequence[:-1]):
                    # Error already raised by helper method
                    pass

                return True  # Partial and valid

        except ET.ParseError:
            raise ValueError(f"Invalid XML: {session_xml}")

    def validate_session_xml(
        self, session_xml: str, is_leaf: bool, is_partial: bool = False
    ) -> bool:
        """
        Validate that session XML contains only allowed tags for node type.

        Args:
            session_xml: XML string to validate
            is_leaf: True if this is a leaf node, False if parent node
            is_partial: True if this is partial XML (should end at </ask>)

        Returns:
            bool: True if XML is valid, False otherwise

        Validation rules:
        - Leaf nodes allow: prompt, submit
        - Parent nodes allow: prompt, submit, notes, ask, response
        - <prompt> must always be first
        - If not partial, <submit> must be last
        - If partial, must end at </ask>
        - <ask> and <response> must be paired in that order
        - <notes> cannot appear between <ask> and <response>
        - Partial validation is not allowed for leaf nodes
        """
        # Rule: Partial validation is not allowed for leaf nodes
        if is_leaf and is_partial:
            return False
            
        try:
            is_xml_partial = self.get_is_xml_partial_or_fail(session_xml, is_leaf)
            
            # Check if the partial/complete status matches what was requested
            if is_partial and not is_xml_partial:
                # Requested partial but XML is complete
                return False
            elif not is_partial and is_xml_partial:
                # Requested complete but XML is partial
                return False
            
            return True
            
        except ValueError as e:
            logging.error("XML validation failed: %s", str(e))
            return False

    def _validate_ask_response_pairing_or_fail(self, tag_sequence: list[str]) -> bool:
        """
        Validate that ask and response tags are properly paired.
        Raises ValueError if invalid.

        Rules:
        - Every <ask> must be followed by a <response> (before the next <ask>)
        - Every <response> must be preceded by an <ask>
        - <notes> cannot appear between <ask> and <response>
        """
        expecting_response = False

        for tag in tag_sequence:
            if tag == "ask":
                if expecting_response:
                    # Found another ask before response
                    raise ValueError("Found <ask> without matching <response>")
                expecting_response = True
            elif tag == "response":
                if not expecting_response:
                    # Found response without preceding ask
                    raise ValueError("Found <response> without preceding <ask>")
                expecting_response = False
            elif tag == "notes" and expecting_response:
                # Notes between ask and response
                raise ValueError("Found <notes> between <ask> and <response>")

        # If we're still expecting a response at the end, that's invalid
        # (unless this is being called on a partial sequence)
        if expecting_response:
            raise ValueError("Unpaired <ask> without <response>")

        return True

    def _validate_ask_response_pairing(self, tag_sequence: list[str]) -> bool:
        """
        Validate that ask and response tags are properly paired.

        Rules:
        - Every <ask> must be followed by a <response> (before the next <ask>)
        - Every <response> must be preceded by an <ask>
        - <notes> cannot appear between <ask> and <response>
        """
        expecting_response = False

        for tag in tag_sequence:
            if tag == "ask":
                if expecting_response:
                    # Found another ask before response
                    logging.error("Found <ask> without matching <response>")
                    return False
                expecting_response = True
            elif tag == "response":
                if not expecting_response:
                    # Found response without preceding ask
                    logging.error("Found <response> without preceding <ask>")
                    return False
                expecting_response = False
            elif tag == "notes" and expecting_response:
                # Notes between ask and response
                logging.error("Found <notes> between <ask> and <response>")
                return False

        # If we're still expecting a response at the end, that's invalid
        # (unless this is being called on a partial sequence)
        if expecting_response:
            logging.error("Unpaired <ask> without <response>")
            return False

        return True

    def _extract_tags(self, root_element) -> set[str]:
        """Extract all XML tag names from direct children of root element."""
        return {child.tag for child in root_element}
