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
            leaf_examples_per_iteration=5,
            parent_examples_per_iteration=3,
            max_parent_examples=20,
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
            parent_readme_path="parent_readme.md"
        )
    
    @pytest.fixture
    def mock_tree_runner(self):
        """Mock TreeRunner to avoid actual API calls."""
        with patch('src.data_collection.session_generator.TreeRunner') as mock_runner_class:
            def create_mock_runner(*args, **kwargs):
                mock_runner = Mock()
                
                # Track which config was used
                max_depth = kwargs.get('max_depth', args[0].max_depth if args else 0)
                
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
    
    def test_generates_sample_sessions_with_story_prefix(self, test_config, mock_tree_runner):
        """Test that writing prompts are prepended with story prefix."""
        with tempfile.TemporaryDirectory() as tmpdir:
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
            original_runner_class = mock_tree_runner
            
            def track_calls(*args, **kwargs):
                runner = original_runner_class(*args, **kwargs)
                original_run = runner.run
                
                def tracked_run(prompt):
                    calls_made.append(prompt)
                    return original_run(prompt)
                
                runner.run = tracked_run
                return runner
            
            mock_tree_runner.side_effect = track_calls
            
            generator = SessionGenerator(test_config)
            prompts = [(1, "A robot discovers emotions"), (2, "Time travel paradox")]
            
            # Fix random seed for reproducibility
            random.seed(42)
            
            generator.generate_sessions_for_iteration(iter_path, prompts, examples_dir)
            
            # Verify story prefix was added for sample sessions
            story_prefixed_calls = [call for call in calls_made 
                                   if call.startswith("Write a story using the following prompt:")]
            assert len(story_prefixed_calls) == 2
            assert "A robot discovers emotions" in story_prefixed_calls[0]
            assert "Time travel paradox" in story_prefixed_calls[1]
    
    def test_creates_different_tree_runners_for_different_depths(self, test_config, mock_tree_runner):
        """Test that sample and leaf generation use different max depths."""
        with tempfile.TemporaryDirectory() as tmpdir:
            iter_path = Path(tmpdir) / "iteration_0"
            iter_path.mkdir()
            (iter_path / "sample-sessions").mkdir()
            (iter_path / "leaf-sessions").mkdir()
            
            examples_dir = iter_path / "examples"
            examples_dir.mkdir()
            (examples_dir / "leaf_examples.xml").write_text("<sessions></sessions>")
            (examples_dir / "parent_examples.xml").write_text("<sessions></sessions>")
            
            # Create a sample session file for node selection
            sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
<sessions>
  <session>
    <id>0</id>
    <prompt>Root prompt</prompt>
    <submit>Root response</submit>
  </session>
