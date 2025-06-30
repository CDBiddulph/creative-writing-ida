"""Tests for file management operations."""

import tempfile
import json
from pathlib import Path
import pytest

from src.data_collection.file_manager import FileManager


class TestFileManager:
    """Test file management functionality."""
    
    def test_creates_complete_experiment_structure(self):
        """Test that setup_experiment creates all required directories and files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exp_path = Path(tmpdir) / "fiction_0628"
            manager = FileManager(exp_path)
            
            config = {
                "experiment_id": "fiction_0628",
                "model": "claude-3",
                "max_iterations": 5,
                "temperature": 0.7
            }
            
            manager.setup_experiment(config)
            
            # Verify experiment directory exists
            assert exp_path.exists()
            assert exp_path.is_dir()
            
            # Verify config.json exists and contains correct data
            config_file = exp_path / "config.json"
            assert config_file.exists()
            saved_config = json.loads(config_file.read_text())
            assert saved_config == config
    
    def test_setup_iteration_creates_correct_structure(self):
        """Test that iteration directories have correct subdirectories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exp_path = Path(tmpdir) / "experiment"
            exp_path.mkdir()
            
            manager = FileManager(exp_path)
            iter_path = manager.setup_iteration(0)
            
            # Verify iteration directory
            assert iter_path == exp_path / "iteration_0"
            assert iter_path.exists()
            
            # Verify subdirectories
            assert (iter_path / "examples").exists()
            assert (iter_path / "sample-sessions").exists()
            assert (iter_path / "leaf-sessions").exists()
            # Note: parent-sessions not created in MVP
    
    def test_handles_existing_experiment_directory(self):
        """Test behavior when experiment directory already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exp_path = Path(tmpdir) / "experiment"
            exp_path.mkdir()
            
            # Add existing config
            existing_config = {"old": "config"}
            (exp_path / "config.json").write_text(json.dumps(existing_config))
            
            manager = FileManager(exp_path)
            new_config = {"new": "config"}
            
            # This should work for resume functionality
            manager.setup_experiment(new_config)
            
            # Config should be overwritten
            saved_config = json.loads((exp_path / "config.json").read_text())
            assert saved_config == new_config
    
    def test_iteration_numbering_is_consistent(self):
        """Test that iteration directories are numbered correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            exp_path = Path(tmpdir) / "experiment"
            exp_path.mkdir()
            
            manager = FileManager(exp_path)
            
            # Create iterations 0, 1, 2
            for i in range(3):
                iter_path = manager.setup_iteration(i)
                assert iter_path.name == f"iteration_{i}"
                assert iter_path.parent == exp_path