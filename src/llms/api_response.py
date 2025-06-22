"""Shared data structures for LLM API responses."""

from dataclasses import dataclass


@dataclass
class LlmResponse:
    """Response from LLM API including text and stop sequence."""
    text: str
    stop_sequence: str