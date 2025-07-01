"""Tests for node selection from session trees."""

import tempfile
from pathlib import Path
import xml.etree.ElementTree as ET
import pytest

from src.data_collection.node_selector import NodeSelector


class TestNodeSelector:
    """Test node selection functionality."""

    def create_sample_session_xml(self, path: Path, session_id: int = 0):
        """Helper to create a sample session XML file."""
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<sessions>
  <final-response>Final response text</final-response>
  <session>
    <id>{session_id}</id>
    <prompt>Write a story about a robot</prompt>
    <ask>Generate a story about a friendly robot</ask>
    <response-id>1</response-id>
    <response>Once upon a time...</response>
    <submit>The complete robot story</submit>
  </session>
  <session>
    <id>1</id>
    <prompt>Generate a story about a friendly robot</prompt>
    <submit>Once upon a time...</submit>
  </session>
  <session>
    <id>2</id>
    <prompt>Add more details about the robot's personality</prompt>
    <submit>The robot was kind and helpful...</submit>
  </session>
</sessions>"""
        path.write_text(xml_content)

    def test_selects_nodes_randomly_from_multiple_sessions(self):
        """Test that nodes are selected randomly across different session files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sample-sessions"
            sessions_dir.mkdir()

            # Create multiple session files
            for i in range(5):
                session_file = sessions_dir / f"{i+1}-test-prompt-{i}.xml"
                self.create_sample_session_xml(session_file)

            selector = NodeSelector(random_seed=42)  # Fixed seed for reproducibility
            selected = selector.select_nodes_for_examples(sessions_dir, 3)

            assert len(selected) == 3

            # Each selection should have (filename, node_id, prompt_text)
            for filename, node_id, prompt_text in selected:
                assert filename.endswith(".xml")
                assert isinstance(node_id, int)
                assert isinstance(prompt_text, str)
                assert len(prompt_text) > 0

    def test_can_select_both_leaf_and_parent_nodes(self):
        """Test that selection includes both leaf and parent nodes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sample-sessions"
            sessions_dir.mkdir()

            # Create a session with clear parent/leaf structure
            session_file = sessions_dir / "1-test.xml"
            xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<sessions>
  <session>
    <id>0</id>
    <prompt>Parent task that needs breakdown</prompt>
    <ask>Break this down into subtasks</ask>
    <response-id>1</response-id>
    <response>Subtask 1 result</response>
    <response-id>2</response-id>
    <response>Subtask 2 result</response>
    <submit>Combined result</submit>
  </session>
  <session>
    <id>1</id>
    <prompt>Break this down into subtasks</prompt>
    <ask>Do subtask 1</ask>
    <response-id>3</response-id>
    <response>Subtask 1.1 result</response>
    <submit>Subtask 1 result</submit>
  </session>
  <session>
    <id>2</id>
    <prompt>Handle subtask 2</prompt>
    <submit>Subtask 2 result</submit>
  </session>
  <session>
    <id>3</id>
    <prompt>Do subtask 1</prompt>
    <submit>Subtask 1.1 result</submit>
  </session>
</sessions>"""
            session_file.write_text(xml_content)

            selector = NodeSelector()

            # Select many times to ensure we get variety
            all_node_ids = []
            for _ in range(10):
                selected = selector.select_nodes_for_examples(sessions_dir, 1)
                all_node_ids.append(selected[0][1])

            # Should have selected different node IDs
            unique_ids = set(all_node_ids)
            assert len(unique_ids) > 1

            # Should include both parent nodes (0, 1) and leaf nodes (2, 3)
            assert any(node_id in [0, 1] for node_id in unique_ids)  # Has parent
            assert any(node_id in [2, 3] for node_id in unique_ids)  # Has leaf

    def test_handles_insufficient_files_gracefully(self):
        """Test error when requesting more files than available."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sample-sessions"
            sessions_dir.mkdir()

            # Create 2 session files with 3 nodes each
            self.create_sample_session_xml(sessions_dir / f"1-test.xml")
            self.create_sample_session_xml(sessions_dir / f"2-test.xml")

            selector = NodeSelector()

            # Can select 2 nodes from each file
            selected = selector.select_nodes_for_examples(sessions_dir, 2)
            assert len(selected) == 2

            # Cannot select 3 nodes
            with pytest.raises(ValueError, match="enough files"):
                selector.select_nodes_for_examples(sessions_dir, 3)

    def test_extracts_correct_prompt_text_from_nodes(self):
        """Test that the correct prompt text is extracted for each node."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sample-sessions"
            sessions_dir.mkdir()

            # Create 3 separate files, each with 1 session
            for n in range(1, 4):
                session_file = sessions_dir / f"{n}-test.xml"
                xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<sessions>
  <session>
    <id>0</id>
    <prompt>This is prompt {n}</prompt>
    <submit>Result {n}</submit>
  </session>
</sessions>"""
                session_file.write_text(xml_content)

            selector = NodeSelector(random_seed=42)

            # Get one node from each file
            selected = selector.select_nodes_for_examples(sessions_dir, 3)
            assert len(selected) == 3

            # Verify we get one node from each file
            filenames = {filename for filename, _, _ in selected}
            assert len(filenames) == 3  # Three different files

            # Verify prompt text format
            for _, node_id, prompt_text in selected:
                assert prompt_text.startswith("This is prompt")
                assert node_id == 0  # All sessions should have root ID 0

    def test_handles_malformed_xml_gracefully(self):
        """Test appropriate error handling for malformed XML."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sample-sessions"
            sessions_dir.mkdir()

            # Create malformed XML
            bad_file = sessions_dir / "1-bad.xml"
            bad_file.write_text("<unclosed_tag>")

            selector = NodeSelector()

            with pytest.raises(ValueError, match="XML parsing error"):
                selector.select_nodes_for_examples(sessions_dir, 1)

    def test_filename_preservation_in_results(self):
        """Test that original filenames are preserved in selection results."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sessions_dir = Path(tmpdir) / "sample-sessions"
            sessions_dir.mkdir()

            # Create files with specific names
            filenames = [
                "123-what-would-happen-if-the-presi.xml",
                "456-you-walk-into-the-grocery-stor.xml",
            ]

            for filename in filenames:
                session_file = sessions_dir / filename
                self.create_sample_session_xml(session_file)

            selector = NodeSelector()
            selected = selector.select_nodes_for_examples(sessions_dir, 2)

            assert set(filenames) == set(filename for filename, _, _ in selected)
