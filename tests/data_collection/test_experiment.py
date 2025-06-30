"""Tests for experiment lifecycle management."""

import tempfile
import json
from pathlib import Path
import pytest
from unittest.mock import Mock, patch
import random

from src.data_collection.experiment import Experiment
from src.data_collection.config import DataCollectionConfig


class TestExperiment:
    """Test experiment orchestration functionality."""
    
    @pytest.fixture
    def test_config(self):
        """Create a test data collection config with temp files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create all required files
            prompts_file = Path(tmpdir) / "prompts.txt"
            prompts_file.write_text("\n".join([f"Test prompt {i}" for i in range(1, 11)]))
            
            leaf_examples = Path(tmpdir) / "seed_leaf.xml"
            leaf_examples.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<sessions>
  <session>
    <prompt>Seed leaf prompt</prompt>
    <submit>Seed leaf response</submit>
  </session>
</sessions>""")
            
            parent_examples = Path(tmpdir) / "seed_parent.xml"
            parent_examples.write_text("""<?xml version="1.0" encoding="UTF-8"?>
<sessions>
  <session>
    <prompt>Seed parent prompt</prompt>
    <ask>Break this down</ask>
    <response>Subtask result</response>
    <submit>Combined result</submit>
  </session>
</sessions>""")
            
            # Create README files
            leaf_readme = Path(tmpdir) / "leaf_readme.md"
            leaf_readme.write_text("Leaf generation instructions")
            parent_readme = Path(tmpdir) / "parent_readme.md"
            parent_readme.write_text("Parent generation instructions")
            
            config = DataCollectionConfig(
                experiment_id="test_exp",
                leaf_examples_per_iteration=2,
                parent_examples_per_iteration=0,  # Skip parent generation for MVP
                max_parent_examples=5,
                max_iterations=3,
                sample_max_depth=2,
                parent_max_depth=1,
                leaf_max_depth=2,
                writing_prompts_path=str(prompts_file),
                seed_leaf_examples=str(leaf_examples),
                seed_parent_examples=str(parent_examples),
                parent_total_char_limit=2000,
                parent_submit_char_limit=500,
                web_ui_port=5000,
                model="test-model",
                temperature=0.7,
                max_tokens=1000,
                leaf_readme_path=str(leaf_readme),
                parent_readme_path=str(parent_readme)
            )
            
            yield config, tmpdir
    
    @pytest.fixture
    def mock_tree_runner(self):
        """Mock TreeRunner to avoid actual API calls."""
        with patch('src.data_collection.session_generator.TreeRunner') as mock_runner_class:
            
            # Create a counter to generate unique content
            call_count = [0]
            
            def create_mock_runner(config):
                mock_runner = Mock()
                
                def run_and_save(prompt):
                    call_count[0] += 1
                    filename = f"output_{call_count[0]}.xml"
                    
                    # Create the actual file in the output directory
                    from pathlib import Path
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
  <session>
    <id>1</id>
    <prompt>Child prompt from: {prompt}</prompt>
    <submit>Child response</submit>
  </session>
