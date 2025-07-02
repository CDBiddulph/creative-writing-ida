"""Tests for example aggregation and formatting."""

import tempfile
from pathlib import Path
import xml.etree.ElementTree as ET
import pytest

from src.data_collection.example_aggregator import ExampleAggregator
from src.data_collection.config import DataCollectionConfig


class TestExampleAggregator:
    """Test example extraction and aggregation functionality."""

    @pytest.fixture
    def mock_config(self):
        """Create a mock data collection config."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create seed files
            seed_leaf = Path(tmpdir) / "seed_leaf.xml"
            seed_parent = Path(tmpdir) / "seed_parent.xml"

            seed_leaf.write_text(
                """<?xml version='1.0' encoding='utf-8'?>
<sessions>
  <session>
    <prompt>Seed leaf prompt</prompt>
    <submit>Seed leaf response</submit>
  </session>
</sessions>"""
            )

            seed_parent.write_text(
                """<?xml version='1.0' encoding='utf-8'?>
<sessions>
  <session>
    <prompt>Seed parent prompt</prompt>
    <ask>Break this down</ask>
    <response>Subtask result</response>
    <submit>Combined result</submit>
  </session>
</sessions>"""
            )

            yield DataCollectionConfig(
                experiment_id="test_exp",
                leaf_examples_per_iteration=5,
                parent_examples_per_iteration=3,
                max_parent_examples=20,
                max_iterations=3,
                sample_max_depth=2,
                parent_max_depth=1,
                leaf_max_depth=3,
                writing_prompts_path="prompts.txt",
                seed_leaf_examples=str(seed_leaf),
                seed_parent_examples=str(seed_parent),
                parent_total_char_limit=2000,
                parent_submit_char_limit=500,
                web_ui_port=5000,
                model="test-model",
                temperature=0.7,
                max_tokens=1000,
                leaf_readme_path="leaf_readme.md",
                parent_readme_path="parent_readme.md",
                keep_seed_parent_examples=False,
                shuffle_examples=True,
            )

    def create_leaf_session_xml(self, path: Path, prompt: str, final_response: str):
        """Create a leaf session XML file."""
        xml_content = f"""<?xml version='1.0' encoding='utf-8'?>
<sessions>
  <final-response>{final_response}</final-response>
  <session>
    <id>0</id>
    <prompt>{prompt}</prompt>
    <submit>This will have placeholders like $PROMPT</submit>
  </session>
  <session>
    <id>1</id>
    <prompt>Child prompt</prompt>
    <submit>Child response</submit>
  </session>
</sessions>"""
        path.write_text(xml_content)

    def create_parent_session_xml(self, path: Path):
        """Create a parent session XML file."""
        xml_content = """<?xml version='1.0' encoding='utf-8'?>
<sessions>
  <final-response>Final response with placeholders resolved</final-response>
  <session>
    <id>0</id>
    <prompt>Write a complex story</prompt>
    <notes>I need to break this down</notes>
    <ask>Generate the first part about $PROMPT</ask>
    <response-id>1</response-id>
    <response>Here's the first part of the story...</response>
    <notes>Good start, now the ending</notes>
    <ask>Now create an ending that references $RESPONSE1</ask>
    <response-id>2</response-id>
    <response>And here's how it ends...</response>
    <submit>Combining $RESPONSE1 and $RESPONSE2 into final story</submit>
  </session>
  <session>
    <id>1</id>
    <prompt>Generate the first part about Write a complex story</prompt>
    <submit>Here's the first part of the story...</submit>
  </session>
  <session>
    <id>2</id>
    <prompt>Now create an ending that references Here's the first part of the story...</prompt>
    <submit>And here's how it ends...</submit>
  </session>
