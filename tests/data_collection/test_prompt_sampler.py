"""Tests for prompt sampling with cross-iteration tracking."""

import tempfile
import json
from pathlib import Path
import pytest

from src.data_collection.prompt_sampler import PromptSampler


class TestPromptSampler:
    """Test prompt sampling functionality."""
    
    def test_samples_without_replacement_across_iterations(self):
        """Test that prompts are never reused across iterations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create prompts file with 10 prompts
            prompts_file = Path(tmpdir) / "prompts.txt"
            prompts = [f"Prompt {i}" for i in range(10)]
            prompts_file.write_text("\n".join(prompts))
            
            # Create experiment structure
            exp_path = Path(tmpdir) / "experiment"
            exp_path.mkdir()
            
            sampler = PromptSampler(str(prompts_file))
            
            # Sample 3 prompts for iteration 0
            iter0_prompts = sampler.sample_prompts_for_iteration(exp_path, 0, 3)
            assert len(iter0_prompts) == 3
            iter0_indices = [idx for idx, _ in iter0_prompts]
            
            # Sample 3 more for iteration 1
            iter1_prompts = sampler.sample_prompts_for_iteration(exp_path, 1, 3)
            assert len(iter1_prompts) == 3
            iter1_indices = [idx for idx, _ in iter1_prompts]
            
            # Verify no overlap
            assert len(set(iter0_indices) & set(iter1_indices)) == 0
            
            # Sample 3 more for iteration 2
            iter2_prompts = sampler.sample_prompts_for_iteration(exp_path, 2, 3)
            assert len(iter2_prompts) == 3
            iter2_indices = [idx for idx, _ in iter2_prompts]
            
            # Verify no overlap with any previous
            all_previous = set(iter0_indices) | set(iter1_indices)
            assert len(all_previous & set(iter2_indices)) == 0
    
    def test_raises_when_insufficient_prompts_available(self):
        """Test error when not enough unused prompts remain."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create prompts file with only 5 prompts
            prompts_file = Path(tmpdir) / "prompts.txt"
            prompts = [f"Prompt {i}" for i in range(5)]
            prompts_file.write_text("\n".join(prompts))
            
            exp_path = Path(tmpdir) / "experiment"
            exp_path.mkdir()
            
            sampler = PromptSampler(str(prompts_file))
            
            # Sample 3 prompts successfully
            sampler.sample_prompts_for_iteration(exp_path, 0, 3)
            
            # Trying to sample 3 more should fail (only 2 left)
            with pytest.raises(ValueError, match="enough unused prompts"):
                sampler.sample_prompts_for_iteration(exp_path, 1, 3)
    
    def test_loads_used_prompts_from_previous_iterations(self):
        """Test that used prompts are correctly loaded from disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            prompts_file = Path(tmpdir) / "prompts.txt"
            prompts = [f"Prompt {i}" for i in range(10)]
            prompts_file.write_text("\n".join(prompts))
            
            exp_path = Path(tmpdir) / "experiment"
            exp_path.mkdir()
            
            # Manually create iteration 0 with used prompts
            iter0_path = exp_path / "iteration_0"
            iter0_path.mkdir()
            used_prompts_file = iter0_path / "used_prompts.json"
            used_prompts_file.write_text(json.dumps([1, 3, 5]))
            
            # Create new sampler and sample for iteration 1
            sampler = PromptSampler(str(prompts_file))
            new_prompts = sampler.sample_prompts_for_iteration(exp_path, 1, 3)
            
            # Verify it doesn't reuse 1, 3, or 5
            new_indices = [idx for idx, _ in new_prompts]
            assert 1 not in new_indices
            assert 3 not in new_indices
            assert 5 not in new_indices
    
    def test_handles_empty_prompts_file(self):
        """Test appropriate error for empty prompts file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            prompts_file = Path(tmpdir) / "prompts.txt"
            prompts_file.write_text("")
            
            with pytest.raises(ValueError, match="empty"):
                PromptSampler(str(prompts_file))
    
    def test_saves_cumulative_used_prompts(self):
        """Test that used prompts accumulate correctly across iterations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            prompts_file = Path(tmpdir) / "prompts.txt"
            prompts = [f"Prompt {i}" for i in range(10)]
            prompts_file.write_text("\n".join(prompts))
            
            exp_path = Path(tmpdir) / "experiment"
            exp_path.mkdir()
            
            sampler = PromptSampler(str(prompts_file))
            
            # Sample for iteration 0
            sampler.sample_prompts_for_iteration(exp_path, 0, 2)
            
            # Check saved file
            iter0_used = json.loads((exp_path / "iteration_0" / "used_prompts.json").read_text())
            assert len(iter0_used) == 2
            
            # Sample for iteration 1
            sampler.sample_prompts_for_iteration(exp_path, 1, 3)
            
            # Check saved file includes both iterations
            iter1_used = json.loads((exp_path / "iteration_1" / "used_prompts.json").read_text())
            assert len(iter1_used) == 5  # 2 + 3
            
            # Verify iter0 prompts are in iter1
            for prompt_idx in iter0_used:
                assert prompt_idx in iter1_used
    
    def test_prompt_indices_are_one_based(self):
        """Test that returned prompt indices are 1-based, not 0-based."""
        with tempfile.TemporaryDirectory() as tmpdir:
            prompts_file = Path(tmpdir) / "prompts.txt"
            prompts = ["First prompt", "Second prompt", "Third prompt"]
            prompts_file.write_text("\n".join(prompts))
            
            exp_path = Path(tmpdir) / "experiment"
            exp_path.mkdir()
            
            sampler = PromptSampler(str(prompts_file))
            sampled = sampler.sample_prompts_for_iteration(exp_path, 0, 3)
            
            indices = sorted([idx for idx, _ in sampled])
            assert indices == [1, 2, 3]  # Not [0, 1, 2]
            
            # Verify text matches
            for idx, text in sampled:
                if idx == 1:
                    assert text == "First prompt"
                elif idx == 2:
                    assert text == "Second prompt"
                elif idx == 3:
                    assert text == "Third prompt"