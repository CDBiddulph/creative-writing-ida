"""Tests for main entry point."""

import unittest
import tempfile
import os
from unittest.mock import patch, Mock
from src.main import main


class TestMain(unittest.TestCase):
    """Test the main function."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)

    @patch('src.main.TreeRunner')
    @patch('src.main.parse_args')
    def test_main_successful_execution(self, mock_parse_args, mock_tree_runner):
        """Test successful execution of main function."""
        # Mock configuration
        mock_config = Mock()
        mock_config.output_dir = self.temp_dir
        mock_parse_args.return_value = mock_config
        
        # Mock TreeRunner
        mock_runner = Mock()
        mock_runner.run.return_value = "session_20240101_120000.xml"
        mock_tree_runner.return_value = mock_runner
        
        # Mock sys.argv to include an initial prompt
        test_args = ['main.py', 'Write a story about robots']
        with patch('sys.argv', test_args):
            main()
        
        # Verify TreeRunner was created and run was called
        mock_tree_runner.assert_called_once_with(mock_config)
        mock_runner.run.assert_called_once_with('Write a story about robots')

    @patch('src.main.TreeRunner')
    @patch('src.main.parse_args')
    def test_main_no_prompt_argument(self, mock_parse_args, mock_tree_runner):
        """Test main function with no prompt argument."""
        mock_config = Mock()
        mock_parse_args.return_value = mock_config
        
        mock_runner = Mock()
        mock_tree_runner.return_value = mock_runner
        
        # No prompt argument provided
        test_args = ['main.py']
        with patch('sys.argv', test_args):
            with self.assertRaises(SystemExit):
                main()

    @patch('src.main.TreeRunner')
    @patch('src.main.parse_args')
    def test_main_multiple_prompt_words(self, mock_parse_args, mock_tree_runner):
        """Test main function with multi-word prompt."""
        mock_config = Mock()
        mock_parse_args.return_value = mock_config
        
        mock_runner = Mock()
        mock_runner.run.return_value = "output.xml"
        mock_tree_runner.return_value = mock_runner
        
        # Multi-word prompt
        test_args = ['main.py', 'Write', 'a', 'complex', 'story', 'about', 'time', 'travel']
        with patch('sys.argv', test_args):
            main()
        
        # Should join all words into single prompt
        mock_runner.run.assert_called_once_with('Write a complex story about time travel')

    @patch('src.main.TreeRunner')
    @patch('src.main.parse_args')
    @patch('builtins.print')
    def test_main_prints_output_filename(self, mock_print, mock_parse_args, mock_tree_runner):
        """Test that main prints the output filename."""
        mock_config = Mock()
        mock_parse_args.return_value = mock_config
        
        mock_runner = Mock()
        output_filename = "session_20240101_120000.xml"
        mock_runner.run.return_value = output_filename
        mock_tree_runner.return_value = mock_runner
        
        test_args = ['main.py', 'Test prompt']
        with patch('sys.argv', test_args):
            main()
        
        # Should print the output filename
        mock_print.assert_called_with(f"Session saved to: {output_filename}")

    @patch('src.main.TreeRunner')
    @patch('src.main.parse_args')
    def test_main_handles_tree_runner_exception(self, mock_parse_args, mock_tree_runner):
        """Test main function handles TreeRunner exceptions gracefully."""
        mock_config = Mock()
        mock_parse_args.return_value = mock_config
        
        # TreeRunner raises an exception
        mock_tree_runner.side_effect = Exception("TreeRunner failed")
        
        test_args = ['main.py', 'Test prompt']
        with patch('sys.argv', test_args):
            with self.assertRaises(Exception):
                main()

    @patch('src.main.TreeRunner')
    @patch('src.main.parse_args')
    def test_main_handles_parse_args_exception(self, mock_parse_args, mock_tree_runner):
        """Test main function handles argument parsing exceptions."""
        # parse_args raises an exception
        mock_parse_args.side_effect = SystemExit("Invalid arguments")
        
        test_args = ['main.py', 'Test prompt']
        with patch('sys.argv', test_args):
            with self.assertRaises(SystemExit):
                main()

    @patch('src.main.TreeRunner')
    @patch('src.main.parse_args')
    @patch('src.main.logging')
    def test_main_sets_up_logging(self, mock_logging, mock_parse_args, mock_tree_runner):
        """Test that main sets up logging appropriately."""
        mock_config = Mock()
        mock_parse_args.return_value = mock_config
        
        mock_runner = Mock()
        mock_runner.run.return_value = "output.xml"
        mock_tree_runner.return_value = mock_runner
        
        test_args = ['main.py', 'Test prompt']
        with patch('sys.argv', test_args):
            main()
        
        # Should configure logging
        mock_logging.basicConfig.assert_called_once()

    @patch('src.main.TreeRunner')
    @patch('src.main.parse_args')
    def test_main_empty_prompt(self, mock_parse_args, mock_tree_runner):
        """Test main function with empty prompt."""
        mock_config = Mock()
        mock_parse_args.return_value = mock_config
        
        mock_runner = Mock()
        mock_runner.run.return_value = "output.xml"
        mock_tree_runner.return_value = mock_runner
        
        test_args = ['main.py', '']
        with patch('sys.argv', test_args):
            main()
        
        # Should still call run with empty string
        mock_runner.run.assert_called_once_with('')

    @patch('src.main.TreeRunner')
    @patch('src.main.parse_args')
    def test_main_special_characters_in_prompt(self, mock_parse_args, mock_tree_runner):
        """Test main function with special characters in prompt."""
        mock_config = Mock()
        mock_parse_args.return_value = mock_config
        
        mock_runner = Mock()
        mock_runner.run.return_value = "output.xml"
        mock_tree_runner.return_value = mock_runner
        
        # Prompt with special characters
        special_prompt = "Write a story with 'quotes' and \"double quotes\" & symbols!"
        test_args = ['main.py'] + special_prompt.split()
        with patch('sys.argv', test_args):
            main()
        
        mock_runner.run.assert_called_once_with(special_prompt)


if __name__ == "__main__":
    unittest.main()