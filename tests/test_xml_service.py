"""Tests for unified XML service."""

import tempfile
from pathlib import Path
import pytest

from src.xml_service import XmlService
from src.session import (
    Session,
    PromptEvent,
    NotesEvent,
    AskEvent,
    ResponseEvent,
    SubmitEvent,
)


class TestXmlService:
    """Test the unified XML service that replaces direct ElementTree usage."""

    @pytest.fixture
    def xml_service(self):
        """Create XML service instance."""
        return XmlService()

    @pytest.fixture
    def sample_session_file(self):
        """Create a sample session XML file for testing."""
        xml_content = """<?xml version='1.0' encoding='utf-8'?>
<sessions>
  <final-response>Complete story about robots</final-response>
  <session>
    <id>0</id>
    <prompt>Write a story about robots</prompt>
    <ask>What type of robot?</ask>
    <response-id>1</response-id>
    <response>Friendly cleaning robot</response>
    <submit>A story about a friendly cleaning robot</submit>
  </session>
  <session>
    <id>1</id>
    <prompt>What type of robot?</prompt>
    <submit>Friendly cleaning robot</submit>
  </session>
</sessions>"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(xml_content)
            return Path(f.name)

    @pytest.fixture
    def sessions_directory(self):
        """Create a directory with multiple session files."""
        tmpdir = Path(tempfile.mkdtemp())

        # Create multiple session files
        for i in range(3):
            session_content = f"""<?xml version='1.0' encoding='utf-8'?>
<sessions>
  <session>
    <id>0</id>
    <prompt>Prompt {i}</prompt>
    <submit>Response {i}</submit>
  </session>
  <session>
    <id>1</id>
    <prompt>Child prompt {i}</prompt>
    <submit>Child response {i}</submit>
  </session>
</sessions>"""
            session_file = tmpdir / f"{i+1}-test-prompt-{i}.xml"
            session_file.write_text(session_content)

        return tmpdir

    def test_parse_sessions_file_returns_session_objects(
        self, xml_service, sample_session_file
    ):
        """Test that parse_sessions_file returns proper Session objects."""
        sessions = xml_service.parse_sessions_file(sample_session_file)

        assert len(sessions) == 2

        # Check first session (parent)
        session_0 = sessions[0]
        assert isinstance(session_0, Session)
        assert session_0.session_id == 0
        assert len(session_0.events) == 4  # prompt, ask, response, submit
        assert isinstance(session_0.events[0], PromptEvent)
        assert isinstance(session_0.events[1], AskEvent)
        assert isinstance(session_0.events[2], ResponseEvent)
        assert isinstance(session_0.events[3], SubmitEvent)

        # Check second session (leaf)
        session_1 = sessions[1]
        assert isinstance(session_1, Session)
        assert session_1.session_id == 1
        assert len(session_1.events) == 2  # prompt, submit
        assert isinstance(session_1.events[0], PromptEvent)
        assert isinstance(session_1.events[1], SubmitEvent)

    def test_parse_sessions_file_without_ids(self, xml_service):
        """Test parsing example files without ID tags uses index as session ID."""
        xml_content = """<?xml version='1.0' encoding='utf-8'?>
<sessions>
  <session>
    <prompt>Write a story</prompt>
    <submit>Once upon a time...</submit>
  </session>
  <session>
    <prompt>Continue the story</prompt>
    <submit>And they lived happily ever after.</submit>
  </session>
</sessions>"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(xml_content)
            file_path = Path(f.name)

        sessions = xml_service.parse_sessions_file(file_path)

        assert len(sessions) == 2
        assert sessions[0].session_id == 0  # First session gets index 0
        assert sessions[1].session_id == 1  # Second session gets index 1
        assert sessions[0].get_prompt_text() == "Write a story"
        assert sessions[1].get_prompt_text() == "Continue the story"

    def test_parse_sessions_file_handles_malformed_xml(self, xml_service):
        """Test graceful handling of malformed XML."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write("<unclosed_tag>malformed")
            malformed_file = Path(f.name)

        with pytest.raises(ValueError, match="XML parsing error"):
            xml_service.parse_sessions_file(malformed_file)

    def test_parse_sessions_file_handles_failed_sessions(self, xml_service):
        """Test parsing of XML with FAILED sessions."""
        xml_content = """<?xml version='1.0' encoding='utf-8'?>
<sessions>
  <session>
    <id>0</id>
    <prompt>Test prompt</prompt>
    <submit>FAILED</submit>
  </session>
