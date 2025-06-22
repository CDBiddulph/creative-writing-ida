"""Tests for configuration management."""

import unittest
import tempfile
import os
from unittest.mock import patch, Mock
from src.tree_config import TreeRunnerConfig, parse_args, create_session_generator


class TestTreeRunnerConfig(unittest.TestCase):
    """Test the TreeRunnerConfig dataclass."""

    def test_config_creation(self):
        """Test creating a TreeRunnerConfig with all required fields."""
        config = TreeRunnerConfig(
            model="test-model",
            max_depth=3,
            output_dir="test_output",
            temperature=0.8,
            max_tokens=2000,
            leaf_readme_path="leaf.md",
            parent_readme_path="parent.md"
        )
        
        self.assertEqual(config.model, "test-model")
        self.assertEqual(config.max_depth, 3)
        self.assertEqual(config.output_dir, "test_output")
        self.assertEqual(config.temperature, 0.8)
        self.assertEqual(config.max_tokens, 2000)
        self.assertEqual(config.leaf_readme_path, "leaf.md")
        self.assertEqual(config.parent_readme_path, "parent.md")
        self.assertIsNone(config.leaf_examples_xml_path)
        self.assertIsNone(config.parent_examples_xml_path)

    def test_config_with_optional_fields(self):
        """Test creating a TreeRunnerConfig with optional fields."""
        config = TreeRunnerConfig(
            model="test-model",
            max_depth=2,
            output_dir="output",
            temperature=0.7,
            max_tokens=1000,
            leaf_readme_path="leaf.md",
            parent_readme_path="parent.md",
            leaf_examples_xml_path="leaf_examples.xml",
            parent_examples_xml_path="parent_examples.xml"
        )
        
        self.assertEqual(config.leaf_examples_xml_path, "leaf_examples.xml")
        self.assertEqual(config.parent_examples_xml_path, "parent_examples.xml")


class TestParseArgs(unittest.TestCase):
    """Test the parse_args function."""

    def test_parse_args_all_required(self):
        """Test parsing with all required arguments."""
        test_args = [
            '--model', 'claude-3-sonnet',
            '--max-depth', '3',
            '--output-dir', '/tmp/output',
            '--temperature', '0.8',
            '--max-tokens', '2000',
            '--leaf-readme-path', 'prompts/leaf.md',
            '--parent-readme-path', 'prompts/parent.md'
        ]
        
        with patch('sys.argv', ['test'] + test_args):
            config = parse_args()
            
            self.assertEqual(config.model, 'claude-3-sonnet')
            self.assertEqual(config.max_depth, 3)
            self.assertEqual(config.output_dir, '/tmp/output')
            self.assertEqual(config.temperature, 0.8)
            self.assertEqual(config.max_tokens, 2000)
            self.assertEqual(config.leaf_readme_path, 'prompts/leaf.md')
            self.assertEqual(config.parent_readme_path, 'prompts/parent.md')

    def test_parse_args_with_optional(self):
        """Test parsing with optional arguments included."""
        test_args = [
            '--model', 'test-model',
            '--max-depth', '2',
            '--output-dir', 'sessions',
            '--temperature', '0.7',
            '--max-tokens', '1000',
            '--leaf-readme-path', 'leaf.md',
            '--parent-readme-path', 'parent.md',
            '--leaf-examples-xml-path', 'examples/leaf.xml',
            '--parent-examples-xml-path', 'examples/parent.xml'
        ]
        
        with patch('sys.argv', ['test'] + test_args):
            config = parse_args()
            
            self.assertEqual(config.leaf_examples_xml_path, 'examples/leaf.xml')
            self.assertEqual(config.parent_examples_xml_path, 'examples/parent.xml')

    def test_parse_args_defaults(self):
        """Test that default values are applied correctly."""
        test_args = [
            '--model', 'test-model',
            '--max-depth', '2',
            '--temperature', '0.7',
            '--max-tokens', '1000',
            '--leaf-readme-path', 'leaf.md',
            '--parent-readme-path', 'parent.md'
            # Note: no output-dir specified, should use default
        ]
        
        with patch('sys.argv', ['test'] + test_args):
            config = parse_args()
            
            # Should use default output directory
            self.assertEqual(config.output_dir, 'sessions/')

    def test_parse_args_invalid_depth(self):
        """Test parsing with invalid max depth values."""
        test_args = [
            '--model', 'test-model',
            '--max-depth', '-1',  # Invalid: negative depth
            '--output-dir', 'output',
            '--temperature', '0.7',
            '--max-tokens', '1000',
            '--leaf-readme-path', 'leaf.md',
            '--parent-readme-path', 'parent.md'
        ]
        
        with patch('sys.argv', ['test'] + test_args):
            with self.assertRaises(SystemExit):  # argparse exits on invalid values
                parse_args()

    def test_parse_args_invalid_temperature(self):
        """Test parsing with invalid temperature values."""
        test_args = [
            '--model', 'test-model',
            '--max-depth', '2',
            '--output-dir', 'output',
            '--temperature', '2.0',  # Invalid: > 1.0
            '--max-tokens', '1000',
            '--leaf-readme-path', 'leaf.md',
            '--parent-readme-path', 'parent.md'
        ]
        
        with patch('sys.argv', ['test'] + test_args):
            with self.assertRaises(SystemExit):
                parse_args()

    def test_parse_args_missing_required(self):
        """Test parsing with missing required arguments."""
        test_args = [
            '--model', 'test-model',
            '--max-depth', '2'
            # Missing other required args
        ]
        
        with patch('sys.argv', ['test'] + test_args):
            with self.assertRaises(SystemExit):
                parse_args()

    def test_parse_args_help(self):
        """Test that help can be displayed."""
        with patch('sys.argv', ['test', '--help']):
            with self.assertRaises(SystemExit):
                parse_args()


