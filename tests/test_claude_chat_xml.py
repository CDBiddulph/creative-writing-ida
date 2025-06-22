"""Tests for the ClaudeChatSessionXmlGenerator class."""

import unittest
from unittest.mock import patch, mock_open, MagicMock
import tempfile
import os
from src.session_xml_generator.claude_chat_xml import ClaudeChatSessionXmlGenerator
from src.session_xml_generator.session_xml_generator import get_session_xml_generator


class TestClaudeChatSessionXmlGenerator(unittest.TestCase):
    """Test the ClaudeChatSessionXmlGenerator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.model = "claude-3-5-haiku-20241022"
        self.max_tokens = 1000
        self.temperature = 0.7
        self.leaf_readme_path = "test_leaf_readme.md"
        self.parent_readme_path = "test_parent_readme.md"
        self.leaf_examples_xml_path = "test_leaf_examples.xml"
        self.parent_examples_xml_path = "test_parent_examples.xml"

        # Sample content for mocking
        self.sample_readme_content = "# Test README\nThis is a test README file."
        self.sample_examples_xml = """<?xml version="1.0" encoding="UTF-8"?>

<sessions>
<session>
<prompt>Test prompt</prompt>
<submit>Test response</submit>
</session>
</sessions>"""

        self.generator = ClaudeChatSessionXmlGenerator(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            leaf_readme_path=self.leaf_readme_path,
            parent_readme_path=self.parent_readme_path,
            leaf_examples_xml_path=self.leaf_examples_xml_path,
            parent_examples_xml_path=self.parent_examples_xml_path,
        )

    def test_init(self):
        """Test initialization of ClaudeChatSessionXmlGenerator."""
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
        generator = ClaudeChatSessionXmlGenerator(
            model=self.model, max_tokens=self.max_tokens, temperature=self.temperature
        )
        self.assertIsNone(generator.leaf_readme_path)
        self.assertIsNone(generator.parent_readme_path)
        self.assertIsNone(generator.leaf_examples_xml_path)
        self.assertIsNone(generator.parent_examples_xml_path)

    @patch("src.session_xml_generator.claude_chat_xml.anthropic.Anthropic")
    @patch("builtins.open", new_callable=mock_open)
    def test_generate_leaf_success(self, mock_file, mock_anthropic):
        """Test successful leaf generation."""
        # Mock file content
        mock_file.return_value.read.return_value = self.sample_readme_content

        # Mock Anthropic API response
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Generated story content")]
        mock_response.stop_reason = "stop_sequence"
        mock_client.messages.create.return_value = mock_response

        result = self.generator.generate_leaf("Write a story about robots")

        # Verify API was called correctly
        expected_content = """# Test README
This is a test README file.

## Transcripts

<?xml version="1.0" encoding="UTF-8"?>

<sessions>
<session>
<prompt>Test prompt</prompt>
<submit>Test response</submit>
</session>
</sessions>

<session>
<prompt>Write a story about robots</prompt>
<submit>"""

        mock_client.messages.create.assert_called_once_with(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[{"role": "user", "content": expected_content}],
            stop_sequences=["</submit>"],
        )

        # Verify result
        self.assertEqual(result, "Generated story content")


    @patch("src.session_xml_generator.claude_chat_xml.anthropic.Anthropic")
    @patch("builtins.open", new_callable=mock_open)
    def test_generate_leaf_without_examples(self, mock_file, mock_anthropic):
        """Test leaf generation without examples XML."""
        generator = ClaudeChatSessionXmlGenerator(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            leaf_readme_path=self.leaf_readme_path,
        )

        # Mock file content
        mock_file.return_value.read.return_value = self.sample_readme_content

        # Mock Anthropic API response
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Generated story without examples")]
        mock_response.stop_reason = "stop_sequence"
        mock_client.messages.create.return_value = mock_response

        result = generator.generate_leaf("Write a story about robots")

        # Verify only readme was opened
        self.assertEqual(mock_file.call_count, 1)

        # Verify API call doesn't include examples
        expected_content = """# Test README