</sessions>"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(xml_content)
            file_path = Path(f.name)

        sessions = xml_service.parse_sessions_file(file_path)
        assert len(sessions) == 1

        session = sessions[0]
        # TODO: consider changing this behavior to mark as failed if the text is FAILED
        assert session.is_failed is False
        assert session.get_submit_text() == "FAILED"

    def test_validate_session_xml_integration(self, xml_service):
        """Test that XML service integrates with existing validation."""
        # Valid leaf session should not raise
        valid_leaf = "<session><prompt>Test</prompt><submit>Result</submit></session>"
        xml_service.validate_session_xml(valid_leaf, is_leaf=True)  # Should not raise

        # Invalid leaf session (missing submit)
        partial_leaf = "<session><prompt>Test</prompt></session>"
        with pytest.raises(ValueError):
            xml_service.validate_session_xml(partial_leaf, is_leaf=True)

    def test_format_sessions_to_file_integration(self, xml_service):
        """Test that XML service integrates with formatting capabilities."""
        # Create Session objects
        session1 = Session(session_id=0)
        session1.add_event(PromptEvent("Test prompt"))
        session1.add_event(SubmitEvent("Test result"))

        session2 = Session(session_id=1)
        session2.add_event(PromptEvent("Child prompt"))
        session2.add_event(SubmitEvent("Child result"))

        sessions = [session1, session2]

        # Should be able to format sessions to XML with optional final response
        xml_output = xml_service.format_sessions_to_xml(
            sessions, final_response="Final result"
        )

        assert "<?xml version=" in xml_output
        assert "<sessions>" in xml_output
        assert "<session>" in xml_output
        assert "<id>0</id>" in xml_output
        assert "<id>1</id>" in xml_output
        assert "Test prompt" in xml_output
        assert "Child prompt" in xml_output
        assert "<final-response>Final result</final-response>" in xml_output

    def test_extract_final_response_from_file(self, xml_service, sample_session_file):
        """Test extracting final-response content from session files."""
        final_response = xml_service.extract_final_response(sample_session_file)

        assert final_response == "Complete story about robots"

    def test_extract_final_response_missing_returns_none(self, xml_service):
        """Test that missing final-response returns None."""
        xml_content = """<?xml version='1.0' encoding='utf-8'?>
<sessions>
  <session>
    <id>0</id>
    <prompt>Test</prompt>
    <submit>Result</submit>
  </session>
</sessions>"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(xml_content)
            file_path = Path(f.name)

        final_response = xml_service.extract_final_response(file_path)
        assert final_response is None

    def test_count_sessions_in_file(self, xml_service, sample_session_file):
        """Test counting number of sessions in a file."""
        count = xml_service.count_sessions(sample_session_file)
        assert count == 2

    def test_parse_sessions_file_preserves_event_order(self, xml_service):
        """Test that event order is preserved when parsing sessions."""
        xml_content = """<?xml version='1.0' encoding='utf-8'?>
<sessions>
  <session>
    <id>0</id>
    <prompt>Main task</prompt>
    <notes>Initial thoughts</notes>
    <ask>First question</ask>
    <response-id>1</response-id>
    <response>First answer</response>
    <ask>Second question</ask>
    <response-id>2</response-id>
    <response>Second answer</response>
    <submit>Final result</submit>
  </session>
