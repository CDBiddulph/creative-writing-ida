"""Prompt sampling with cross-iteration tracking."""

from pathlib import Path
from typing import List, Set, Tuple
import json
import random


class PromptSampler:
    """Manages prompt sampling without replacement across iterations."""

    def __init__(self, prompts_file_path: str):
        """
        Initialize prompt sampler with prompts file.

        Args:
            prompts_file_path: Path to file containing writing prompts (one per line)
        """
        self.prompts_file_path = Path(prompts_file_path)

        # Load and validate prompts
        if not self.prompts_file_path.exists():
            raise FileNotFoundError(f"Prompts file not found: {prompts_file_path}")

        self.prompts = self.prompts_file_path.read_text().strip().split("\n")
        self.prompts = [p.strip() for p in self.prompts if p.strip()]

        if not self.prompts:
            raise ValueError(f"Prompts file is empty: {prompts_file_path}")

    def sample_prompts_for_iteration(
        self, experiment_path: Path, iteration: int, num_prompts: int
    ) -> List[Tuple[int, str]]:
        """
        Sample prompts for an iteration without replacement across all iterations.

        Args:
            experiment_path: Path to experiment directory
            iteration: Current iteration number (0-based)
            num_prompts: Number of prompts to sample

        Returns:
            List of tuples (prompt_index, prompt_text) for sampled prompts

        Raises:
            ValueError: If not enough unused prompts available
        """
        # Get all previously used prompts
        used_prompts = self._get_cumulative_used_prompts(experiment_path)

        # Find available prompts (1-based indexing)
        all_indices = set(range(1, len(self.prompts) + 1))
        available_indices = all_indices - used_prompts

        if len(available_indices) < num_prompts:
            raise ValueError(
                f"Not enough unused prompts available. "
                f"Need {num_prompts}, but only {len(available_indices)} unused prompts remain."
            )

        # Sample without replacement
        sampled_indices = random.sample(list(available_indices), num_prompts)

        # Get prompt texts (convert to 0-based for list indexing)
        result = []
        for idx in sampled_indices:
            prompt_text = self.prompts[idx - 1]  # Convert to 0-based
            result.append((idx, prompt_text))

        # Update used prompts
        new_used_prompts = used_prompts | set(sampled_indices)
        self._save_used_prompts(experiment_path, iteration, new_used_prompts)

        return result

    def _get_cumulative_used_prompts(self, experiment_path: Path) -> Set[int]:
        """Get all used prompts from all previous iterations."""
        used_prompts = set()

        # Look for all iteration directories
        for iter_dir in experiment_path.glob("iteration_*"):
            used_prompts_file = iter_dir / "used_prompts.json"
            if used_prompts_file.exists():
                iter_used = json.loads(used_prompts_file.read_text())
                used_prompts.update(iter_used)

        return used_prompts

    def _save_used_prompts(
        self, experiment_path: Path, iteration: int, used_prompts: Set[int]
    ) -> None:
        """Save cumulative used prompts for this iteration."""
        iter_path = experiment_path / f"iteration_{iteration}"
        iter_path.mkdir(exist_ok=True)

        used_prompts_file = iter_path / "used_prompts.json"
        used_prompts_file.write_text(json.dumps(sorted(list(used_prompts))))
