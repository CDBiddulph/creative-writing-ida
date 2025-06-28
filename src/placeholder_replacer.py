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
        
        Args:
            text: Text containing placeholders
            replacement_map: Map of placeholders to replacement values
            
        Returns:
            Text with placeholders replaced
        """
        result = text
        
        # Sort placeholders by length (descending) to avoid partial replacements
        # e.g., replace $RESPONSE10 before $RESPONSE1
        sorted_placeholders = sorted(replacement_map.keys(), key=len, reverse=True)
        
        for placeholder in sorted_placeholders:
            if placeholder in replacement_map:
                result = result.replace(placeholder, replacement_map[placeholder])
        
        return result
    
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