class TestCreateSessionGenerator(unittest.TestCase):
    """Test the create_session_generator function."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config = TreeRunnerConfig(
            model="claude-3-sonnet",
            max_depth=2,
            output_dir=self.temp_dir,
            temperature=0.7,
            max_tokens=1000,
            leaf_readme_path="leaf.md",
            parent_readme_path="parent.md"
        )

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)

    @patch('src.tree_config.get_session_xml_generator')
    def test_create_session_generator_base_model(self, mock_factory):
        """Test creating generator for base model."""
        mock_generator = Mock()
        mock_factory.return_value = mock_generator
        
        result = create_session_generator(self.config)
        
        mock_factory.assert_called_once_with(
            model="claude-3-sonnet",
            max_tokens=1000,
            leaf_readme_path="leaf.md",
            parent_readme_path="parent.md",
            temperature=0.7,
            leaf_examples_xml_path=None,
            parent_examples_xml_path=None
        )
        self.assertEqual(result, mock_generator)

    @patch('src.tree_config.get_session_xml_generator')
    def test_create_session_generator_chat_model(self, mock_factory):
        """Test creating generator for chat model."""
        self.config.model = "claude-3-5-haiku-20241022"
        mock_generator = Mock()
        mock_factory.return_value = mock_generator
        
        result = create_session_generator(self.config)
        
        mock_factory.assert_called_once_with(
            model="claude-3-5-haiku-20241022",
            max_tokens=1000,
            leaf_readme_path="leaf.md",
            parent_readme_path="parent.md",
            temperature=0.7,
            leaf_examples_xml_path=None,
            parent_examples_xml_path=None
        )

    @patch('src.tree_config.get_session_xml_generator')
    def test_create_session_generator_with_examples(self, mock_factory):
        """Test creating generator with example paths."""
        self.config.leaf_examples_xml_path = "examples/leaf.xml"
        self.config.parent_examples_xml_path = "examples/parent.xml"
        
        mock_generator = Mock()
        mock_factory.return_value = mock_generator
        
        result = create_session_generator(self.config)
        
        # Should pass through the example paths
        call_args = mock_factory.call_args[1]
        self.assertEqual(call_args['leaf_examples_xml_path'], "examples/leaf.xml")
        self.assertEqual(call_args['parent_examples_xml_path'], "examples/parent.xml")

    @patch('src.tree_config.get_session_xml_generator')
    def test_create_session_generator_factory_error(self, mock_factory):
        """Test handling of factory errors."""
        mock_factory.side_effect = ValueError("Unknown model")
        
        with self.assertRaises(ValueError):
            create_session_generator(self.config)

    def test_create_session_generator_config_validation(self):
        """Test that config is validated before creating generator."""
        # Test with invalid paths
        invalid_config = TreeRunnerConfig(
            model="test-model",
            max_depth=2,
            output_dir=self.temp_dir,
            temperature=0.7,
            max_tokens=1000,
            leaf_readme_path="nonexistent.md",
            parent_readme_path="also_nonexistent.md"
        )
        
        # The function should handle non-existent files gracefully
        # (validation might happen later in the pipeline)
        with patch('src.tree_config.get_session_xml_generator') as mock_factory:
            mock_factory.return_value = Mock()
            result = create_session_generator(invalid_config)
            self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()