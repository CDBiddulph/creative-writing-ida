"""Tests for the ClaudeBaseSessionGenerator class."""

import unittest
from unittest.mock import patch, MagicMock
import tempfile
import os
from src.session_generator.claude_base import ClaudeBaseSessionGenerator
from src.session_generator.factory import get_session_generator


class TestClaudeBaseSessionGenerator(unittest.TestCase):
    """Test the ClaudeBaseSessionGenerator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.model = "as-hackathon-big-base-rollout"
        self.max_tokens = 1000
        self.temperature = 0.7

        # Sample content
        self.sample_readme_content = "# Test README\nThis is a test README file."
        self.sample_examples_xml = """<?xml version="1.0" encoding="UTF-8"?>

<sessions>
<session>
<prompt>Test prompt</prompt>
<submit>Test response</submit>
</session>
</sessions>"""

        # Create temporary files
        self.temp_dir = tempfile.mkdtemp()

        self.leaf_readme_path = os.path.join(self.temp_dir, "leaf_readme.md")
        with open(self.leaf_readme_path, "w") as f:
            f.write(self.sample_readme_content)

        self.parent_readme_path = os.path.join(self.temp_dir, "parent_readme.md")
        with open(self.parent_readme_path, "w") as f:
            f.write(self.sample_readme_content)

        self.leaf_examples_xml_path = os.path.join(self.temp_dir, "leaf_examples.xml")
        with open(self.leaf_examples_xml_path, "w") as f:
            f.write(self.sample_examples_xml)

        self.parent_examples_xml_path = os.path.join(
            self.temp_dir, "parent_examples.xml"
        )
        with open(self.parent_examples_xml_path, "w") as f:
            f.write(self.sample_examples_xml)

        self.generator = ClaudeBaseSessionGenerator(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            leaf_readme_path=self.leaf_readme_path,
            parent_readme_path=self.parent_readme_path,
            leaf_examples_xml_path=self.leaf_examples_xml_path,
            parent_examples_xml_path=self.parent_examples_xml_path,
        )

    def tearDown(self):
        """Clean up temporary files."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_init(self):
        """Test initialization of ClaudeBaseSessionGenerator."""
        self.assertEqual(self.generator.model, self.model)
        self.assertEqual(self.generator.max_tokens, self.max_tokens)
        self.assertEqual(self.generator.temperature, self.temperature)
        self.assertEqual(self.generator.leaf_readme_path, self.leaf_readme_path)
        self.assertEqual(self.generator.parent_readme_path, self.parent_readme_path)
        self.assertEqual(
            self.generator.leaf_examples_xml_path, self.leaf_examples_xml_path
        )
        self.assertEqual(
            self.generator.parent_examples_xml_path, self.parent_examples_xml_path
        )

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        generator = ClaudeBaseSessionGenerator(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            leaf_readme_path=self.leaf_readme_path,
            parent_readme_path=self.parent_readme_path,
        )
        self.assertEqual(generator.leaf_readme_path, self.leaf_readme_path)
        self.assertEqual(generator.parent_readme_path, self.parent_readme_path)
        self.assertIsNone(generator.leaf_examples_xml_path)
        self.assertIsNone(generator.parent_examples_xml_path)

    @patch("src.llms.claude_base.anthropic.Anthropic")
    def test_generate_leaf_success(self, mock_anthropic):
        """Test successful leaf generation returns Session object."""

        # Mock Anthropic API response
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.completion = "submit>Generated story content"
        mock_response.stop_reason = "stop_sequence"
        mock_response.stop_sequence = "</submit>"
        mock_client.completions.create.return_value = mock_response

        result = self.generator.generate_leaf("Write a story about robots", session_id=1)

        # Verify result is a Session object
        from src.session import Session
        self.assertIsInstance(result, Session)
        self.assertEqual(result.session_id, 1)
        self.assertFalse(result.is_failed)
        
        # Verify the Session can be converted to expected XML
        expected_xml = "<session>\n<prompt>Write a story about robots</prompt>\n<submit>Generated story content</submit>\n</session>"
        self.assertEqual(result.to_xml(), expected_xml)

    @patch("src.llms.claude_base.anthropic.Anthropic")
    def test_generate_parent_success(self, mock_anthropic):
        """Test successful parent generation returns Session object."""

        # Mock Anthropic API response
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.completion = "notes>Some notes</notes>\n<ask>What color?"
        mock_response.stop_reason = "stop_sequence"
        mock_response.stop_sequence = "</ask>"
        mock_client.completions.create.return_value = mock_response

        result = self.generator.generate_parent("Create a story about adventure", session_id=0)

        # Verify result is a Session object
        from src.session import Session
        self.assertIsInstance(result, Session)
        self.assertEqual(result.session_id, 0)
        self.assertFalse(result.is_failed)
        
        # Verify the Session can be converted to expected XML
        # The mock response includes 'notes>Some notes</notes>\n<ask>What color?' so we expect both notes and ask
        result_xml = result.to_xml(include_closing_tag=False)
        self.assertIn("<prompt>Create a story about adventure</prompt>", result_xml)
        self.assertIn("<ask>What color?</ask>", result_xml)
        # Notes tag should be present since it's in the mock response
        self.assertTrue("<notes>" in result_xml or "<ask>" in result_xml)

    @patch("src.llms.claude_base.anthropic.Anthropic")
    def test_generate_leaf_api_error_returns_failed_session(self, mock_anthropic):
        """Test API error handling returns failed Session."""
        # Mock Anthropic API to raise an exception
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.completions.create.side_effect = Exception("API Error")

        result = self.generator.generate_leaf("Write a story", session_id=1, max_retries=1)

        # Should return failed Session rather than raising exception
        from src.session import Session
        self.assertIsInstance(result, Session)
        self.assertTrue(result.is_failed)
        self.assertEqual(result.session_id, 1)
        self.assertEqual(result.to_xml(), "FAILED")

    def test_generate_leaf_missing_readme_file(self):
        """Test error handling when README file is missing returns failed Session."""
        generator = ClaudeBaseSessionGenerator(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            leaf_readme_path="nonexistent_file.md",
            parent_readme_path=self.parent_readme_path,
        )

        result = generator.generate_leaf("Write a story", session_id=1)
        
        # Should return failed Session rather than raising exception
        from src.session import Session
        self.assertIsInstance(result, Session)
        self.assertTrue(result.is_failed)

    @patch("src.llms.claude_base.anthropic.Anthropic")
    def test_continue_parent_success(self, mock_anthropic):
        """Test successful continue_parent returns Session object."""
        # Mock Anthropic API response
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.completion = "notes>Good response!</notes>\n<submit>Final story content"
        mock_response.stop_reason = "stop_sequence"
        mock_response.stop_sequence = "</submit>"
        mock_client.completions.create.return_value = mock_response

        # Create an initial session to continue
        from src.session import Session, PromptEvent, AskEvent, ResponseEvent
        current_session = Session(session_id=0)
        current_session.add_event(PromptEvent(text="Write a story"))
        current_session.add_event(AskEvent(text="What genre?"))
        current_session.add_event(ResponseEvent(text="Science fiction"))

        result = self.generator.continue_parent(current_session)

        # Verify result is a Session object
        self.assertIsInstance(result, Session)
        self.assertEqual(result.session_id, 0)
        self.assertFalse(result.is_failed)


