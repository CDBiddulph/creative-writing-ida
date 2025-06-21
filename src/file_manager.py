"""File management utilities for loading and saving session data."""

import os
from typing import Optional
from models import Session, generate_session_filename


class FileManager:
    """Handles file I/O operations for the tree simulation system."""
    
    @staticmethod
    def load_readme_content(file_path: str) -> str:
        """Load README content from file, with fallback."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Warning: README file {file_path} not found. Using default content.")
            return "# Fiction Experiments\n\nTranscripts of creative writing experiments."
        except Exception as e:
            print(f"Warning: Error loading README file {file_path}: {e}. Using default content.")
            return "# Fiction Experiments\n\nTranscripts of creative writing experiments."
    
    @staticmethod
    def load_examples_xml(file_path: Optional[str]) -> str:
        """Load examples XML from file, returning empty string if not provided or not found."""
        if not file_path:
            return ""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            print(f"Warning: Examples file {file_path} not found. Continuing without examples.")
            return ""
        except Exception as e:
            print(f"Warning: Error loading examples file {file_path}: {e}. Continuing without examples.")
            return ""
    
    @staticmethod
    def ensure_output_directory(output_dir: str) -> None:
        """Ensure the output directory exists."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    @staticmethod
    def save_session_xml(sessions: list[Session], output_dir: str) -> str:
        """Save sessions to timestamped XML file and return the filename."""
        FileManager.ensure_output_directory(output_dir)
        
        filename = generate_session_filename()
        file_path = os.path.join(output_dir, filename)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                f.write('<sessions>\n')
                
                for session in sessions:
                    # Add proper indentation to session XML
                    session_xml = session.to_xml()
                    indented_xml = '\n'.join('  ' + line if line.strip() else line 
                                           for line in session_xml.split('\n'))
                    f.write(indented_xml + '\n\n')
                
                f.write('</sessions>\n')
            
            print(f"Session XML saved to: {file_path}")
            return filename
            
        except Exception as e:
            print(f"Error saving session XML to {file_path}: {e}")
            raise
    
    @staticmethod
    def get_absolute_path(file_path: str) -> str:
        """Convert relative path to absolute path."""
        if os.path.isabs(file_path):
            return file_path
        return os.path.abspath(file_path)