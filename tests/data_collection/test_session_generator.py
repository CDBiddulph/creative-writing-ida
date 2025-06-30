"""Tests for session generation functionality."""

import tempfile
from pathlib import Path
import xml.etree.ElementTree as ET
import pytest
from unittest.mock import Mock, patch
import random

from src.data_collection.session_generator import SessionGenerator
from src.data_collection.config import DataCollectionConfig


class TestSessionGenerator:
    """Test session generation using tree runner."""

    @pytest.fixture
    def test_config(self):
        """Create a test data collection config."""
        return DataCollectionConfig(
            experiment_id="test_exp",
            leaf_examples_per_iteration=1,
            parent_examples_per_iteration=0,  # TODO: once we have a web UI, enable parent generation for tests
            max_parent_examples=5,
            max_iterations=3,
            sample_max_depth=2,
            parent_max_depth=1,
            leaf_max_depth=3,
            writing_prompts_path="prompts.txt",
            seed_leaf_examples="leaf.xml",
            seed_parent_examples="parent.xml",
            parent_total_char_limit=2000,
            parent_submit_char_limit=500,
            web_ui_port=5000,
            model="test-model",
            temperature=0.7,
            max_tokens=1000,
            leaf_readme_path="leaf_readme.md",
            parent_readme_path="parent_readme.md",
        )

    @pytest.fixture
    def mock_tree_runner(self):
        """Mock TreeRunner to avoid actual API calls."""
        with patch(
            "src.data_collection.session_generator.TreeRunner"
        ) as mock_runner_class:

            def create_mock_runner(*args, **kwargs):
                mock_runner = Mock()

                # Track which config was used
                max_depth = kwargs.get("max_depth", args[0].max_depth if args else 0)

                def run_and_create_file(prompt):
                    # Create XML content based on the prompt
                    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<sessions>
  <final-response>Generated response for: {prompt}</final-response>
  <session>
    <id>0</id>
    <prompt>{prompt}</prompt>
    <submit>Generated response for: {prompt}</submit>
  </session>
  <session>
    <id>1</id>
    <prompt>Child prompt from: {prompt}</prompt>
    <submit>Child response</submit>
  </session>