</sessions>"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(xml_content)
            file_path = Path(f.name)

        sessions = xml_service.parse_sessions_file(file_path)
        session = sessions[0]

        # Check event order is preserved
        event_types = [type(event).__name__ for event in session.events]
        expected_order = [
            "PromptEvent",
            "NotesEvent",
            "AskEvent",
            "ResponseEvent",
            "AskEvent",
            "ResponseEvent",
            "SubmitEvent",
        ]
        assert event_types == expected_order

    def test_parse_sessions_file_handles_empty_file(self, xml_service):
        """Test handling of empty sessions file."""
        xml_content = """<?xml version='1.0' encoding='utf-8'?>
<sessions>
</sessions>"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(xml_content)
            file_path = Path(f.name)

        sessions = xml_service.parse_sessions_file(file_path)
        assert len(sessions) == 0

    def test_format_sessions_to_xml_includes_metadata(self, xml_service):
        """Test that formatting includes proper metadata and structure."""
        # Create Session objects
        session1 = Session(session_id=0)
        session1.add_event(PromptEvent("Main task"))
        session1.add_event(AskEvent("What approach?"))
        session1.add_event(ResponseEvent("Step by step"))
        session1.add_event(SubmitEvent("Completed task"))

        session2 = Session(session_id=1)
        session2.add_event(PromptEvent("What approach?"))
        session2.add_event(SubmitEvent("Step by step"))

        sessions = [session1, session2]

        xml_output = xml_service.format_sessions_to_xml(sessions)

        # Should include XML declaration
        assert xml_output.startswith("<?xml version='1.0' encoding='utf-8'?>")

        # Should have sessions root
        assert "<sessions>" in xml_output
        assert "</sessions>" in xml_output

        # Should include session IDs
        assert "<id>0</id>" in xml_output
        assert "<id>1</id>" in xml_output

        # Should include basic session structure without response-id (that's tree-specific metadata)
        assert "<ask>What approach?</ask>" in xml_output
        assert "<response>Step by step</response>" in xml_output

    def test_write_empty_sessions_list(self, xml_service):
        """Test that writing an empty list of sessions creates valid XML."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            output_path = Path(f.name)

        # Write empty list of sessions
        xml_service.write_sessions_file([], output_path)

        # Verify file was created and has valid content
        assert output_path.exists()
        content = output_path.read_text()

        # Should have XML declaration and empty sessions element
        assert content.startswith("<?xml version='1.0' encoding='utf-8'?>")
        assert "<sessions />" in content
        assert "<session>" not in content  # No session elements

        # Should be able to parse back the empty file
        sessions = xml_service.parse_sessions_file(output_path)
        assert len(sessions) == 0

    def test_auto_detect_complete_session(self, xml_service):
        """Test auto-detection of complete session XML."""
        complete_xml = """
        <session>
            <prompt>Test task</prompt>
            <submit>Result</submit>
        </session>
        """

        # Should auto-detect as complete and not raise
        xml_service.validate_session_xml(complete_xml, is_leaf=True)

    def test_auto_detect_partial_session(self, xml_service):
        """Test auto-detection of partial session XML."""
        partial_xml = """
        <session>
            <prompt>Test task</prompt>
            <ask>What should I do?</ask>
        """

        # Should auto-detect as partial and not raise
        xml_service.validate_session_xml(partial_xml, is_leaf=False)

    def test_auto_detect_malformed_xml(self, xml_service):
        """Test auto-detection with malformed XML raises appropriate error."""
        malformed_xml = "<session><prompt>Test<unclosed_tag>"

        with pytest.raises(ValueError):
            xml_service.validate_session_xml(malformed_xml, is_leaf=True)

    def test_validate_leaf_session_valid_comprehensive(self, xml_service):
        """Test validation of valid leaf session XML with detailed content."""
        xml = """
        <session>
            <prompt>Write a story about robots</prompt>
            <submit>Once upon a time, there was a robot named Bob...</submit>
        </session>
        """

        # Should not raise an exception for valid XML
        xml_service.validate_session_xml(xml, is_leaf=True)

    def test_validate_leaf_session_invalid_tags(self, xml_service):
        """Test validation fails for leaf with invalid tags."""
        xml = """
        <session>
            <prompt>Write a story</prompt>
            <notes>This shouldn't be in a leaf</notes>
            <submit>Story content</submit>
        </session>
        """

        with pytest.raises(ValueError):
            xml_service.validate_session_xml(xml, is_leaf=True)

    def test_validate_parent_session_valid_comprehensive(self, xml_service):
        """Test validation of valid parent session XML with all event types."""
        xml = """
        <session>
            <prompt>Write a story about robots</prompt>
            <notes>I need to think about this</notes>
            <ask>What type of robot?</ask>
            <response>Friendly cleaning robot</response>
            <submit>A story about a friendly cleaning robot</submit>
        </session>
        """

        # Should not raise an exception for valid XML
        xml_service.validate_session_xml(xml, is_leaf=False)

    def test_validate_empty_xml_fails(self, xml_service):
        """Test validation fails for empty XML."""
        xml = ""

        with pytest.raises(ValueError):
            xml_service.validate_session_xml(xml, is_leaf=True)

    def test_validate_non_session_root_fails(self, xml_service):
        """Test validation fails for non-session root."""
        xml = """
        <document>
            <prompt>Test</prompt>
            <submit>Result</submit>
        </document>
        """

        with pytest.raises(ValueError):
            xml_service.validate_session_xml(xml, is_leaf=True)

    def test_partial_xml_validation_leaf_is_not_valid(self, xml_service):
        """Test partial leaf sessions (just prompt) are not valid."""
        xml = """
        <session>
            <prompt>Test</prompt>
        """

        with pytest.raises(ValueError, match="Leaf session must have 2 events, got 1"):
            xml_service.validate_session_xml(xml, is_leaf=True)

    def test_xml_with_attributes_valid(self, xml_service):
        """Test validation handles XML with attributes correctly."""
        xml = """
        <session id="123">
            <prompt type="story">Write a story</prompt>
            <submit format="text">Story content here</submit>
        </session>
        """

        # Should not raise exception for XML with attributes
        xml_service.validate_session_xml(xml, is_leaf=True)

    def test_xml_with_response_id_elements_valid(self, xml_service):
        """Test validation handles response-id elements correctly."""
        xml = """
        <session>
            <prompt>Main task</prompt>
            <ask>First question</ask>
            <response-id>1</response-id>
            <response>First answer</response>
            <submit>Final result</submit>
        </session>
        """

        # Should not raise exception for XML with response-id elements
        xml_service.validate_session_xml(xml, is_leaf=False)

    def test_format_sessions_for_prompt_with_partial_prompt(self, xml_service):
        """Test formatting examples plus partial session starting with prompt."""
        # Example session
        example_session = Session(session_id=0)
        example_session.add_event(PromptEvent("Write a story about robots"))
        example_session.add_event(SubmitEvent("Once upon a time, there was a robot..."))

        # Partial session to continue from
        partial_session = Session(session_id=1)
        partial_session.add_event(PromptEvent("Write about space"))

        result = xml_service.format_sessions_for_prompt(
            [example_session], partial_session
        )

        expected = """<sessions>
  <session>
    <prompt>Write a story about robots</prompt>
    <submit>Once upon a time, there was a robot...</submit>
  </session>
  <session>
    <prompt>Write about space</prompt>
    <"""

        assert result == expected

    def test_format_sessions_for_prompt_multiple_examples(self, xml_service):
        """Test formatting multiple example sessions with partial session."""
        session1 = Session(session_id=0)
        session1.add_event(PromptEvent("Write a story about robots"))
        session1.add_event(AskEvent("What type of robot?"))
        session1.add_event(ResponseEvent("Friendly cleaning robot"))
        session1.add_event(SubmitEvent("A story about a friendly cleaning robot"))

        session2 = Session(session_id=1)
        session2.add_event(PromptEvent("What type of robot?"))
        session2.add_event(SubmitEvent("Friendly cleaning robot"))

        # Partial session to continue from
        partial_session = Session(session_id=2)
        partial_session.add_event(PromptEvent("Write about aliens"))

        result = xml_service.format_sessions_for_prompt(
            [session1, session2], partial_session
        )

        expected = """<sessions>
  <session>
    <prompt>Write a story about robots</prompt>
    <ask>What type of robot?</ask>
    <response>Friendly cleaning robot</response>
    <submit>A story about a friendly cleaning robot</submit>
  </session>
  <session>
    <prompt>What type of robot?</prompt>
    <submit>Friendly cleaning robot</submit>
  </session>
  <session>
    <prompt>Write about aliens</prompt>
    <"""

        assert result == expected

    def test_format_sessions_for_prompt_no_examples(self, xml_service):
        """Test formatting with no examples, just partial session."""
        # Partial session to continue from
        partial_session = Session(session_id=0)
        partial_session.add_event(PromptEvent("Write a story"))

        result = xml_service.format_sessions_for_prompt([], partial_session)

        expected = """<sessions>
  <session>
    <prompt>Write a story</prompt>
    <"""

        assert result == expected

    def test_format_sessions_for_prompt_preserves_content(self, xml_service):
        """Test that content with special characters is preserved."""
        session = Session(session_id=0)
        session.add_event(PromptEvent('Write a story with "quotes" and <tags>'))
        session.add_event(SubmitEvent("Once upon a time... & they lived happily."))

        # Partial session with special characters
        partial_session = Session(session_id=1)
        partial_session.add_event(PromptEvent('More "quotes" & <symbols>'))

        result = xml_service.format_sessions_for_prompt([session], partial_session)

        expected = """<sessions>
  <session>
    <prompt>Write a story with "quotes" and &lt;tags&gt;</prompt>
    <submit>Once upon a time... &amp; they lived happily.</submit>
  </session>
  <session>
    <prompt>More "quotes" &amp; &lt;symbols&gt;</prompt>
    <"""

        assert result == expected

    def test_format_sessions_for_prompt_partial_ending_with_response(self, xml_service):
        """Test formatting with partial session ending with response for LLM to continue."""
        # Example session
        example_session = Session(session_id=0)
        example_session.add_event(PromptEvent("Write a story about robots"))
        example_session.add_event(SubmitEvent("A story about robots"))

        # Partial session ending with response
        partial_session = Session(session_id=1)
        partial_session.add_event(PromptEvent("Write about space"))
        partial_session.add_event(AskEvent("What should happen first?"))
        partial_session.add_event(ResponseEvent("A spaceship lands"))

        result = xml_service.format_sessions_for_prompt(
            [example_session], partial_session
        )

        expected = """<sessions>
  <session>
    <prompt>Write a story about robots</prompt>
    <submit>A story about robots</submit>
  </session>
  <session>
    <prompt>Write about space</prompt>
    <ask>What should happen first?</ask>
    <response>A spaceship lands</response>
    <"""

        assert result == expected
