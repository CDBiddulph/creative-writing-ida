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
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
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

    def test_parse_sessions_file_returns_session_objects(self, xml_service, sample_session_file):
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

    def test_parse_session_nodes_extracts_node_info(self, xml_service, sample_session_file):
        """Test that parse_session_nodes extracts (filename, node_id, prompt) tuples."""
        nodes = xml_service.parse_session_nodes(sample_session_file)
        
        assert len(nodes) == 2
        
        # Check that we get tuples with correct structure
        for filename, node_id, prompt_text in nodes:
            assert filename == sample_session_file.name
            assert isinstance(node_id, int)
            assert isinstance(prompt_text, str)
            assert len(prompt_text) > 0
        
        # Check specific content
        node_ids = [node_id for _, node_id, _ in nodes]
        prompts = [prompt for _, _, prompt in nodes]
        
        assert 0 in node_ids
        assert 1 in node_ids
        assert "Write a story about robots" in prompts
        assert "What type of robot?" in prompts

    def test_extract_session_examples_for_leaf_type(self, xml_service, sessions_directory):
        """Test extracting leaf examples from session files."""
        examples = xml_service.extract_session_examples(sessions_directory, "leaf")
        
        assert len(examples) == 3  # One from each file
        
        for example in examples:
            assert "prompt" in example
            assert "submit" in example
            assert isinstance(example["prompt"], str)
            assert isinstance(example["submit"], str)

    def test_extract_session_examples_for_parent_type(self, xml_service):
        """Test extracting parent examples from session files."""
        # Create a session file with parent structure
        tmpdir = Path(tempfile.mkdtemp())
        parent_session_content = """<?xml version="1.0" encoding="UTF-8"?>
<sessions>
  <session>
    <id>0</id>
    <prompt>Complex task</prompt>
    <ask>What approach?</ask>
    <response>Step by step</response>
    <ask>What first?</ask>
    <response>Plan the work</response>
    <submit>Planned approach with steps</submit>
  </session>
  <session>
    <id>1</id>
    <prompt>What approach?</prompt>
    <submit>Step by step</submit>
  </session>
</sessions>"""
        session_file = tmpdir / "parent-session.xml"
        session_file.write_text(parent_session_content)
        
        examples = xml_service.extract_session_examples(tmpdir, "parent")
        
        assert len(examples) == 1
        example = examples[0]
        
        assert example["prompt"] == "Complex task"
        assert example["submit"] == "Planned approach with steps"
        assert "ask" in example
        assert "response" in example
        assert isinstance(example["ask"], list)
        assert isinstance(example["response"], list)
        assert len(example["ask"]) == 2
        assert len(example["response"]) == 2

    def test_parse_sessions_file_handles_malformed_xml(self, xml_service):
        """Test graceful handling of malformed XML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write("<unclosed_tag>malformed")
            malformed_file = Path(f.name)
        
        with pytest.raises(ValueError, match="XML parsing error"):
            xml_service.parse_sessions_file(malformed_file)

    def test_parse_session_nodes_handles_missing_elements(self, xml_service):
        """Test handling of XML with missing id or prompt elements."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<sessions>
  <session>
    <id>0</id>
    <!-- Missing prompt -->
    <submit>Response without prompt</submit>
  </session>
  <session>
    <!-- Missing id -->
    <prompt>Prompt without id</prompt>
    <submit>Response</submit>
  </session>