</sessions>"""
                    output_file.write_text(xml_content)
                    
                    return filename
                
                mock_runner.run.side_effect = run_and_save
                return mock_runner
            
            mock_runner_class.side_effect = create_mock_runner
            yield mock_runner_class
    
    def test_creates_new_experiment_directory_structure(self, test_config, mock_tree_runner):
        """Test that run() creates complete experiment structure for new experiment."""
        config, tmpdir = test_config
        
        # Fix random seed
        random.seed(42)
        
        experiment = Experiment(config, base_dir=Path(tmpdir))
        experiment.run()
        
        # Verify experiment directory exists
        exp_path = Path(tmpdir) / config.experiment_id
        assert exp_path.exists()
        
        # Verify config.json was created
        assert (exp_path / "config.json").exists()
        saved_config = json.loads((exp_path / "config.json").read_text())
        assert saved_config["experiment_id"] == "test_exp"
        assert saved_config["max_iterations"] == 3
        
        # Verify all iteration directories exist
        for i in range(3):
            iter_path = exp_path / f"iteration_{i}"
            assert iter_path.exists()
            assert (iter_path / "examples").exists()
            assert (iter_path / "sample-sessions").exists()
            assert (iter_path / "leaf-sessions").exists()
            assert (iter_path / "used_prompts.json").exists()
            
            # Check examples exist
            assert (iter_path / "examples" / "leaf_examples.xml").exists()
            assert (iter_path / "examples" / "parent_examples.xml").exists()
    
    def test_resumes_existing_experiment_from_correct_iteration(self, test_config, mock_tree_runner):
        """Test that run() resumes from the last incomplete iteration."""
        config, tmpdir = test_config
        config.max_iterations = 3  # Need 3 iterations to test resumption
        
        # Fix random seed
        random.seed(42)
        
        # First, run experiment for 2 iterations only
        config_partial = config.__class__(**vars(config))
        config_partial.max_iterations = 2
        
        experiment1 = Experiment(config_partial, base_dir=Path(tmpdir))
        experiment1.run()
        
        # Verify we have 2 iterations
        exp_path = Path(tmpdir) / "test_exp"
        assert (exp_path / "iteration_0").exists()
        assert (exp_path / "iteration_1").exists()
        assert not (exp_path / "iteration_2").exists()
        
        # Now resume with full config (3 iterations)
        experiment2 = Experiment(config, base_dir=Path(tmpdir))
        experiment2.run()
        
        # Verify iteration 2 was created during resume
        iter2_path = exp_path / "iteration_2"
        assert iter2_path.exists()
        
        # Verify used prompts accumulated correctly
        iter0_used = json.loads((exp_path / "iteration_0" / "used_prompts.json").read_text())
        iter1_used = json.loads((exp_path / "iteration_1" / "used_prompts.json").read_text())
        iter2_used = json.loads((iter2_path / "used_prompts.json").read_text())
        
        # Each iteration should have more used prompts (cumulative)
        assert len(iter1_used) > len(iter0_used)
        assert len(iter2_used) > len(iter1_used)
        
        # Verify no prompts are reused across iterations
        assert len(set(iter2_used)) == len(iter2_used)  # No duplicates
    
    def test_completes_when_max_iterations_reached(self, test_config, mock_tree_runner):
        """Test that experiment stops after max_iterations."""
        config, tmpdir = test_config
        config.max_iterations = 2
        
        random.seed(42)
        
        experiment = Experiment(config, base_dir=Path(tmpdir))
        experiment.run()
        
        exp_path = Path(tmpdir) / config.experiment_id
        
        # Should have exactly 2 iterations (0 and 1)
        assert (exp_path / "iteration_0").exists()
        assert (exp_path / "iteration_1").exists()
        assert not (exp_path / "iteration_2").exists()
    
    def test_handles_insufficient_prompts_gracefully(self, test_config, mock_tree_runner):
        """Test appropriate error when running out of prompts."""
        config, tmpdir = test_config
        
        # Create prompts file with too few prompts
        prompts_file = Path(tmpdir) / "few_prompts.txt"
        prompts_file.write_text("Only one prompt")
        config.writing_prompts_path = str(prompts_file)
        config.leaf_examples_per_iteration = 5  # Request more than available
        
        experiment = Experiment(config, base_dir=Path(tmpdir))
        
        with pytest.raises(RuntimeError, match="Insufficient prompts|not enough"):
            experiment.run()
    
    def test_generates_correct_final_command(self, test_config, mock_tree_runner):
        """Test that get_final_command returns properly formatted command."""
        config, tmpdir = test_config
        config.max_iterations = 1  # Just one iteration for speed
        
        random.seed(42)
        
        experiment = Experiment(config, base_dir=Path(tmpdir))
        experiment.run()
        
        command = experiment.get_final_command()
        
        # Verify command structure
        assert "python src/tree_runner_main.py" in command
        assert "--model test-model" in command
        assert "--temperature 0.7" in command
        assert "--max-tokens 1000" in command
        assert "--leaf-examples-xml-path" in command
        assert "iteration_0/examples/leaf_examples.xml" in command
        assert "--parent-examples-xml-path" in command
        assert "iteration_0/examples/parent_examples.xml" in command
        assert '--prompt "Your prompt here"' in command
    
    def test_sample_sessions_have_correct_filenames(self, test_config, mock_tree_runner):
        """Test that sample session files follow naming convention."""
        config, tmpdir = test_config
        config.max_iterations = 1
        
        random.seed(42)
        
        experiment = Experiment(config, base_dir=Path(tmpdir))
        experiment.run()
        
        # Check sample session filenames
        exp_path = Path(tmpdir) / config.experiment_id
        sample_sessions = list((exp_path / "iteration_0" / "sample-sessions").glob("*.xml"))
        
        # Should have files like "1-test-prompt-1.xml"
        assert len(sample_sessions) == 2  # leaf_examples_per_iteration = 2
        
        for session_file in sample_sessions:
            # Filename should start with a number
            parts = session_file.stem.split("-", 1)
            assert parts[0].isdigit()
            # Should be 1-based index
            assert int(parts[0]) >= 1
            assert int(parts[0]) <= 10  # We have 10 prompts
            # Rest should be truncated prompt (about 30 chars)
            assert len(parts[1]) <= 35  # Some wiggle room
    
    def test_leaf_sessions_have_node_id_in_filename(self, test_config, mock_tree_runner):
        """Test that leaf session files include node ID."""
        config, tmpdir = test_config
        config.max_iterations = 1
        
        random.seed(42)
        
        experiment = Experiment(config, base_dir=Path(tmpdir))
        experiment.run()
        
        # Check leaf session filenames
        exp_path = Path(tmpdir) / config.experiment_id
        leaf_sessions = list((exp_path / "iteration_0" / "leaf-sessions").glob("*.xml"))
        
        # Should have files like "1-0-prompt-text.xml"
        assert len(leaf_sessions) == 2  # leaf_examples_per_iteration = 2
        
        for session_file in leaf_sessions:
            # Filename should have format: promptindex-nodeid-text
            parts = session_file.stem.split("-", 2)
            assert len(parts) >= 3
            assert parts[0].isdigit()  # Prompt index
            assert parts[1].isdigit()  # Node ID
    
    def test_used_prompts_accumulate_correctly(self, test_config, mock_tree_runner):
        """Test that used prompts accumulate across iterations."""
        config, tmpdir = test_config
        config.max_iterations = 3
        config.leaf_examples_per_iteration = 1  # Use fewer prompts
        
        random.seed(42)
        
        experiment = Experiment(config, base_dir=Path(tmpdir))
        experiment.run()
        
        exp_path = Path(tmpdir) / config.experiment_id
        
        # Check used prompts for each iteration
        iter0_used = json.loads((exp_path / "iteration_0" / "used_prompts.json").read_text())
        iter1_used = json.loads((exp_path / "iteration_1" / "used_prompts.json").read_text())
        iter2_used = json.loads((exp_path / "iteration_2" / "used_prompts.json").read_text())
        
        # Each iteration should have more prompts
        assert len(iter0_used) == 1
        assert len(iter1_used) == 2
        assert len(iter2_used) == 3
        
        # Later iterations should include all earlier prompts
        for prompt in iter0_used:
            assert prompt in iter1_used
            assert prompt in iter2_used
        
        for prompt in iter1_used:
            assert prompt in iter2_used