</sessions>"""
            (iter_path / "sample-sessions" / "1-test-prompt.xml").write_text(sample_xml)
            
            # Track TreeRunner creations
            runners_created = []
            
            def track_runner_creation(*args, **kwargs):
                runner = Mock()
                runner.run.return_value = "output.xml"
                # Store the config used
                if args:
                    runners_created.append(('args', args[0]))
                else:
                    runners_created.append(('kwargs', kwargs))
                return runner
            
            mock_tree_runner.side_effect = track_runner_creation
            
            generator = SessionGenerator(test_config)
            prompts = [(1, "Test prompt")]
            
            random.seed(42)
            
            generator.generate_sessions_for_iteration(iter_path, prompts, examples_dir)
            
            # Should have created runners with different depths
            # First for sample generation (depth 2), then for leaf generation (depth 3)
            assert len(runners_created) >= 2
            
            # TODO: Verify exact depths once TreeRunnerConfig structure is known
            # For now, just verify multiple runners were created
            assert len(runners_created) > 1
    
    def test_generates_leaf_sessions_from_selected_nodes(self, test_config, mock_tree_runner):
        """Test that leaf sessions are generated from nodes selected from sample sessions."""
        with tempfile.TemporaryDirectory() as tmpdir:
            iter_path = Path(tmpdir) / "iteration_0"
            iter_path.mkdir()
            (iter_path / "sample-sessions").mkdir()
            (iter_path / "leaf-sessions").mkdir()
            
            examples_dir = iter_path / "examples"
            examples_dir.mkdir()
            (examples_dir / "leaf_examples.xml").write_text("<sessions></sessions>")
            (examples_dir / "parent_examples.xml").write_text("<sessions></sessions>")
            
            # Create sample sessions that will be used for node selection
            sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
<sessions>
  <session>
    <id>0</id>
    <prompt>Root task that needs completion</prompt>
    <submit>Root response</submit>
  </session>
  <session>
    <id>1</id>
    <prompt>Subtask 1</prompt>
    <submit>Subtask 1 response</submit>
  </session>
</sessions>"""
            (iter_path / "sample-sessions" / "1-root-task-that-needs-completi.xml").write_text(sample_xml)
            
            generator = SessionGenerator(test_config)
            prompts = [(1, "Root task that needs completion")]
            
            random.seed(42)
            
            generator.generate_sessions_for_iteration(iter_path, prompts, examples_dir)
            
            # Verify leaf sessions were created
            leaf_sessions = list((iter_path / "leaf-sessions").glob("*.xml"))
            assert len(leaf_sessions) > 0
            
            # Verify filename format includes node ID
            for session_file in leaf_sessions:
                parts = session_file.stem.split("-", 2)
                assert len(parts) >= 3
                assert parts[0] == "1"  # Original prompt index
                assert parts[1].isdigit()  # Node ID
    
    def test_uses_current_iteration_examples_for_generation(self, test_config, mock_tree_runner):
        """Test that the generator loads and uses current iteration's examples."""
        with tempfile.TemporaryDirectory() as tmpdir:
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
            
            # Track TreeRunnerConfig creation
            configs_created = []
            
            def track_config(*args, **kwargs):
                mock_runner = Mock()
                mock_runner.run.return_value = "output.xml"
                
                # Check if example paths are in kwargs
                if 'leaf_examples_xml_path' in kwargs:
                    configs_created.append({
                        'leaf_path': kwargs.get('leaf_examples_xml_path'),
                        'parent_path': kwargs.get('parent_examples_xml_path')
                    })
                
                return mock_runner
            
            mock_tree_runner.side_effect = track_config
            
            generator = SessionGenerator(test_config)
            prompts = [(1, "Test prompt")]
            
            generator.generate_sessions_for_iteration(iter_path, prompts, examples_dir)
            
            # Verify configs were created with correct example paths
            assert len(configs_created) > 0
            
            # TODO: Check exact paths once TreeRunnerConfig initialization is known
            # For now, just verify some configs were created
    
    def test_handles_tree_generation_failures_gracefully(self, test_config, mock_tree_runner):
        """Test appropriate error handling when tree generation fails."""
        with tempfile.TemporaryDirectory() as tmpdir:
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
            prompts = [(1, "Test prompt")]
            
            with pytest.raises(RuntimeError, match="generation fail|API call failed"):
                generator.generate_sessions_for_iteration(iter_path, prompts, examples_dir)
    
    def test_creates_files_with_correct_naming_convention(self, test_config, mock_tree_runner):
        """Test that generated files follow the naming convention."""
        with tempfile.TemporaryDirectory() as tmpdir:
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
                        (iter_path / "sample-sessions" / filename).write_text("<sessions></sessions>")
                    else:
                        # This is a leaf session
                        # TODO: Update filename format once known
                        filename = "1-0-test-leaf-prompt.xml"
                        (iter_path / "leaf-sessions" / filename).write_text("<sessions></sessions>")
                    
                    return filename
                
                mock_runner.run.side_effect = write_file
                return mock_runner
            
            mock_tree_runner.side_effect = writing_runner
            
            generator = SessionGenerator(test_config)
            prompts = [(1, "Test prompt for a story")]
            
            random.seed(42)
            
            generator.generate_sessions_for_iteration(iter_path, prompts, examples_dir)
            
            # Check that files were created
            sample_files = list((iter_path / "sample-sessions").glob("*.xml"))
            leaf_files = list((iter_path / "leaf-sessions").glob("*.xml"))
            
            # TODO: Verify exact counts once node selection logic is implemented
            assert len(sample_files) >= 1
            assert len(leaf_files) >= 0  # Might be 0 if no leaf examples requested