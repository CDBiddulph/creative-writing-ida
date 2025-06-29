"""Handles placeholder replacement in session text."""

import re
from typing import Dict, List, Optional
from .session import Session, PromptEvent, ResponseEvent


class PlaceholderReplacer:
    """Handles replacement of placeholders like $PROMPT, $RESPONSE1, etc."""
    
    def __init__(self):
        """Initialize the placeholder replacer."""
        self.placeholder_pattern = re.compile(r'\$(?:PROMPT|RESPONSE\d+)')
    
    def extract_placeholders(self, text: str) -> List[str]:
        """Extract all placeholders from text.
        
        Args:
            text: Text that may contain placeholders
            
        Returns:
            List of unique placeholders found in the text
        """
        return list(set(self.placeholder_pattern.findall(text)))
    
    def build_replacement_map(self, session: Session) -> Dict[str, str]:
        """Build a map of placeholders to their replacement values.
        
        Args:
            session: Session containing prompt and response events
            
        Returns:
            Dictionary mapping placeholders to their replacement text
        """
        replacement_map = {}
        
        # Extract prompt text
        prompt_events = [event for event in session.events if isinstance(event, PromptEvent)]
        if prompt_events:
            replacement_map['$PROMPT'] = prompt_events[0].text
        
        # Extract response texts
        response_events = [event for event in session.events if isinstance(event, ResponseEvent)]
        for i, response_event in enumerate(response_events, 1):
            replacement_map[f'$RESPONSE{i}'] = response_event.text
        
        return replacement_map
    
    def replace_placeholders(self, text: str, replacement_map: Dict[str, str]) -> str:
        """Replace placeholders in text with their values.
        
        If the text consists only of a single placeholder (e.g., just "$PROMPT"),
        replace it with the exact content. Otherwise, use context naming.
        
        Args:
            text: Text containing placeholders
            replacement_map: Map of placeholders to replacement values
            
        Returns:
            Text with placeholders replaced
        """
        # Check if text is just a single placeholder
        stripped_text = text.strip()
        if stripped_text in replacement_map:
            return replacement_map[stripped_text]
        
        # Otherwise, handle multiple placeholders or mixed content
        # Extract all placeholders in the text
        placeholders_in_text = self.extract_placeholders(text)
        
        # Only create context for placeholders that exist in replacement_map
        placeholders_to_replace = [p for p in placeholders_in_text if p in replacement_map]
        
        if not placeholders_to_replace:
            # No replaceable placeholders found, return original text
            return text
        
        # Create context mapping
        context_map = {}
        context_num = 1
        
        # Sort placeholders to ensure consistent ordering
        sorted_placeholders = sorted(placeholders_to_replace)
        
        for placeholder in sorted_placeholders:
            context_name = f"CONTEXT{context_num}"
            context_map[placeholder] = context_name
            context_num += 1
        
        # Build context section
        context_lines = []
        for placeholder in sorted_placeholders:
            context_name = context_map[placeholder]
            content = replacement_map[placeholder]
            context_lines.append(f"{context_name}:\n{content}")
        
        # Replace placeholders with context names in the original text
        result = text
        # Sort by length descending to avoid partial replacements
        for placeholder in sorted(context_map.keys(), key=len, reverse=True):
            context_name = context_map[placeholder]
            result = result.replace(placeholder, f"${context_name}")
        
        # Combine context definitions with the updated text
        return "\n\n".join(context_lines) + "\n\n" + result
    
    def process_text(self, text: str, session: Session) -> str:
        """Process text to replace all placeholders.
        
        Args:
            text: Text that may contain placeholders
            session: Session containing the replacement values
            
        Returns:
            Text with all placeholders replaced
        """
        if not text:
            return text
            
        # Check if there are any placeholders
        if not self.placeholder_pattern.search(text):
            return text
        
        # Build replacement map and replace
        replacement_map = self.build_replacement_map(session)
        return self.replace_placeholders(text, replacement_map)