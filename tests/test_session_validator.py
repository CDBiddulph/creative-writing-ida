"""Tests for SessionValidator class."""

import pytest
from src.session_validator import SessionValidator
from src.session import (
    Session,
    PromptEvent,
    NotesEvent,
    AskEvent,
    ResponseEvent,
    SubmitEvent,
)


class TestSessionValidator:
    """Test the SessionValidator class."""

    @pytest.fixture
    def validator(self):
        """Create SessionValidator instance."""
        return SessionValidator()

    def test_validate_leaf_session_valid(self, validator):
        """Test validation of valid leaf session."""
        session = Session(session_id=0)
        session.add_event(PromptEvent("Write a story about robots"))
        session.add_event(
            SubmitEvent("Once upon a time, there was a robot named Bob...")
        )

        # Should not raise exception
        validator.validate_session(session, is_leaf=True)

    def test_validate_leaf_session_minimal(self, validator):
        """Test validation of minimal valid leaf session."""
        session = Session(session_id=0)
        session.add_event(PromptEvent("Test"))
        session.add_event(SubmitEvent("Result"))

        # Should not raise exception
        validator.validate_session(session, is_leaf=True)

    def test_validate_leaf_session_invalid_events(self, validator):
        """Test validation fails for leaf with invalid events."""
        session = Session(session_id=0)
        session.add_event(PromptEvent("Write a story"))
        session.add_event(NotesEvent("This shouldn't be in a leaf"))
        session.add_event(SubmitEvent("Story content"))

        with pytest.raises(ValueError, match="Leaf session must have 2 events, got 3"):
            validator.validate_session(session, is_leaf=True)

    def test_validate_parent_session_valid(self, validator):
        """Test validation of valid parent session."""
        session = Session(session_id=0)
        session.add_event(PromptEvent("Write a story about robots"))
        session.add_event(NotesEvent("I need to think about this"))
        session.add_event(AskEvent("What type of robot?"))
        session.add_event(ResponseEvent("Friendly cleaning robot"))
        session.add_event(SubmitEvent("A story about a friendly cleaning robot"))

        # Should not raise exception
        validator.validate_session(session, is_leaf=False)

    def test_validate_parent_session_with_multiple_asks(self, validator):
        """Test validation of parent session with multiple ask/response pairs."""
        session = Session(session_id=0)
        session.add_event(PromptEvent("Complex task"))
        session.add_event(AskEvent("First question?"))
        session.add_event(ResponseEvent("First answer"))
        session.add_event(AskEvent("Second question?"))
        session.add_event(ResponseEvent("Second answer"))
        session.add_event(SubmitEvent("Final result"))

        # Should not raise exception
        validator.validate_session(session, is_leaf=False)

    def test_validate_parent_session_minimal(self, validator):
        """Test validation of minimal valid parent session."""
        session = Session(session_id=0)
        session.add_event(PromptEvent("Task"))
        session.add_event(SubmitEvent("Result"))

        # Should not raise exception
        validator.validate_session(session, is_leaf=False)

    def test_validate_empty_session(self, validator):
        """Test validation fails for empty session."""
        session = Session(session_id=0)

        with pytest.raises(ValueError, match="Empty session"):
            validator.validate_session(session, is_leaf=True)

    def test_validate_prompt_not_first_fails(self, validator):
        """Test validation fails when prompt is not first."""
        # Create session with events in wrong order by manipulating the events list directly
        session = Session(session_id=0)
        session.events = [SubmitEvent("Result first"), PromptEvent("Prompt second")]

        with pytest.raises(ValueError, match="First event must be PromptEvent"):
            validator.validate_session(session, is_leaf=True)

    def test_validate_ask_without_response_fails(self, validator):
        """Test validation fails for ask without response."""
        session = Session(session_id=0)
        session.add_event(PromptEvent("Prompt"))
        session.add_event(AskEvent("Ask"))
        session.add_event(SubmitEvent("Submission"))

        with pytest.raises(
            ValueError, match="Found SubmitEvent after AskEvent, expected ResponseEvent"
        ):
            validator.validate_session(session, is_leaf=False)

    def test_validate_response_without_ask_fails(self, validator):
        """Test validation fails for response without ask."""
        session = Session(session_id=0)
        session.add_event(PromptEvent("Prompt"))
        session.add_event(ResponseEvent("Response"))
        session.add_event(SubmitEvent("Submission"))

        with pytest.raises(
            ValueError, match="Found ResponseEvent without preceding AskEvent"
        ):
            validator.validate_session(session, is_leaf=False)

    def test_validate_notes_between_ask_response_invalid(self, validator):
        """Test validation fails for notes between ask and response."""
        session = Session(session_id=0)
        session.add_event(PromptEvent("Prompt"))
        session.add_event(AskEvent("Question"))
        session.add_event(NotesEvent("Notes in wrong place"))
        session.add_event(ResponseEvent("Answer"))
        session.add_event(SubmitEvent("Result"))

        with pytest.raises(
            ValueError, match="Found NotesEvent after AskEvent, expected ResponseEvent"
        ):
            validator.validate_session(session, is_leaf=False)

    def test_partial_validation_succeeds(self, validator):
        """Test partial validation for parent session."""
        session = Session(session_id=0)
        session.add_event(PromptEvent("Task"))
        session.add_event(AskEvent("Question"))

        # Should not raise exception for partial validation
        validator.validate_session(session, is_leaf=False)

    def test_partial_leaf_session_valid(self, validator):
        """Test partial leaf session (just prompt) is valid."""
        session = Session(session_id=0)
        session.add_event(PromptEvent("Task"))

        # A partial leaf session (just prompt) is not valid.
        with pytest.raises(ValueError, match="Leaf session must have 2 events, got 1"):
            validator.validate_session(session, is_leaf=True)

    def test_leaf_with_ask_response_fails(self, validator):
        """Test leaf session with ask/response fails."""
        session = Session(session_id=0)
        session.add_event(PromptEvent("Task"))
        session.add_event(AskEvent("Question"))
        session.add_event(ResponseEvent("Answer"))
        session.add_event(SubmitEvent("Result"))

        with pytest.raises(ValueError, match="Leaf session must have 2 events, got 4"):
            validator.validate_session(session, is_leaf=True)

    def test_partial_session_notes_before_ask_valid(self, validator):
        """Test partial validation allows notes before ask."""
        session = Session(session_id=0)
        session.add_event(PromptEvent("Task"))
        session.add_event(NotesEvent("Some notes"))
        session.add_event(AskEvent("Question"))

        # Should not raise exception
        validator.validate_session(session, is_leaf=False)

    def test_multiple_ask_response_pairs_valid(self, validator):
        """Test multiple ask/response pairs are valid."""
        session = Session(session_id=0)
        session.add_event(PromptEvent("Complex task"))
        session.add_event(AskEvent("First question"))
        session.add_event(ResponseEvent("First answer"))
        session.add_event(AskEvent("Second question"))
        session.add_event(ResponseEvent("Second answer"))
        session.add_event(AskEvent("Third question"))
        session.add_event(ResponseEvent("Third answer"))
        session.add_event(SubmitEvent("Final result"))

        # Should not raise exception
        validator.validate_session(session, is_leaf=False)