</sessions>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            file_path = Path(f.name)
        
        # Should skip sessions with missing required elements
        nodes = xml_service.parse_session_nodes(file_path)
        assert len(nodes) == 0

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
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            file_path = Path(f.name)
        
        sessions = xml_service.parse_sessions_file(file_path)
        assert len(sessions) == 1
        
        session = sessions[0]
        assert session.is_failed is False  # XML parsing shouldn't automatically mark as failed
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
        xml_output = xml_service.format_sessions_to_xml(sessions, final_response="Final result")
        
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
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            file_path = Path(f.name)
        
        final_response = xml_service.extract_final_response(file_path)
        assert final_response is None

    def test_count_sessions_in_file(self, xml_service, sample_session_file):
        """Test counting number of sessions in a file."""
        count = xml_service.count_sessions(sample_session_file)
        assert count == 2

    def test_extract_session_by_id(self, xml_service, sample_session_file):
        """Test extracting a specific session by ID."""
        session = xml_service.extract_session_by_id(sample_session_file, session_id=1)
        
        assert session is not None
        assert session.session_id == 1
        assert len(session.events) == 2
        assert session.events[0].text == "What type of robot?"

    def test_extract_session_by_id_not_found(self, xml_service, sample_session_file):
        """Test that non-existent session ID returns None."""
        session = xml_service.extract_session_by_id(sample_session_file, session_id=999)
        assert session is None

    def test_parse_sessions_file_preserves_event_order(self, xml_service):
        """Test that event order is preserved when parsing sessions."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<sessions>
  <session>
    <id>0</id>
    <prompt>Main task</prompt>
    <notes>Initial thoughts</notes>
    <ask>First question</ask>
    <response>First answer</response>
    <ask>Second question</ask>
    <response>Second answer</response>
    <submit>Final result</submit>
  </session>
</sessions>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            file_path = Path(f.name)
        
        sessions = xml_service.parse_sessions_file(file_path)
        session = sessions[0]
        
        # Check event order is preserved
        event_types = [type(event).__name__ for event in session.events]
        expected_order = ['PromptEvent', 'AskEvent', 'ResponseEvent', 'AskEvent', 'ResponseEvent', 'SubmitEvent']
        assert event_types == expected_order

    def test_parse_sessions_file_handles_empty_file(self, xml_service):
        """Test handling of empty sessions file."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<sessions>
</sessions>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            file_path = Path(f.name)
        
        sessions = xml_service.parse_sessions_file(file_path)
        assert len(sessions) == 0

    def test_extract_session_examples_filters_by_max_count(self, xml_service, sessions_directory):
        """Test that extract_session_examples respects maximum count limits."""
        # Create many session files
        for i in range(10):
            session_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<sessions>
  <session>
    <id>0</id>
    <prompt>Prompt {i}</prompt>
    <submit>Response {i}</submit>
  </session>
</sessions>"""
            session_file = sessions_directory / f"extra-{i}.xml"
            session_file.write_text(session_content)
        
        # Extract with limit
        examples = xml_service.extract_session_examples(sessions_directory, "leaf", max_examples=5)
        assert len(examples) == 5

    def test_parse_session_nodes_handles_empty_directory(self, xml_service):
        """Test node parsing with empty directory."""
        tmpdir = Path(tempfile.mkdtemp())
        nodes = xml_service.parse_session_nodes(tmpdir)
        assert len(nodes) == 0

    def test_validate_session_xml_delegates_to_validator(self, xml_service):
        """Test that validation properly delegates to XmlValidator."""
        valid_xml = "<session><prompt>Test</prompt><submit>Result</submit></session>"
        invalid_xml = "<session><prompt>Test</prompt></session>"  # Missing submit
        
        # Should delegate to existing XmlValidator
        assert xml_service.validate_session_xml(valid_xml, is_leaf=True) == True
        assert xml_service.validate_session_xml(invalid_xml, is_leaf=True) == False
        
        # Test partial validation
        partial_xml = "<session><prompt>Test</prompt><ask>Question</ask>"
        assert xml_service.validate_session_xml(partial_xml, is_leaf=False, is_partial=True) == True

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
        
        # Should include response-id for parent session
        assert "<response-id>1</response-id>" in xml_output
        
        # Should include final-response
        assert "<final-response>" in xml_output

    def test_extract_session_examples_handles_malformed_files_gracefully(self, xml_service):
        """Test that malformed files are skipped during example extraction."""
        tmpdir = Path(tempfile.mkdtemp())
        
        # Create one good file
        good_file = tmpdir / "good.xml"
        good_file.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<sessions>
  <session>
    <id>0</id>
    <prompt>Good prompt</prompt>
    <submit>Good result</submit>
  </session>
</sessions>""")
        
        # Create one malformed file
        bad_file = tmpdir / "bad.xml"
        bad_file.write_text("<unclosed>malformed")
        
        # Should extract from good file, skip bad file
        examples = xml_service.extract_session_examples(tmpdir, "leaf")
        assert len(examples) == 1
        assert examples[0]["prompt"] == "Good prompt"

    def test_count_sessions_with_mixed_session_types(self, xml_service):
        """Test counting sessions in files with both leaf and parent sessions."""
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<sessions>
  <final-response>Complete result</final-response>
  <session>
    <id>0</id>
    <prompt>Parent task</prompt>
    <ask>Break this down</ask>
    <response-id>1</response-id>
    <response>Subtask result</response>
    <submit>Combined result</submit>
  </session>
  <session>
    <id>1</id>
    <prompt>Break this down</prompt>
    <submit>Subtask result</submit>
  </session>