</sessions>"""
        path.write_text(xml_content)

    def test_copies_seed_examples_for_iteration_zero(self, mock_config):
        """Test that iteration 0 copies seed example files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create seed examples
            examples_dir = Path(tmpdir) / "examples"
            examples_dir.mkdir()
            seed_leaf = examples_dir / "leaf.xml"
            seed_parent = examples_dir / "parent.xml"
            seed_leaf.write_text("<sessions><session>leaf seed</session></sessions>")
            seed_parent.write_text(
                "<sessions><session>parent seed</session></sessions>"
            )

            # Update config with correct paths
            mock_config.seed_leaf_examples = str(seed_leaf)
            mock_config.seed_parent_examples = str(seed_parent)

            # Create iteration directory
            exp_path = Path(tmpdir) / "experiment"
            exp_path.mkdir()
            iter_path = exp_path / "iteration_0"
            iter_path.mkdir()
            (iter_path / "examples").mkdir()

            aggregator = ExampleAggregator(mock_config)
            aggregator.create_examples_for_iteration(iter_path, 0, exp_path)

            # Verify files were copied
            assert (iter_path / "examples" / "leaf_examples.xml").exists()
            assert (iter_path / "examples" / "parent_examples.xml").exists()

            # Verify content matches
            leaf_content = (iter_path / "examples" / "leaf_examples.xml").read_text()
            assert "leaf seed" in leaf_content
            parent_content = (
                iter_path / "examples" / "parent_examples.xml"
            ).read_text()
            assert "parent seed" in parent_content

    def test_extracts_leaf_examples_correctly(self, mock_config):
        """Test extraction of leaf examples from session trees."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exp_path = Path(tmpdir) / "experiment"
            exp_path.mkdir()

            # Create iteration 0 with leaf sessions
            iter0_path = exp_path / "iteration_0"
            iter0_path.mkdir()
            leaf_sessions = iter0_path / "leaf-sessions"
            leaf_sessions.mkdir()

            # Create multiple leaf session files
            self.create_leaf_session_xml(
                leaf_sessions / "1-0-first-prompt.xml",
                "First prompt text",
                "First final response",
            )
            self.create_leaf_session_xml(
                leaf_sessions / "2-1-second-prompt.xml",
                "Second prompt text",
                "Second final response",
            )

            # Create iteration 1 structure
            iter1_path = exp_path / "iteration_1"
            iter1_path.mkdir()
            (iter1_path / "examples").mkdir()

            aggregator = ExampleAggregator(mock_config)
            aggregator.create_examples_for_iteration(iter1_path, 1, exp_path)

            # Verify leaf examples were created
            leaf_examples = iter1_path / "examples" / "leaf_examples.xml"
            assert leaf_examples.exists()

            # Parse and verify content
            tree = ET.parse(leaf_examples)
            sessions = tree.findall(".//session")
            assert len(sessions) == 2

            # Verify prompts and submits (final-response becomes submit)
            prompts = [s.find("prompt").text for s in sessions]
            submits = [s.find("submit").text for s in sessions]

            expected_prompts = ["First prompt text", "Second prompt text"]
            expected_submits = ["First final response", "Second final response"]
            assert prompts == expected_prompts
            assert submits == expected_submits

    def test_leaf_examples_only_include_prompt_and_submit(self, mock_config):
        """Test that leaf examples don't include notes, asks, or responses."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exp_path = Path(tmpdir) / "experiment"
            exp_path.mkdir()

            # Create iteration 0 with a complex leaf session
            iter0_path = exp_path / "iteration_0"
            iter0_path.mkdir()
            leaf_sessions = iter0_path / "leaf-sessions"
            leaf_sessions.mkdir()

            # Create leaf session that might have complex structure
            complex_xml = """<?xml version='1.0' encoding='utf-8'?>
<sessions>
  <final-response>This is the final answer</final-response>
  <session>
    <id>0</id>
    <prompt>Complex task</prompt>
    <notes>Internal thinking</notes>
    <ask>Break it down</ask>
    <response>Subtask result</response>
    <submit>Placeholder submit</submit>
  </session>
</sessions>"""
            (leaf_sessions / "1-0-complex.xml").write_text(complex_xml)

            # Create iteration 1
            iter1_path = exp_path / "iteration_1"
            iter1_path.mkdir()
            (iter1_path / "examples").mkdir()

            aggregator = ExampleAggregator(mock_config)
            aggregator.create_examples_for_iteration(iter1_path, 1, exp_path)

            # Parse result
            leaf_examples = iter1_path / "examples" / "leaf_examples.xml"
            tree = ET.parse(leaf_examples)
            session = tree.find(".//session")

            # Should only have prompt and submit
            assert session.find("prompt") is not None
            assert session.find("submit") is not None

            # Should NOT have notes, ask, or response
            assert session.find("notes") is None
            assert session.find("ask") is None
            assert session.find("response") is None

            # Submit should be from final-response, not original submit
            assert session.find("submit").text == "This is the final answer"

    def test_parent_examples_preserve_full_structure(self, mock_config):
        """Test that parent examples keep all session elements."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exp_path = Path(tmpdir) / "experiment"
            exp_path.mkdir()

            # Create iteration 0 with parent sessions
            iter0_path = exp_path / "iteration_0"
            iter0_path.mkdir()
            parent_sessions = iter0_path / "parent-sessions"
            parent_sessions.mkdir()

            # Create parent session
            self.create_parent_session_xml(parent_sessions / "1-0-story.xml")

            # Create iteration 1
            iter1_path = exp_path / "iteration_1"
            iter1_path.mkdir()
            (iter1_path / "examples").mkdir()

            # Need to stub leaf examples too
            (iter0_path / "leaf-sessions").mkdir()

            aggregator = ExampleAggregator(mock_config)
            aggregator.create_examples_for_iteration(iter1_path, 1, exp_path)

            # Parse parent examples
            parent_examples = iter1_path / "examples" / "parent_examples.xml"
            tree = ET.parse(parent_examples)
            session = tree.find(".//session")

            # Verify all elements are preserved
            assert session.find("prompt").text == "Write a complex story"
            assert len(session.findall("notes")) == 2
            assert len(session.findall("ask")) == 2
            assert len(session.findall("response")) == 2
            assert session.find("submit") is not None

            # Verify placeholders are preserved in asks
            asks = [ask.text for ask in session.findall("ask")]
            assert any("$PROMPT" in ask for ask in asks)
            assert any("$RESPONSE1" in ask for ask in asks)

    def test_parent_examples_accumulate_across_iterations(self, mock_config):
        """Test that parent examples accumulate while leaf examples reset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exp_path = Path(tmpdir) / "experiment"
            exp_path.mkdir()

            # Create iterations 0, 1, 2 with parent sessions
            for i in range(3):
                iter_path = exp_path / f"iteration_{i}"
                iter_path.mkdir()
                parent_sessions = iter_path / "parent-sessions"
                parent_sessions.mkdir()
                leaf_sessions = iter_path / "leaf-sessions"
                leaf_sessions.mkdir()

                # Add unique parent session for each iteration
                parent_xml = f"""<?xml version='1.0' encoding='utf-8'?>
<sessions>
  <session>
    <id>0</id>
    <prompt>Parent prompt iteration {i}</prompt>
    <ask>Task for iteration {i}</ask>
    <response>Response {i}</response>
    <submit>Submit {i}</submit>
  </session>
</sessions>"""
                (parent_sessions / f"1-0-iter{i}.xml").write_text(parent_xml)

                # Add leaf session
                self.create_leaf_session_xml(
                    leaf_sessions / f"1-0-leaf{i}.xml",
                    f"Leaf prompt {i}",
                    f"Leaf response {i}",
                )

            # Create iteration 3 and aggregate
            iter3_path = exp_path / "iteration_3"
            iter3_path.mkdir()
            (iter3_path / "examples").mkdir()

            aggregator = ExampleAggregator(mock_config)
            aggregator.create_examples_for_iteration(iter3_path, 3, exp_path)

            # Check parent examples - should have all 3
            parent_tree = ET.parse(iter3_path / "examples" / "parent_examples.xml")
            parent_sessions = parent_tree.findall(".//session")
            assert len(parent_sessions) == 3

            parent_prompts = [s.find("prompt").text for s in parent_sessions]
            expected_parent_prompts = [
                "Parent prompt iteration 0",
                "Parent prompt iteration 1",
                "Parent prompt iteration 2",
            ]
            assert parent_prompts == expected_parent_prompts

            # Check leaf examples - should only have latest
            leaf_tree = ET.parse(iter3_path / "examples" / "leaf_examples.xml")
            leaf_sessions = leaf_tree.findall(".//session")
            assert len(leaf_sessions) == 1
            assert leaf_sessions[0].find("prompt").text == "Leaf prompt 2"

    def test_handles_max_parent_examples_limit(self, mock_config):
        """Test that parent accumulation stops at max_parent_examples."""
        mock_config.max_parent_examples = 2  # Set low limit

        with tempfile.TemporaryDirectory() as tmpdir:
            exp_path = Path(tmpdir) / "experiment"
            exp_path.mkdir()

            # Create 3 iterations with parent sessions
            for i in range(3):
                iter_path = exp_path / f"iteration_{i}"
                iter_path.mkdir()
                parent_sessions = iter_path / "parent-sessions"
                parent_sessions.mkdir()
                (iter_path / "leaf-sessions").mkdir()

                parent_xml = f"""<?xml version='1.0' encoding='utf-8'?>
<sessions>
  <session>
    <id>0</id>
    <prompt>Parent {i}</prompt>
    <submit>Submit {i}</submit>
  </session>
</sessions>"""
                (parent_sessions / f"1-0-p{i}.xml").write_text(parent_xml)

            # Aggregate for iteration 3
            iter3_path = exp_path / "iteration_3"
            iter3_path.mkdir()
            (iter3_path / "examples").mkdir()

            aggregator = ExampleAggregator(mock_config)
            aggregator.create_examples_for_iteration(iter3_path, 3, exp_path)

            # Should only have 2 parent examples (the limit)
            parent_tree = ET.parse(iter3_path / "examples" / "parent_examples.xml")
            parent_sessions = parent_tree.findall(".//session")
            assert len(parent_sessions) == 2

    def test_generates_pretty_printed_xml(self, mock_config):
        """Test that output XML is properly formatted with indentation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exp_path = Path(tmpdir) / "experiment"
            exp_path.mkdir()

            # Create simple structure
            iter0_path = exp_path / "iteration_0"
            iter0_path.mkdir()
            leaf_sessions = iter0_path / "leaf-sessions"
            leaf_sessions.mkdir()

            self.create_leaf_session_xml(
                leaf_sessions / "1-0-test.xml", "Test prompt", "Test response"
            )

            iter1_path = exp_path / "iteration_1"
            iter1_path.mkdir()
            (iter1_path / "examples").mkdir()

            aggregator = ExampleAggregator(mock_config)
            aggregator.create_examples_for_iteration(iter1_path, 1, exp_path)

            # Read raw XML and check formatting
            xml_content = (iter1_path / "examples" / "leaf_examples.xml").read_text()

            # Should have XML declaration
            assert "<?xml version='1.0' encoding='utf-8'?>" in xml_content

            # Should have newlines and indentation
            assert "\n" in xml_content
            # TODO: Check exact indentation once formatting logic is implemented

            # Should be valid XML
            ET.fromstring(xml_content)  # Will raise if invalid
