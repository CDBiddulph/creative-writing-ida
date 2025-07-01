"""Session and event classes for representing session data as Python objects."""

from dataclasses import dataclass, field
from typing import List, Type
from abc import ABC, abstractmethod
import xml.etree.ElementTree as ET

FAILED_STR = "FAILED"


@dataclass
class SessionEvent(ABC):
    """Base class for session events."""

    @abstractmethod
    def to_xml_element(self) -> ET.Element:
        """Convert event to XML element."""
        pass


@dataclass
class PromptEvent(SessionEvent):
    """Represents a prompt event in a session."""

    text: str

    def to_xml_element(self) -> ET.Element:
        elem = ET.Element("prompt")
        elem.text = self.text
        return elem


@dataclass
class NotesEvent(SessionEvent):
    """Represents a notes event in a session."""

    text: str

    def to_xml_element(self) -> ET.Element:
        elem = ET.Element("notes")
        elem.text = self.text
        return elem


@dataclass
class AskEvent(SessionEvent):
    """Represents an ask event in a session."""

    text: str

    def to_xml_element(self) -> ET.Element:
        elem = ET.Element("ask")
        elem.text = self.text
        return elem


@dataclass
class ResponseEvent(SessionEvent):
    """Represents a response event in a session."""

    text: str

    def to_xml_element(self) -> ET.Element:
        elem = ET.Element("response")
        elem.text = self.text
        return elem


@dataclass
class SubmitEvent(SessionEvent):
    """Represents a submit event in a session."""

    text: str

    def to_xml_element(self) -> ET.Element:
        elem = ET.Element("submit")
        elem.text = self.text
        return elem


@dataclass
class Session:
    """Represents a complete session with events and metadata."""

    session_id: int
    events: List[SessionEvent] = field(default_factory=list)
    is_failed: bool = False

    def add_event(self, event: SessionEvent) -> None:
        """Add an event to the session."""
        if self.is_failed:
            raise ValueError("Cannot add an event to a failed session")
        last_event = next(reversed(self.events), None)
        if isinstance(last_event, SubmitEvent):
            raise ValueError("Cannot add an event after a submit event")
        self.events.append(event)

    def to_xml(self, include_closing_tag: bool = True) -> str:
        """Convert session to XML string."""
        if self.is_failed:
            return FAILED_STR

        lines = ["<session>"]
        for event in self.events:
            elem = event.to_xml_element()
            lines.append(f"<{elem.tag}>{elem.text}</{elem.tag}>")

        if include_closing_tag:
            lines.append("</session>")

        return "\n".join(lines)

    @classmethod
    def from_xml(cls, xml_string: str, session_id: int) -> "Session":
        """Create a Session from an XML string."""
        # Handle partial XML by adding closing tag if needed
        if not xml_string.strip().endswith("</session>"):
            xml_string = xml_string + "\n</session>"

        root = ET.fromstring(xml_string)

        session = cls(session_id=session_id)

        for elem in root:
            text = elem.text or ""
            if elem.tag == "prompt":
                session.add_event(PromptEvent(text=text))
            elif elem.tag == "notes":
                session.add_event(NotesEvent(text=text))
            elif elem.tag == "ask":
                session.add_event(AskEvent(text=text))
            elif elem.tag == "response":
                session.add_event(ResponseEvent(text=text))
            elif elem.tag == "submit":
                session.add_event(SubmitEvent(text=text))

        return session

    def is_complete(self) -> bool:
        """Check if session is complete (has a submit event)."""
        if self.is_failed:
            return True
        try:
            self.get_submit_text()
            return True
        except ValueError:
            return False

    def _get_last_event_text(self, event_type: Type[SessionEvent]) -> str:
        """Get the text of the last event of the given type.

        Raises:
            ValueError: If the last event is not of the given type.
        """
        if self.is_failed:
            return FAILED_STR
        if not self.events:
            raise ValueError("No events in session")
        event = self.events[-1]
        if not isinstance(event, event_type):
            raise ValueError(f"Last event is not a {event_type.__name__} event")
        return event.text

    def get_prompt_text(self) -> str:
        """Get the text of the first event of the given type."""
        if self.is_failed:
            raise ValueError("Cannot get prompt text for a failed session")
        if not self.events:
            raise ValueError("No events in session")
        if not isinstance(self.events[0], PromptEvent):
            raise ValueError("First event is not a prompt event")
        return self.events[0].text

    def get_ask_text(self) -> str:
        """Get the text of the last event, which should be an ask event.

        Raises:
            ValueError: If the last event is not an ask event
        """
        return self._get_last_event_text(AskEvent)

    def get_submit_text(self) -> str:
        """Get the text of the last event, which should be a submit event.

        Raises:
            ValueError: If the last event is not a submit event
        """
        return self._get_last_event_text(SubmitEvent)

    def copy(self) -> "Session":
        """Create a copy of this session."""
        new_session = Session(session_id=self.session_id, is_failed=self.is_failed)
        for event in self.events:
            # Create new event instances
            if isinstance(event, PromptEvent):
                new_session.add_event(PromptEvent(text=event.text))
            elif isinstance(event, NotesEvent):
                new_session.add_event(NotesEvent(text=event.text))
            elif isinstance(event, AskEvent):
                new_session.add_event(AskEvent(text=event.text))
            elif isinstance(event, ResponseEvent):
                new_session.add_event(ResponseEvent(text=event.text))
            elif isinstance(event, SubmitEvent):
                new_session.add_event(SubmitEvent(text=event.text))
        return new_session
