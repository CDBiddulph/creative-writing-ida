"""Data models for tree simulation sessions and responses."""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from datetime import datetime


@dataclass
class AskResponse:
    """Represents an ask/response pair within a session."""
    ask: str
    response: str
    response_session_id: int


@dataclass
class Session:
    """Represents a single session with prompt and potentially multiple ask/response cycles."""
    id: int
    prompt: str
    responding_to_id: Optional[int] = None  # Which session this is responding to
    notes: List[str] = field(default_factory=list)
    ask_responses: List[AskResponse] = field(default_factory=list)
    final_submit: str = ""
    
    def add_note(self, note: str) -> None:
        """Add a note to the session."""
        self.notes.append(note)
    
    def add_ask_response(self, ask: str, response: str, response_session_id: int) -> None:
        """Add an ask/response pair."""
        self.ask_responses.append(AskResponse(ask, response, response_session_id))
    
    def set_final_submit(self, submit: str) -> None:
        """Set the final submission."""
        self.final_submit = submit
    
    def to_xml(self) -> str:
        """Convert session to XML format."""
        xml = "<session>\n"
        
        # Add response-id if this session is responding to another
        if self.responding_to_id is not None:
            xml += f"  <response-id>{self.responding_to_id}</response-id>\n"
        
        # Add prompt
        xml += f"  <prompt>{self.prompt}</prompt>\n"
        
        # Add notes and ask/response cycles
        note_idx = 0
        for i, ask_resp in enumerate(self.ask_responses):
            # Add note before ask if available
            if note_idx < len(self.notes):
                xml += f"  <notes>\n    {self.notes[note_idx]}\n  </notes>\n"
                note_idx += 1
            
            xml += f"  <ask>\n    {ask_resp.ask}\n  </ask>\n"
            xml += f"  <response-id>{ask_resp.response_session_id}</response-id>\n"
            xml += f"  <response>\n    {ask_resp.response}\n  </response>\n"
        
        # Add any remaining notes
        while note_idx < len(self.notes):
            xml += f"  <notes>\n    {self.notes[note_idx]}\n  </notes>\n"
            note_idx += 1
        
        # Add final submit if present
        if self.final_submit:
            xml += f"  <submit>{self.final_submit}</submit>\n"
        
        xml += "</session>"
        return xml


@dataclass 
class TreeNode:
    """Represents a node in the hierarchical tree."""
    session: Session
    children: List['TreeNode'] = field(default_factory=list)
    parent: Optional['TreeNode'] = None
    depth: int = 0
    is_leaf: bool = False
    
    def add_child(self, child_node: 'TreeNode') -> None:
        """Add a child node."""
        child_node.parent = self
        child_node.depth = self.depth + 1
        self.children.append(child_node)
    
    def get_all_sessions_preorder(self) -> List[Session]:
        """Get all sessions in pre-order traversal."""
        sessions = [self.session]
        for child in self.children:
            sessions.extend(child.get_all_sessions_preorder())
        return sessions


class SessionIDManager:
    """Manages session ID assignment."""
    
    def __init__(self):
        self._next_id = 0
    
    def get_next_id(self) -> int:
        """Get the next available session ID."""
        session_id = self._next_id
        self._next_id += 1
        return session_id
    
    def reset(self) -> None:
        """Reset ID counter."""
        self._next_id = 0


def generate_session_filename() -> str:
    """Generate a timestamped filename for session output."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"session_{timestamp}.xml"