</sessions>"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_content)
            file_path = Path(f.name)
        
        count = xml_service.count_sessions(file_path)
        assert count == 2

    def test_parse_session_nodes_extracts_from_multiple_files(self, xml_service, sessions_directory):
        """Test that parse_session_nodes works across multiple files in directory."""
        # sessions_directory fixture creates 3 files with 2 sessions each
        nodes = xml_service.parse_session_nodes(sessions_directory)
        
        # Should find 6 total nodes (2 per file × 3 files)
        assert len(nodes) == 6
        
        # Should have different filenames
        filenames = {node[0] for node in nodes}
        assert len(filenames) == 3  # 3 different files
        
        # Should have variety of node IDs
        node_ids = {node[1] for node in nodes}
        assert 0 in node_ids
        assert 1 in node_ids

    def test_extract_session_examples_preserves_parent_structure(self, xml_service):
        """Test that parent examples preserve ask/response structure."""
        tmpdir = Path(tempfile.mkdtemp())
        parent_file = tmpdir / "parent.xml"
        parent_file.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<sessions>
  <session>
    <id>0</id>
    <prompt>Complex workflow</prompt>
    <notes>Planning phase</notes>
    <ask>What's the first step?</ask>
    <response>Gather requirements</response>
    <notes>Execution phase</notes>
    <ask>How to implement?</ask>
    <response>Build incrementally</response>
    <ask>When to deploy?</ask>
    <response>After testing</response>
    <submit>Complete workflow executed</submit>
  </session>
</sessions>""")
        
        examples = xml_service.extract_session_examples(tmpdir, "parent")
        assert len(examples) == 1
        
        example = examples[0]
        assert example["prompt"] == "Complex workflow"
        assert example["submit"] == "Complete workflow executed"
        
        # Should preserve multiple asks and responses in order
        assert len(example["ask"]) == 3
        assert len(example["response"]) == 3
        assert example["ask"][0] == "What's the first step?"
        assert example["response"][0] == "Gather requirements"
        assert example["ask"][2] == "When to deploy?"
        assert example["response"][2] == "After testing"
        
        # Should handle notes if present
        if "notes" in example:
            assert isinstance(example["notes"], list)

    def test_parse_sessions_file_ignores_metadata_elements(self, xml_service, sample_session_file):
        """Test that parsing ignores file-level metadata like final-response."""
        sessions = xml_service.parse_sessions_file(sample_session_file)
        
        # Should have parsed sessions but ignored final-response and response-id elements
        assert len(sessions) == 2
        
        # Sessions should not contain metadata elements like response-id
        for session in sessions:
            for event in session.events:
                # Events should only be the core session types
                assert isinstance(event, (PromptEvent, AskEvent, ResponseEvent, SubmitEvent))