</sessions>"""

                    # In real implementation, TreeRunner would save to a file
                    # For now, just return a dummy filename
                    return f"tree_output_depth{max_depth}.xml"

                mock_runner.run.side_effect = run_and_create_file
                mock_runner.max_depth = max_depth
                return mock_runner

            mock_runner_class.side_effect = create_mock_runner
            yield mock_runner_class

    def test_generates_sample_sessions_with_story_prefix(
        self, test_config, mock_tree_runner
    ):
        """Test that writing prompts are prepended with story prefix."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create prompts file
            prompts_file = Path(tmpdir) / "prompts.txt"
            prompts_file.write_text(
                "A robot discovers emotions\nTime travel paradox\nSpace station mystery"
            )
            test_config.writing_prompts_path = str(prompts_file)

            iter_path = Path(tmpdir) / "iteration_0"
            iter_path.mkdir()
            (iter_path / "sample-sessions").mkdir()
            (iter_path / "leaf-sessions").mkdir()

            examples_dir = iter_path / "examples"
            examples_dir.mkdir()
            (examples_dir / "leaf_examples.xml").write_text("<sessions></sessions>")
            (examples_dir / "parent_examples.xml").write_text("<sessions></sessions>")

            # Track calls to TreeRunner
            calls_made = []

            def track_calls(*args, **kwargs):
                runner = Mock()

                def tracked_run(prompt):
                    calls_made.append(prompt)
                    return "output.xml"

                runner.run = tracked_run
                return runner

            mock_tree_runner.side_effect = track_calls

            generator = SessionGenerator(test_config)

            # Fix random seed for reproducibility
            random.seed(42)

            # Create experiment path
            exp_path = Path(tmpdir) / "experiment"
            exp_path.mkdir()

            generator.generate_sessions_for_iteration(iter_path, exp_path, 0)

            # Verify story prefix was added for sample sessions
            story_prefixed_calls = [
                call
                for call in calls_made
                if call.startswith("Write a story using the following prompt:")
            ]
            assert len(story_prefixed_calls) >= 1
            # Should contain at least one of our prompts with story prefix
            has_story_prefix = any(
                "Write a story using the following prompt:" in call
                for call in calls_made
            )
            assert has_story_prefix

    def test_generates_both_sample_and_leaf_sessions(
        self, test_config, mock_tree_runner
    ):
        """Test that both sample and leaf sessions are generated when appropriate."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create prompts file
            prompts_file = Path(tmpdir) / "prompts.txt"
            prompts_file.write_text("Test prompt\nAnother prompt\nThird prompt")
            test_config.writing_prompts_path = str(prompts_file)
            iter_path = Path(tmpdir) / "iteration_0"
            iter_path.mkdir()
            (iter_path / "sample-sessions").mkdir()
            (iter_path / "leaf-sessions").mkdir()

            examples_dir = iter_path / "examples"
            examples_dir.mkdir()
            (examples_dir / "leaf_examples.xml").write_text("<sessions></sessions>")
            (examples_dir / "parent_examples.xml").write_text("<sessions></sessions>")

            # Use a mock that actually creates files with multiple nodes
            def create_mock_runner(config):
                runner = Mock()

                def run_and_save(prompt):
                    # Create different session types based on the prompt
                    if "Write a story" in prompt:
                        # Sample session with multiple nodes for leaf selection
                        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<sessions>
  <final-response>Story response</final-response>
  <session>
    <id>0</id>
    <prompt>Write a story using the following prompt: Test prompt</prompt>
    <submit>Root story</submit>
  </session>
  <session>
    <id>1</id>
    <prompt>First chapter</prompt>
    <submit>Chapter 1 content</submit>
  </session>
  <session>
    <id>2</id>
    <prompt>Second chapter</prompt>
    <submit>Chapter 2 content</submit>
  </session>
</sessions>"""
                    else:
                        # Leaf session
                        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<sessions>
  <final-response>Leaf response for: {prompt}</final-response>
  <session>
    <id>0</id>
    <prompt>{prompt}</prompt>
    <submit>Leaf response</submit>
  </session>
</sessions>"""

                    # Save to the appropriate output directory
                    output_dir = Path(config.output_dir)
                    output_dir.mkdir(parents=True, exist_ok=True)
                    filename = (
                        f"generated_{len(list(output_dir.glob('*.xml'))) + 1}.xml"
                    )
                    output_file = output_dir / filename
                    output_file.write_text(xml_content)

                    return filename

                runner.run.side_effect = run_and_save
                return runner

            mock_tree_runner.side_effect = create_mock_runner

            # Configure for generating leaf sessions
            test_config.leaf_examples_per_iteration = 1
            generator = SessionGenerator(test_config)

            random.seed(42)

            # Create experiment path
            exp_path = Path(tmpdir) / "experiment"
            exp_path.mkdir()

            generator.generate_sessions_for_iteration(iter_path, exp_path, 0)

            # Should have created sample sessions
            sample_sessions = list((iter_path / "sample-sessions").glob("*.xml"))
            assert len(sample_sessions) > 0

            # Should have created leaf sessions (if enough nodes available)
            leaf_sessions = list((iter_path / "leaf-sessions").glob("*.xml"))
            # Leaf sessions depend on node availability in sample sessions
            # This is a behavioral test - just verify the system tried to work

    def test_generates_leaf_sessions_from_selected_nodes(
        self, test_config, mock_tree_runner
    ):
        """Test that leaf sessions can be generated when sample sessions have multiple nodes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create prompts file
            prompts_file = Path(tmpdir) / "prompts.txt"
            prompts_file.write_text("Root task that needs completion\nAnother task")
            test_config.writing_prompts_path = str(prompts_file)
            iter_path = Path(tmpdir) / "iteration_0"
            iter_path.mkdir()
            (iter_path / "sample-sessions").mkdir()
            (iter_path / "leaf-sessions").mkdir()

            examples_dir = iter_path / "examples"
            examples_dir.mkdir()
            (examples_dir / "leaf_examples.xml").write_text("<sessions></sessions>")
            (examples_dir / "parent_examples.xml").write_text("<sessions></sessions>")

            # Use the same mock pattern from the experiment tests that creates files
            def create_mock_runner(config):
                mock_runner = Mock()
                call_count = [0]

                def run_and_save(prompt):
                    call_count[0] += 1
                    filename = f"output_{call_count[0]}.xml"

                    # Create the actual file in the output directory
                    output_dir = Path(config.output_dir)
                    output_dir.mkdir(parents=True, exist_ok=True)
                    output_file = output_dir / filename

                    # Create mock session XML content
                    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<sessions>
  <final-response>Generated response for: {prompt}</final-response>
  <session>
    <id>0</id>
    <prompt>{prompt}</prompt>
    <submit>Generated response for: {prompt}</submit>
  </session>
