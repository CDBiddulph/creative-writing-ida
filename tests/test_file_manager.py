"""Tests for the file_manager module."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import tempfile
import shutil
from file_manager import FileManager
from models import Session, generate_session_filename


class TestFileManager(unittest.TestCase):
    """Test the FileManager class."""
    
    def setUp(self):
        """Create temporary directory for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.test_file_path = os.path.join(self.test_dir, "test_readme.md")
        self.test_xml_path = os.path.join(self.test_dir, "test_examples.xml")
    
    def tearDown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.test_dir)
    
    def test_load_readme_content_success(self):
        """Test loading README content from file."""
        test_content = "# Test README\n\nThis is a test."
        with open(self.test_file_path, 'w') as f:
            f.write(test_content)
        
        content = FileManager.load_readme_content(self.test_file_path)
        self.assertEqual(content, test_content)
    
    def test_load_readme_content_file_not_found(self):
        """Test loading README when file doesn't exist."""
        content = FileManager.load_readme_content("nonexistent.md")
        self.assertIn("Fiction Experiments", content)
    
    def test_load_examples_xml_success(self):
        """Test loading examples XML from file."""
        test_xml = "<session><prompt>Test</prompt></session>"
        with open(self.test_xml_path, 'w') as f:
            f.write(test_xml)
        
        content = FileManager.load_examples_xml(self.test_xml_path)
        self.assertEqual(content, test_xml)
    
    def test_load_examples_xml_none_path(self):
        """Test loading examples with None path."""
        content = FileManager.load_examples_xml(None)
        self.assertEqual(content, "")
    
    def test_load_examples_xml_file_not_found(self):
        """Test loading examples when file doesn't exist."""
        content = FileManager.load_examples_xml("nonexistent.xml")
        self.assertEqual(content, "")
    
    def test_ensure_output_directory(self):
        """Test ensuring output directory exists."""
        output_dir = os.path.join(self.test_dir, "output")
        self.assertFalse(os.path.exists(output_dir))
        
        FileManager.ensure_output_directory(output_dir)
        self.assertTrue(os.path.exists(output_dir))
        
        # Should not raise error if called again
        FileManager.ensure_output_directory(output_dir)
        self.assertTrue(os.path.exists(output_dir))
    
    def test_save_session_xml(self):
        """Test saving sessions to XML file."""
        output_dir = os.path.join(self.test_dir, "output")
        
        # Create test sessions
        session1 = Session(id=0, prompt="First prompt")
        session1.set_final_submit("First response")
        
        session2 = Session(id=1, prompt="Second prompt", responding_to_id=0)
        session2.set_final_submit("Second response")
        
        sessions = [session1, session2]
        
        # Save sessions
        filename = FileManager.save_session_xml(sessions, output_dir)
        
        # Check file was created
        file_path = os.path.join(output_dir, filename)
        self.assertTrue(os.path.exists(file_path))
        
        # Check content
        with open(file_path, 'r') as f:
            content = f.read()
        
        self.assertIn('<?xml version="1.0" encoding="UTF-8"?>', content)
        self.assertIn('<sessions>', content)
        self.assertIn('</sessions>', content)
        self.assertIn('<prompt>First prompt</prompt>', content)
        self.assertIn('<submit>First response</submit>', content)
        self.assertIn('<response-id>0</response-id>', content)
    
    def test_get_absolute_path(self):
        """Test converting relative to absolute paths."""
        # Already absolute path
        abs_path = "/home/user/file.txt"
        self.assertEqual(FileManager.get_absolute_path(abs_path), abs_path)
        
        # Relative path
        rel_path = "file.txt"
        result = FileManager.get_absolute_path(rel_path)
        self.assertTrue(os.path.isabs(result))
        self.assertTrue(result.endswith("file.txt"))


class TestGenerateSessionFilename(unittest.TestCase):
    """Test the generate_session_filename function."""
    
    def test_filename_format(self):
        """Test generated filename format."""
        filename = generate_session_filename()
        self.assertTrue(filename.startswith("session_"))
        self.assertTrue(filename.endswith(".xml"))
        # Check timestamp format YYYYMMDD_HHMMSS
        self.assertEqual(len(filename), 27)  # session_YYYYMMDD_HHMMSS.xml


if __name__ == '__main__':
    unittest.main()