This is a test README file.

## Transcripts

<session>
<prompt>Write a story about robots</prompt>
<submit>"""

        mock_client.messages.create.assert_called_once_with(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[{"role": "user", "content": expected_content}],
            stop_sequences=["</submit>"],
        )

        self.assertEqual(result, "Generated story without examples")

    @patch("src.session_xml_generator.claude_chat_xml.anthropic.Anthropic")
    @patch("builtins.open", new_callable=mock_open)
    def test_generate_parent_success(self, mock_file, mock_anthropic):
        """Test successful parent generation."""
        # Mock file content
        mock_file.return_value.read.return_value = self.sample_readme_content

        # Mock Anthropic API response
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [
            MagicMock(
                text="<notes>Some notes</notes>\n<ask>What color?</ask>\n<ask>What size?</ask>"
            )
        ]
        mock_response.stop_reason = "stop_sequence"
        mock_client.messages.create.return_value = mock_response

        result = self.generator.generate_parent("Create a story about adventure")

        # Verify API was called correctly for parent
        expected_readme_content = """# Test README
This is a test README file."""

        expected_transcript_content = """<?xml version="1.0" encoding="UTF-8"?>

<sessions>
<session>
<prompt>Test prompt</prompt>
<submit>Test response</submit>
</session>
</sessions>

<session>
<prompt>Create a story about adventure</prompt>
<submit>"""

        mock_client.messages.create.assert_called_once_with(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system="The assistant is in CLI simulation mode, and responds to the user's CLI commands only with the output of the command.",
            messages=[
                {"role": "user", "content": "<cmd>cat README.md</cmd>"},
                {"role": "assistant", "content": expected_readme_content},
                {"role": "user", "content": "<cmd>cat transcripts.xml</cmd>"},
                {"role": "assistant", "content": expected_transcript_content},
            ],
            stop_sequences=["</submit>"],
        )

        # Verify result
        self.assertIn("<notes>Some notes</notes>", result)
        self.assertIn("<ask>What color?</ask>", result)

    @patch("src.session_xml_generator.claude_chat_xml.anthropic.Anthropic")
    @patch("builtins.open", new_callable=mock_open)
    def test_generate_parent_with_system_prompt(self, mock_file, mock_anthropic):
        """Test parent generation includes system prompt."""
        # Mock file content
        mock_file.return_value.read.return_value = self.sample_readme_content

        # Mock Anthropic API response
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="<ask>What genre?</ask>")]
        mock_response.stop_reason = "stop_sequence"
        mock_client.messages.create.return_value = mock_response

        result = self.generator.generate_parent("Create a story")

        # Verify system prompt and CLI simulation format
        expected_readme_content = """# Test README
This is a test README file."""

        expected_transcript_content = """<session>