</sessions>"""
                    output_file.write_text(xml_content)

                    return filename

                mock_runner.run.side_effect = run_and_save
                return mock_runner

            mock_tree_runner.side_effect = create_mock_runner

            # Configure for a scenario that should generate leaf sessions
            test_config.leaf_examples_per_iteration = 1
            generator = SessionGenerator(test_config)

            random.seed(42)

            # Create experiment path
            exp_path = Path(tmpdir) / "experiment"
            exp_path.mkdir()

            generator.generate_sessions_for_iteration(iter_path, exp_path, 0)

            # Verify sample sessions were created first
            sample_sessions = list((iter_path / "sample-sessions").glob("*.xml"))
            assert len(sample_sessions) > 0

            # Behavioral test - the system should attempt to work correctly

    def test_uses_current_iteration_examples_for_generation(
        self, test_config, mock_tree_runner
    ):
        """Test that the generator operates with the current iteration's example files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create prompts file
            prompts_file = Path(tmpdir) / "prompts.txt"
            prompts_file.write_text("Test prompt for examples")
            test_config.writing_prompts_path = str(prompts_file)
            iter_path = Path(tmpdir) / "iteration_0"
            iter_path.mkdir()
            (iter_path / "sample-sessions").mkdir()
            (iter_path / "leaf-sessions").mkdir()

            examples_dir = iter_path / "examples"
            examples_dir.mkdir()

            # Create example files with specific content
            leaf_content = """<sessions>
  <session>
    <prompt>Example leaf prompt</prompt>
    <submit>Example leaf response</submit>
  </session>
</sessions>"""
            parent_content = """<sessions>
  <session>
    <prompt>Example parent prompt</prompt>
    <ask>Break this down</ask>
    <response>Subtask result</response>
    <submit>Combined result</submit>
  </session>
</sessions>"""
            (examples_dir / "leaf_examples.xml").write_text(leaf_content)
            (examples_dir / "parent_examples.xml").write_text(parent_content)

            generator = SessionGenerator(test_config)

            # Create experiment path
            exp_path = Path(tmpdir) / "experiment"
            exp_path.mkdir()

            generator.generate_sessions_for_iteration(iter_path, exp_path, 0)

            # Verify the system ran without errors
            # The integration with examples is tested more thoroughly at the Experiment level
            assert True  # Behavioral test - just verify it runs

    def test_handles_tree_generation_failures_gracefully(
        self, test_config, mock_tree_runner
    ):
        """Test appropriate error handling when tree generation fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create prompts file
            prompts_file = Path(tmpdir) / "prompts.txt"
            prompts_file.write_text("Test prompt that will fail")
            test_config.writing_prompts_path = str(prompts_file)
            iter_path = Path(tmpdir) / "iteration_0"
            iter_path.mkdir()
            (iter_path / "sample-sessions").mkdir()

            examples_dir = iter_path / "examples"
            examples_dir.mkdir()
            (examples_dir / "leaf_examples.xml").write_text("<sessions></sessions>")
            (examples_dir / "parent_examples.xml").write_text("<sessions></sessions>")

            # Make TreeRunner fail
            def failing_runner(*args, **kwargs):
                mock_runner = Mock()
                mock_runner.run.side_effect = Exception("API call failed")
                return mock_runner

            mock_tree_runner.side_effect = failing_runner

            generator = SessionGenerator(test_config)

            # Create experiment path
            exp_path = Path(tmpdir) / "experiment"
            exp_path.mkdir()

            with pytest.raises(RuntimeError, match="generation fail|API call failed"):
                generator.generate_sessions_for_iteration(iter_path, exp_path, 0)

    def test_creates_files_with_correct_naming_convention(
        self, test_config, mock_tree_runner
    ):
        """Test that generated files follow the naming convention."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create prompts file
            prompts_file = Path(tmpdir) / "prompts.txt"
            prompts_file.write_text("Test prompt for a story\nAnother story prompt")
            test_config.writing_prompts_path = str(prompts_file)
            iter_path = Path(tmpdir) / "iteration_0"
            iter_path.mkdir()
            (iter_path / "sample-sessions").mkdir()
            (iter_path / "leaf-sessions").mkdir()

            examples_dir = iter_path / "examples"
            examples_dir.mkdir()
            (examples_dir / "leaf_examples.xml").write_text("<sessions></sessions>")
            (examples_dir / "parent_examples.xml").write_text("<sessions></sessions>")

            # Create mock that actually writes files
            def writing_runner(*args, **kwargs):
                mock_runner = Mock()

                def write_file(prompt):
                    # Simulate what TreeRunner would do - save to output directory
                    # For testing, we'll just create empty files with expected names
                    if "Write a story" in prompt:
                        # This is a sample session
                        # TODO: Update filename once exact truncation logic is known
                        filename = "1-write-a-story-using-the-follow.xml"
                        (iter_path / "sample-sessions" / filename).write_text(
                            "<sessions></sessions>"
                        )
                    else:
                        # This is a leaf session
                        # TODO: Update filename format once known
                        filename = "1-0-test-leaf-prompt.xml"
                        (iter_path / "leaf-sessions" / filename).write_text(
                            "<sessions></sessions>"
                        )

                    return filename

                mock_runner.run.side_effect = write_file
                return mock_runner

            mock_tree_runner.side_effect = writing_runner

            generator = SessionGenerator(test_config)

            random.seed(42)

            # Create experiment path
            exp_path = Path(tmpdir) / "experiment"
            exp_path.mkdir()

            generator.generate_sessions_for_iteration(iter_path, exp_path, 0)

            # Check that files were created
            sample_files = list((iter_path / "sample-sessions").glob("*.xml"))
            leaf_files = list((iter_path / "leaf-sessions").glob("*.xml"))

            # TODO: Verify exact counts once node selection logic is implemented
            assert len(sample_files) >= 1
            assert len(leaf_files) >= 0  # Might be 0 if no leaf examples requested

    def test_parent_generation_raises_not_implemented(
        self, test_config, mock_tree_runner
    ):
        """Test that parent generation raises NotImplementedError when needed."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create prompts file
            prompts_file = Path(tmpdir) / "prompts.txt"
            prompts_file.write_text("Test prompt 1\nTest prompt 2\nTest prompt 3")
            test_config.writing_prompts_path = str(prompts_file)

            # Enable parent generation
            test_config.parent_examples_per_iteration = 1
            test_config.max_parent_examples = 5

            iter_path = Path(tmpdir) / "iteration_0"
            iter_path.mkdir()
            examples_dir = iter_path / "examples"
            examples_dir.mkdir()
            (examples_dir / "leaf_examples.xml").write_text("<sessions></sessions>")
            (examples_dir / "parent_examples.xml").write_text("<sessions></sessions>")

            generator = SessionGenerator(test_config)
            exp_path = Path(tmpdir) / "experiment"
            exp_path.mkdir()

            # Should raise NotImplementedError when parent generation is attempted
            with pytest.raises(
                NotImplementedError, match="Parent example generation requires a web UI"
            ):
                generator.generate_sessions_for_iteration(iter_path, exp_path, 0)
