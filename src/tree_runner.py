"""Main orchestrator for tree-based story generation."""

import os
from datetime import datetime
from .tree_runner_config import TreeRunnerConfig, create_session_generator
from .session_processor import SessionProcessor
from .xml_formatter import XmlFormatter


class TreeRunner:
    """Main orchestrator for tree-based story generation."""

    def __init__(self, config: TreeRunnerConfig):
        """
        Initialize TreeRunner with configuration.

        Args:
            config: TreeRunnerConfig containing all settings for generation
        """
        self.config = config

        # Create dependencies
        self.session_generator = create_session_generator(config)
        self.xml_formatter = XmlFormatter()

        # Create session processor
        self.session_processor = SessionProcessor(
            session_generator=self.session_generator, max_depth=config.max_depth
        )

        # Ensure output directory exists
        os.makedirs(config.output_dir, exist_ok=True)

    def run(self, initial_prompt: str) -> str:
        """
        Run the complete tree generation process from initial prompt to saved file.

        Args:
            initial_prompt: The starting prompt for the root session

        Returns:
            str: Filename of the saved XML output file

        Creates a complete tree by calling SessionProcessor.process_session,
        then saves the result as a timestamped XML file.
        """
        # Generate the complete tree
        root_node = self.session_processor.process_session(initial_prompt)

        # Format as XML
        formatted_xml = self.xml_formatter.format_tree_xml(root_node)

        # Create timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"tree_generation_{timestamp}.xml"
        filepath = os.path.join(self.config.output_dir, filename)

        # Save to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(formatted_xml)

        return filename