<prompt>Create a story</prompt>
<submit>"""

        mock_client.messages.create.assert_called_once_with(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system="The assistant is in CLI simulation mode, and responds to the user's CLI commands only with the output of the command.",
            messages=[
                {"role": "user", "content": "<cmd>cat README.md</cmd>"},
                {"role": "assistant", "content": expected_readme_content},
                {"role": "user", "content": "<cmd>cat transcripts.xml</cmd>"},
                {"role": "assistant", "content": expected_transcript_content},
            ],
            stop_sequences=["</submit>"],
        )

    @patch("src.session_xml_generator.claude_chat_xml.anthropic.Anthropic")
    def test_generate_leaf_api_error(self, mock_anthropic):
        """Test API error handling in leaf generation."""
        # Mock Anthropic API to raise an exception
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("API Error")

        with self.assertRaises(Exception) as context:
            self.generator.generate_leaf("Write a story")

        self.assertIn("API Error", str(context.exception))

    @patch("src.session_xml_generator.claude_chat_xml.anthropic.Anthropic")
    @patch("builtins.open", new_callable=mock_open)
    def test_generate_leaf_wrong_stop_reason(self, mock_file, mock_anthropic):
        """Test handling of unexpected stop reason."""
        # Mock file content
        mock_file.return_value.read.return_value = self.sample_readme_content

        # Mock Anthropic API response with wrong stop reason
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Incomplete response")]
        mock_response.stop_reason = "max_tokens"
        mock_client.messages.create.return_value = mock_response

        with self.assertRaises(RuntimeError) as context:
            self.generator.generate_leaf("Write a story")

        self.assertIn("API call did not complete properly", str(context.exception))
        self.assertIn("max_tokens", str(context.exception))

    @patch("src.session_xml_generator.claude_chat_xml.anthropic.Anthropic")
    @patch("builtins.open", new_callable=mock_open)
    def test_generate_leaf_unexpected_response_format(self, mock_file, mock_anthropic):
        """Test handling of unexpected response format."""
        # Mock file content
        mock_file.return_value.read.return_value = self.sample_readme_content

        # Mock Anthropic API response with unexpected format
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = []  # Empty content list
        mock_response.stop_reason = "stop_sequence"
        mock_client.messages.create.return_value = mock_response

        with self.assertRaises(ValueError) as context:
            self.generator.generate_leaf("Write a story")

        self.assertIn("Unexpected response format", str(context.exception))

    def test_generate_leaf_missing_readme_file(self):
        """Test error handling when README file is missing."""
        generator = ClaudeChatSessionXmlGenerator(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            leaf_readme_path="nonexistent_file.md",
        )

        with self.assertRaises(FileNotFoundError):
            generator.generate_leaf("Write a story")

    def test_generate_leaf_missing_examples_file(self):
        """Test error handling when examples file is missing."""
        with self.assertRaises(FileNotFoundError):
            self.generator.generate_leaf("Write a story")

    @patch("builtins.open", new_callable=mock_open)
    def test_generate_leaf_no_readme_path(self, mock_file):
        """Test leaf generation without README path uses default content."""
        generator = ClaudeChatSessionXmlGenerator(
            model=self.model, max_tokens=self.max_tokens, temperature=self.temperature
        )

        with patch(
            "src.session_xml_generator.claude_chat_xml.anthropic.Anthropic"
        ) as mock_anthropic:
            mock_client = MagicMock()
            mock_anthropic.return_value = mock_client
            mock_response = MagicMock()
            mock_response.content = [MagicMock(text="Default content story")]
            mock_response.stop_reason = "stop_sequence"
            mock_client.messages.create.return_value = mock_response

            result = generator.generate_leaf("Write a story")

            # Verify no files were opened
            mock_file.assert_not_called()

            # Verify API call uses default content
            expected_content = """# Fiction Leaf Experiments

Transcripts of delegated microfiction experiments.

## Transcripts

<session>
<prompt>Write a story</prompt>
<submit>"""

            mock_client.messages.create.assert_called_once_with(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[{"role": "user", "content": expected_content}],
                stop_sequences=["</submit>"],
            )

            self.assertEqual(result, "Default content story")

    @patch("src.session_xml_generator.claude_chat_xml.anthropic.Anthropic")
    @patch("builtins.open", new_callable=mock_open)
    def test_generate_leaf_cli_simulation_messages(self, mock_file, mock_anthropic):
        """Test that leaf generation uses proper CLI simulation message format."""
        # Mock file content
        mock_file.return_value.read.return_value = self.sample_readme_content

        # Mock Anthropic API response
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="CLI response")]
        mock_response.stop_reason = "stop_sequence"
        mock_client.messages.create.return_value = mock_response

        result = self.generator.generate_leaf("Write a story")

        # Verify messages structure for CLI simulation
        expected_content = """# Test README
This is a test README file.

## Transcripts

