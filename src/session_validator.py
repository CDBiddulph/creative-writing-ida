"""Validates Session objects for correct structure and event sequences."""

from typing import List

from .session import (
    Session,
    PromptEvent,
    NotesEvent,
    AskEvent,
    ResponseEvent,
    SubmitEvent,
)


class SessionValidator:
    """Validates Session objects for correct structure and event sequences."""

    def validate_session(self, session: Session, is_leaf: bool) -> None:
        """
        Validate session structure for the given node type.

        Args:
            session: Session object to validate
            is_leaf: True for leaf node, False for parent node

        Raises:
            ValueError: If session structure is invalid (wrong events, order, etc.)
        """
        if not session.events:
            raise ValueError("Empty session")

        # Rule: PromptEvent must be first
        if not isinstance(session.events[0], PromptEvent):
            event_name = session.events[0].__class__.__name__
            raise ValueError(f"First event must be PromptEvent, got {event_name}")

        if is_leaf:
            self._validate_leaf_session(session)
        else:
            self._validate_parent_session(session)

    def _validate_leaf_session(self, session: Session) -> None:
        """Validate a leaf session's structure."""
        num_events = len(session.events)

        # Leaf sessions can only have 2 events.
        # There are no partial leaf sessions.
        if num_events != 2:
            raise ValueError(f"Leaf session must have 2 events, got {num_events}")
        # The last event must be SubmitEvent.
        if not isinstance(session.events[1], SubmitEvent):
            event_name = session.events[1].__class__.__name__
            raise ValueError(
                f"Last event in leaf session must be SubmitEvent, got {event_name}"
            )

    def _validate_parent_session(self, session: Session) -> None:
        """Validate a parent session's structure."""
        # Check if complete (has SubmitEvent as last event)
        if isinstance(session.events[-1], SubmitEvent):
            # Complete parent session - validate ask/response pairing
            self._validate_ask_response_pairing_or_fail(session.events)
        else:
            # Partial parent session - must end with AskEvent
            if not isinstance(session.events[-1], AskEvent):
                event_name = session.events[-1].__class__.__name__
                raise ValueError(
                    f"Partial parent session must end with AskEvent, got {event_name}"
                )

            # Cannot have SubmitEvent in partial session
            if any(isinstance(event, SubmitEvent) for event in session.events):
                raise ValueError("Partial session cannot contain SubmitEvent")

            # Validate ask/response pairing up to the last ask
            if len(session.events) > 1:
                self._validate_ask_response_pairing_or_fail(session.events[:-1])

    def _validate_ask_response_pairing_or_fail(self, events: List) -> None:
        """
        Validate that AskEvent and ResponseEvent are properly paired.
        Raises ValueError if invalid.

        Rules:
        - Every AskEvent must be followed by a ResponseEvent (before the next AskEvent)
        - Every ResponseEvent must be preceded by an AskEvent
        - No events of any kind can appear between AskEvent and ResponseEvent
        """
        expecting_response = False

        for i, event in enumerate(events):
            if isinstance(event, AskEvent):
                if expecting_response:
                    # Found another ask before response
                    raise ValueError(
                        f"Found AskEvent without matching ResponseEvent: index {i} of {events}"
                    )
                expecting_response = True
            elif isinstance(event, ResponseEvent):
                if not expecting_response:
                    # Found response without preceding ask
                    raise ValueError(
                        f"Found ResponseEvent without preceding AskEvent: index {i} of {events}"
                    )
                expecting_response = False
            elif expecting_response:
                # Any event other than ResponseEvent while expecting response is invalid
                event_name = event.__class__.__name__
                raise ValueError(
                    f"Found {event_name} instead of ResponseEvent after AskEvent: index {i} of {events}"
                )

        # If we're still expecting a response at the end, that's invalid
        # (unless this is being called on a partial sequence)
        if expecting_response:
            raise ValueError(
                f"Unpaired AskEvent without ResponseEvent: index {i} of {events}"
            )
