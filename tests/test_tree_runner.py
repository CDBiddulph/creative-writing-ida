"""Tests for TreeRunner class."""

import unittest
import tempfile
import os
from unittest.mock import Mock, patch
from src.tree_runner import TreeRunner
from src.tree_config import TreeRunnerConfig


class TestTreeRunner(unittest.TestCase):
    """Test the TreeRunner class."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = TreeRunnerConfig(
            model="test-model",
            max_depth=2,
            output_dir=self.temp_dir,
            temperature=0.7,
            max_tokens=1000,
            leaf_readme_path="test_leaf.md",
            parent_readme_path="test_parent.md",
            prompt="Test prompt"
        )

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_init(self):
        """Test TreeRunner initialization."""
        runner = TreeRunner(self.config)
        self.assertIsInstance(runner, TreeRunner)

    @patch('src.tree_config.create_session_generator')
    def test_run_creates_output_file(self, mock_create_generator):
        """Test that run creates an output file with timestamp."""
        # Mock the XML generator to return simple XML
        mock_generator = Mock()
        mock_generator.generate_leaf.return_value = "<session><prompt>Test</prompt><submit>Result</submit></session>"
        mock_create_generator.return_value = mock_generator
        
        runner = TreeRunner(self.config)
        result_filename = runner.run("Write a simple story")
        
        # Check that a file was created
        self.assertIsNotNone(result_filename)
        self.assertTrue(result_filename.endswith('.xml'))
        
        # Check that file exists in output directory
        full_path = os.path.join(self.temp_dir, result_filename)
        self.assertTrue(os.path.exists(full_path))

    @patch('src.tree_config.create_session_generator')
    def test_run_with_tree_structure(self, mock_create_generator):
        """Test run with a tree that has parent and child nodes."""
        # Mock generator that creates asks in parent nodes
        mock_generator = Mock()
        
        def mock_generate_parent(prompt):
            if "Write a story" in prompt:
                return "<session><prompt>Write a story</prompt><notes>Need ideas</notes><ask>What genre?</ask>"
            elif "What genre?" in prompt:
                return "<session><prompt>What genre?</prompt><submit>Science fiction</submit></session>"
        
        def mock_generate_leaf(prompt):
            return f"<session><prompt>{prompt}</prompt><submit>Leaf response</submit></session>"
        
        mock_generator.generate_parent.side_effect = mock_generate_parent
        mock_generator.generate_leaf.side_effect = mock_generate_leaf
        mock_create_generator.return_value = mock_generator
        
        runner = TreeRunner(self.config)
        result_filename = runner.run("Write a story about robots")
        
        # Verify file was created
        full_path = os.path.join(self.temp_dir, result_filename)
        self.assertTrue(os.path.exists(full_path))
        
        # Read and verify XML structure
        with open(full_path, 'r') as f:
            content = f.read()
        
        self.assertIn('<sessions>', content)
        self.assertIn('<session>', content)
        self.assertIn('<id>0</id>', content)

    @patch('src.tree_config.create_session_generator')
    def test_run_with_failed_generation(self, mock_create_generator):
        """Test run when session generation fails."""
        mock_generator = Mock()
        mock_generator.generate_leaf.return_value = "FAILED"
        mock_create_generator.return_value = mock_generator
        
        runner = TreeRunner(self.config)
        result_filename = runner.run("Write a story")
        
        # Should still create a file even with failed content
        full_path = os.path.join(self.temp_dir, result_filename)
        self.assertTrue(os.path.exists(full_path))
        
        with open(full_path, 'r') as f:
            content = f.read()
        
        self.assertIn('FAILED', content)

    def test_run_with_invalid_initial_prompt(self):
        """Test run with empty or invalid initial prompt."""
        runner = TreeRunner(self.config)
        
        # Should handle empty prompt gracefully
        with patch('src.tree_config.create_session_generator') as mock_create:
            mock_generator = Mock()
            mock_generator.generate_leaf.return_value = "<session><prompt></prompt><submit>Empty</submit></session>"
            mock_create.return_value = mock_generator
            
            result_filename = runner.run("")
            self.assertIsNotNone(result_filename)


if __name__ == "__main__":
    unittest.main()