<session>
<prompt>Write a story</prompt>
<submit>"""

        mock_client.messages.create.assert_called_once_with(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            messages=[{"role": "user", "content": expected_content}],
            stop_sequences=["</submit>"],
        )

    @patch("src.session_xml_generator.claude_chat_xml.anthropic.Anthropic")
    @patch("builtins.open", new_callable=mock_open)
    def test_generate_parent_cli_simulation_messages(self, mock_file, mock_anthropic):
        """Test that parent generation uses proper CLI simulation message format."""
        # Mock file content
        mock_file.return_value.read.return_value = self.sample_readme_content

        # Mock Anthropic API response
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="<ask>CLI ask</ask>")]
        mock_response.stop_reason = "stop_sequence"
        mock_client.messages.create.return_value = mock_response

        result = self.generator.generate_parent("Create a story")

        # Verify CLI simulation system prompt and message structure
        expected_readme_content = """# Test README
This is a test README file."""

        expected_transcript_content = """<session>
<prompt>Create a story</prompt>
<submit>"""

        mock_client.messages.create.assert_called_once_with(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system="The assistant is in CLI simulation mode, and responds to the user's CLI commands only with the output of the command.",
            messages=[
                {"role": "user", "content": "<cmd>cat README.md</cmd>"},
                {"role": "assistant", "content": expected_readme_content},
                {"role": "user", "content": "<cmd>cat transcripts.xml</cmd>"},
                {"role": "assistant", "content": expected_transcript_content},
            ],
            stop_sequences=["</submit>"],
        )


class TestGetSessionXmlGeneratorChatModel(unittest.TestCase):
    """Test the get_session_xml_generator factory function for chat models."""

    def test_get_chat_model_generator(self):
        """Test getting chat model generator."""
        # This will work once ClaudeChatSessionXmlGenerator is implemented
        generator = get_session_xml_generator(
            model="claude-3-5-haiku-20241022",
            max_tokens=1000,
            leaf_readme_path="leaf.md",
            parent_readme_path="parent.md",
        )

        self.assertIsInstance(generator, ClaudeChatSessionXmlGenerator)
        self.assertEqual(generator.model, "claude-3-5-haiku-20241022")
        self.assertEqual(generator.max_tokens, 1000)

    def test_get_sonnet_model_generator(self):
        """Test getting sonnet model generator."""
        generator = get_session_xml_generator(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            leaf_readme_path="leaf.md",
            parent_readme_path="parent.md",
            temperature=0.3,
        )

        self.assertIsInstance(generator, ClaudeChatSessionXmlGenerator)
        self.assertEqual(generator.model, "claude-sonnet-4-20250514")
        self.assertEqual(generator.temperature, 0.3)

    def test_get_opus_model_generator(self):
        """Test getting opus model generator."""
        generator = get_session_xml_generator(
            model="claude-opus-4-20250514",
            max_tokens=1500,
            leaf_readme_path="leaf.md",
            parent_readme_path="parent.md",
        )

        self.assertIsInstance(generator, ClaudeChatSessionXmlGenerator)
        self.assertEqual(generator.model, "claude-opus-4-20250514")

    def test_get_generator_with_all_params_chat(self):
        """Test factory function with all parameters for chat model."""
        generator = get_session_xml_generator(
            model="claude-3-5-haiku-20241022",
            max_tokens=2000,
            leaf_readme_path="leaf.md",
            parent_readme_path="parent.md",
            temperature=0.5,
            leaf_examples_xml_path="leaf_examples.xml",
            parent_examples_xml_path="parent_examples.xml",
        )

        self.assertIsInstance(generator, ClaudeChatSessionXmlGenerator)
        self.assertEqual(generator.temperature, 0.5)
        self.assertEqual(generator.leaf_examples_xml_path, "leaf_examples.xml")
        self.assertEqual(generator.parent_examples_xml_path, "parent_examples.xml")


if __name__ == "__main__":
    unittest.main()
