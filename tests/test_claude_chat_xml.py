"""Tests for the ClaudeChatSessionGenerator class."""

import unittest
from unittest.mock import patch, MagicMock
import tempfile
import os
from src.session import Session, PromptEvent, AskEvent, ResponseEvent
from src.session_generator.claude_chat import ClaudeChatSessionGenerator
from src.session_generator.factory import get_session_generator


class TestClaudeChatSessionGenerator(unittest.TestCase):
    """Test the ClaudeChatSessionGenerator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.model = "claude-3-5-haiku-20241022"
        self.max_tokens = 1000
        self.temperature = 0.7

        # Sample content
        self.sample_readme_content = "# Test README\nThis is a test README file."
        self.sample_examples_xml = """<?xml version='1.0' encoding='utf-8'?>
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

        self.generator = ClaudeChatSessionGenerator(
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
        """Test initialization of ClaudeChatSessionGenerator."""
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
        generator = ClaudeChatSessionGenerator(
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

    @patch("src.llms.claude_chat.anthropic.Anthropic")
    def test_generate_leaf_success(self, mock_anthropic):
        """Test successful leaf generation returns Session object."""

        # Mock Anthropic API response
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="submit>Generated story content")]
        mock_response.stop_reason = "stop_sequence"
        mock_response.stop_sequence = "</submit>"
        mock_client.messages.create.return_value = mock_response

        result = self.generator.generate_leaf(
            "Write a story about robots", session_id=1
        )

        self.assertIsInstance(result, Session)
        self.assertEqual(result.session_id, 1)
        self.assertFalse(result.is_failed)

        # Verify the Session can be converted to expected XML
        expected_xml = "<session>\n<prompt>Write a story about robots</prompt>\n<submit>Generated story content</submit>\n</session>"
        self.assertEqual(result.to_xml(), expected_xml)

    @patch("src.llms.claude_chat.anthropic.Anthropic")
    def test_generate_parent_success(self, mock_anthropic):
        """Test successful parent generation returns Session object."""

        # Mock Anthropic API response
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text="notes>Some notes</notes>\n<ask>What color?")
        ]
        mock_response.stop_reason = "stop_sequence"
        mock_response.stop_sequence = "</ask>"
        mock_client.messages.create.return_value = mock_response

        result = self.generator.generate_parent(
            "Create a story about adventure", session_id=0
        )

        self.assertIsInstance(result, Session)
        self.assertEqual(result.session_id, 0)
        self.assertFalse(result.is_failed)

        # Verify the Session generates the expected XML
        result_xml = result.to_xml(include_closing_tag=False)
        expected_xml = (
            "<session>\n"
            "<prompt>Create a story about adventure</prompt>\n"
            "<notes>Some notes</notes>\n"
            "<ask>What color?</ask>"
        )
        self.assertEqual(result_xml, expected_xml)

    @patch("src.llms.claude_chat.anthropic.Anthropic")
    def test_generate_leaf_api_error_returns_failed_session(self, mock_anthropic):
        """Test API error handling returns failed Session."""
        # Mock Anthropic API to raise an exception
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("API Error")

        result = self.generator.generate_leaf(
            "Write a story", session_id=1, max_retries=1
        )

        self.assertIsInstance(result, Session)
        self.assertTrue(result.is_failed)
        self.assertEqual(result.session_id, 1)
        self.assertEqual(result.to_xml(), "FAILED")

    def test_generate_leaf_missing_readme_file(self):
        """Test error handling when README file is missing returns failed Session."""
        generator = ClaudeChatSessionGenerator(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            leaf_readme_path="nonexistent_file.md",
            parent_readme_path=self.parent_readme_path,
        )

        result = generator.generate_leaf("Write a story", session_id=1)

        self.assertIsInstance(result, Session)
        self.assertTrue(result.is_failed)

    @patch("src.llms.claude_chat.anthropic.Anthropic")
    def test_continue_parent_success(self, mock_anthropic):
        """Test successful continue_parent returns Session object."""
        # Mock Anthropic API response
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(text="notes>Good response!</notes>\n<submit>Final story content")
        ]
        mock_response.stop_reason = "stop_sequence"
        mock_response.stop_sequence = "</submit>"
        mock_client.messages.create.return_value = mock_response

        current_session = Session(session_id=0)
        current_session.add_event(PromptEvent(text="Write a story"))
        current_session.add_event(AskEvent(text="What genre?"))
        current_session.add_event(ResponseEvent(text="Science fiction"))

        result = self.generator.continue_parent(current_session)

        # Verify result is a Session object
        self.assertIsInstance(result, Session)
        self.assertEqual(result.session_id, 0)
        self.assertFalse(result.is_failed)


class TestGetSessionGeneratorChatModel(unittest.TestCase):
    """Test the get_session_generator factory function for chat models."""

    def test_get_chat_model_generator(self):
        """Test getting chat model generator."""
        generator = get_session_generator(
            model="claude-3-5-haiku-20241022",
            max_tokens=1000,
            leaf_readme_path="leaf.md",
            parent_readme_path="parent.md",
        )

        self.assertIsInstance(generator, ClaudeChatSessionGenerator)
        self.assertEqual(generator.model, "claude-3-5-haiku-20241022")
        self.assertEqual(generator.max_tokens, 1000)

    def test_get_sonnet_model_generator(self):
        """Test getting sonnet model generator."""
        generator = get_session_generator(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            leaf_readme_path="leaf.md",
            parent_readme_path="parent.md",
            temperature=0.3,
        )

        self.assertIsInstance(generator, ClaudeChatSessionGenerator)
        self.assertEqual(generator.model, "claude-sonnet-4-20250514")
        self.assertEqual(generator.temperature, 0.3)

    def test_get_opus_model_generator(self):
        """Test getting opus model generator."""
        generator = get_session_generator(
            model="claude-opus-4-20250514",
            max_tokens=1500,
            leaf_readme_path="leaf.md",
            parent_readme_path="parent.md",
        )

        self.assertIsInstance(generator, ClaudeChatSessionGenerator)
        self.assertEqual(generator.model, "claude-opus-4-20250514")

    def test_get_generator_with_all_params_chat(self):
        """Test factory function with all parameters for chat model."""
        generator = get_session_generator(
            model="claude-3-5-haiku-20241022",
            max_tokens=2000,
            leaf_readme_path="leaf.md",
            parent_readme_path="parent.md",
            temperature=0.5,
            leaf_examples_xml_path="leaf_examples.xml",
            parent_examples_xml_path="parent_examples.xml",
        )

        self.assertIsInstance(generator, ClaudeChatSessionGenerator)
        self.assertEqual(generator.temperature, 0.5)
        self.assertEqual(generator.leaf_examples_xml_path, "leaf_examples.xml")
        self.assertEqual(generator.parent_examples_xml_path, "parent_examples.xml")


if __name__ == "__main__":
    unittest.main()
