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
        raise NotImplementedError("Not implemented")

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
        if not session_xml or not session_xml.strip():
            return False

        # Leaf nodes cannot be partial
        if is_leaf and is_partial:
            return False

        try:
            # For partial XML, we need to complete it before parsing
            xml_to_parse = session_xml
            if is_partial:
                # Add closing session tag if missing
                xml_to_parse = session_xml.strip()
                if not xml_to_parse.endswith("</session>"):
                    xml_to_parse += "\n</session>"

            # Parse the XML
            root = ET.fromstring(xml_to_parse)

            # Check that root is 'session'
            if root.tag != "session":
                logging.error("Root tag is not 'session': %s", session_xml)
                return False

            # Get list of child tags in order
            children = list(root)
            if not children:
                return False

            # Extract tag names preserving order
            tag_sequence = [child.tag for child in children]
            found_tags = set(tag_sequence)

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

            # Rule 1: <prompt> must be first
            if tag_sequence[0] != "prompt":
                logging.error("First tag must be 'prompt': %s", session_xml)
                return False

            # Rule 2: If not partial, <submit> must be last
            if not is_partial:
                if tag_sequence[-1] != "submit":
                    logging.error(
                        "Last tag must be 'submit' for complete XML: %s", session_xml
                    )
                    return False

                # For leaf nodes, both prompt and submit are required
                if is_leaf:
                    if "prompt" not in found_tags or "submit" not in found_tags:
                        logging.error(
                            "Leaf node missing prompt or submit: %s", session_xml
                        )
                        return False
                    # Leaf nodes cannot have ask/response
                    if "ask" in found_tags or "response" in found_tags:
                        logging.error(
                            "Leaf node cannot have ask/response tags: %s", session_xml
                        )
                        return False
                else:
                    # For complete parent nodes, validate ask/response pairing
                    if not self._validate_ask_response_pairing(tag_sequence):
                        return False
            else:
                # Rule 3: If partial, must end at </ask>
                if tag_sequence[-1] != "ask":
                    logging.error("Partial XML must end at </ask>: %s", session_xml)
                    return False

                # Cannot have submit in partial XML
                if "submit" in found_tags:
                    logging.error("Partial XML cannot contain submit: %s", session_xml)
                    return False

                # Validate ask/response pairing up to the last ask
                if not self._validate_ask_response_pairing(tag_sequence[:-1]):
                    return False

            return True

        except ET.ParseError:
            logging.error("Invalid XML: %s", session_xml)
            return False

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