class TestGetSessionGenerator(unittest.TestCase):
    """Test the get_session_generator factory function."""

    def test_get_base_model_generator(self):
        """Test getting base model generator."""
        generator = get_session_generator(
            model="as-hackathon-big-base-rollout",
            max_tokens=1000,
            leaf_readme_path="leaf.md",
            parent_readme_path="parent.md",
        )

        self.assertIsInstance(generator, ClaudeBaseSessionGenerator)
        self.assertEqual(generator.model, "as-hackathon-big-base-rollout")
        self.assertEqual(generator.max_tokens, 1000)

    def test_get_chat_model_generator(self):
        """Test getting chat model generator."""
        generator = get_session_generator(
            model="claude-3-5-haiku-20241022",
            max_tokens=1000,
            leaf_readme_path="leaf.md",
            parent_readme_path="parent.md",
        )

        # Import here to avoid circular import
        from src.session_generator.claude_chat import (
            ClaudeChatSessionGenerator,
        )

        self.assertIsInstance(generator, ClaudeChatSessionGenerator)
        self.assertEqual(generator.model, "claude-3-5-haiku-20241022")
        self.assertEqual(generator.max_tokens, 1000)

    def test_get_generator_with_all_params(self):
        """Test factory function with all parameters."""
        generator = get_session_generator(
            model="as-hackathon-little-base-rollout",
            max_tokens=2000,
            leaf_readme_path="leaf.md",
            parent_readme_path="parent.md",
            temperature=0.5,
            leaf_examples_xml_path="leaf_examples.xml",
            parent_examples_xml_path="parent_examples.xml",
        )

        self.assertIsInstance(generator, ClaudeBaseSessionGenerator)
        self.assertEqual(generator.temperature, 0.5)
        self.assertEqual(generator.leaf_examples_xml_path, "leaf_examples.xml")
        self.assertEqual(generator.parent_examples_xml_path, "parent_examples.xml")


if __name__ == "__main__":
    unittest.main()