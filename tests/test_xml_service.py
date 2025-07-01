"""Tests for unified XML service."""

import tempfile
from pathlib import Path
import pytest

from src.xml_service import XmlService
from src.session import Session, PromptEvent, AskEvent, ResponseEvent, SubmitEvent


class TestXmlService:
    """Test the unified XML service that replaces direct ElementTree usage."""

    @pytest.fixture
    def xml_service(self):
        """Create XML service instance."""
        return XmlService()

    @pytest.fixture
    def sample_session_file(self):
        """Create a sample session XML file for testing."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
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
            session_content = f"""<?xml version="1.0" encoding="UTF-8"?>
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

    def test_parse_sessions_file_handles_malformed_xml(self, xml_service):
        """Test graceful handling of malformed XML."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write("<unclosed_tag>malformed")
            malformed_file = Path(f.name)

        with pytest.raises(ValueError, match="XML parsing error"):
            xml_service.parse_sessions_file(malformed_file)

    def test_parse_sessions_file_handles_failed_sessions(self, xml_service):
        """Test parsing of XML with FAILED sessions."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
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
        # Valid leaf session
        valid_leaf = "<session><prompt>Test</prompt><submit>Result</submit></session>"
        assert xml_service.validate_session_xml(valid_leaf, is_leaf=True)

        # Invalid session (missing submit)
        invalid_session = "<session><prompt>Test</prompt></session>"
        assert not xml_service.validate_session_xml(invalid_session, is_leaf=True)

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
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
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
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
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
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<sessions>
</sessions>"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False) as f:
            f.write(xml_content)
            file_path = Path(f.name)

        sessions = xml_service.parse_sessions_file(file_path)
        assert len(sessions) == 0

    def test_validate_session_xml_delegates_to_validator(self, xml_service):
        """Test that validation properly delegates to XmlValidator."""
        valid_xml = "<session><prompt>Test</prompt><submit>Result</submit></session>"
        invalid_xml = "<session><prompt>Test</prompt></session>"  # Missing submit

        # Should delegate to existing XmlValidator
        assert xml_service.validate_session_xml(valid_xml, is_leaf=True) == True
        assert xml_service.validate_session_xml(invalid_xml, is_leaf=True) == False

        # Test partial validation
        partial_xml = "<session><prompt>Test</prompt><ask>Question</ask>"
        assert (
            xml_service.validate_session_xml(
                partial_xml, is_leaf=False, is_partial=True
            )
            == True
        )

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
        assert xml_output.startswith('<?xml version="1.0" encoding="UTF-8"?>')

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
        assert content.startswith('<?xml version="1.0" encoding="UTF-8"?>')
        assert "<sessions />" in content
        assert "<session>" not in content  # No session elements

        # Should be able to parse back the empty file
        sessions = xml_service.parse_sessions_file(output_path)
        assert len(sessions) == 0
