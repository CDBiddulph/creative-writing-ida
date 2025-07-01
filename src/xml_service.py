"""Unified XML service for all XML operations in the codebase.

This service replaces direct ElementTree usage throughout the codebase and provides
a clean interface for all XML-related operations including parsing, validation,
formatting, and example extraction.
"""

import xml.etree.ElementTree as ET
import io
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

from .session import (
    Session,
    PromptEvent,
    NotesEvent,
    AskEvent,
    ResponseEvent,
    SubmitEvent,
)
from .xml_validator import XmlValidator


class XmlService:
    """Unified service for all XML operations.

    Consolidates XML parsing, validation, formatting, and example extraction
    to eliminate scattered ElementTree usage throughout the codebase.
    """

    def __init__(self):
        """Initialize XML service with validator."""
        self.xml_validator = XmlValidator()

    def parse_sessions_file(self, file_path: Path) -> List[Session]:
        """Parse a complete sessions XML file into Session objects.

        Args:
            file_path: Path to the XML file containing sessions

        Returns:
            List of Session objects parsed from the file

        Raises:
            ValueError: If XML is malformed or cannot be parsed
        """
        try:
            if file_path.is_dir():
                raise ValueError(f"Expected file path, got directory: {file_path}")

            content = file_path.read_text(encoding="utf-8")
            root = ET.fromstring(content)

            if root.tag != "sessions":
                raise ValueError(f"Expected root element 'sessions', got '{root.tag}'")

            sessions = []
            for session_elem in root.findall("session"):
                # Get session ID
                id_elem = session_elem.find("id")
                if id_elem is None or id_elem.text is None:
                    raise ValueError(f"Session without ID: {session_elem}")

                try:
                    session_id = int(id_elem.text)
                except ValueError:
                    raise ValueError(f"Invalid session ID: {id_elem.text}")

                # Create session object
                session = Session(session_id=session_id)

                # Parse events (skip id, response-id, and notes elements)
                for elem in session_elem:
                    text = elem.text or ""
                    if elem.tag in ("id", "response-id"):
                        continue
                    elif elem.tag == "prompt":
                        session.add_event(PromptEvent(text=text))
                    elif elem.tag == "notes":
                        session.add_event(NotesEvent(text=text))
                    elif elem.tag == "ask":
                        session.add_event(AskEvent(text=text))
                    elif elem.tag == "response":
                        session.add_event(ResponseEvent(text=text))
                    elif elem.tag == "submit":
                        session.add_event(SubmitEvent(text=text))
                    else:
                        raise ValueError(f"Unknown element: {elem.tag}")

                sessions.append(session)

            return sessions

        except ET.ParseError as e:
            raise ValueError(f"XML parsing error: {e}")
        except FileNotFoundError:
            raise ValueError(f"File not found: {file_path}")

    def validate_session_xml(
        self, xml_string: str, is_leaf: bool, is_partial: bool = False
    ) -> bool:
        """Validate session XML structure.

        Args:
            xml_string: XML string to validate
            is_leaf: Whether this is a leaf session
            is_partial: Whether to allow incomplete sessions

        Returns:
            True if XML is valid, False otherwise
        """
        return self.xml_validator.validate_session_xml(xml_string, is_leaf, is_partial)

    def format_sessions_to_xml(
        self, sessions: List[Session], final_response: str = None
    ) -> str:
        """Format Session objects into complete XML document.

        Args:
            sessions: List of Session objects to format
            final_response: Optional final response text to include in document

        Returns:
            Complete XML document string with headers and formatting
        """
        # Create root sessions element
        sessions_elem = ET.Element("sessions")

        # Add final-response if provided
        if final_response:
            final_elem = ET.SubElement(sessions_elem, "final-response")
            final_elem.text = final_response

        # Add each session
        for session in sessions:
            session_elem = ET.SubElement(sessions_elem, "session")

            # Add session ID
            id_elem = ET.SubElement(session_elem, "id")
            id_elem.text = str(session.session_id)

            # Add events
            for event in session.events:
                event_elem = event.to_xml_element()
                session_elem.append(event_elem)

        # Pretty print
        self._indent(sessions_elem)

        # Create XML string with header
        output = io.StringIO()
        output.write('<?xml version="1.0" encoding="UTF-8"?>\n')

        tree = ET.ElementTree(sessions_elem)
        tree.write(output, encoding="unicode", xml_declaration=False)

        return output.getvalue()

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

    def extract_final_response(self, file_path: Path) -> Optional[str]:
        """Extract final-response content from a session file.

        Args:
            file_path: Path to the XML file

        Returns:
            Final response text if present, None otherwise
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            root = ET.fromstring(content)

            final_elem = root.find("final-response")
            if final_elem is not None and final_elem.text:
                return final_elem.text

            return None

        except (ET.ParseError, FileNotFoundError):
            raise ValueError(f"Error reading or parsing file: {file_path}")

    def count_sessions(self, file_path: Path) -> int:
        """Count the number of sessions in a file.

        Args:
            file_path: Path to the XML file

        Returns:
            Number of sessions in the file
        """
        # Parse file and count sessions
        sessions = self.parse_sessions_file(file_path)
        return len(sessions)

    def write_sessions_file(
        self, sessions: List[Session], file_path: Path, final_response: str = None
    ) -> None:
        """Write Session objects to an XML file.

        Args:
            sessions: List of Session objects to write
            file_path: Path where to write the XML file
            final_response: Optional final response text to include
        """
        xml_content = self.format_sessions_to_xml(sessions, final_response)
        file_path.write_text(xml_content, encoding="utf-8")
