import json

MAX_LOG_LENGTH = 1000


def shorten_for_logging(text: str, max_length: int = MAX_LOG_LENGTH) -> str:
    """Shorten text to show beginning and end, return as JSON string."""
    if len(text) <= max_length:
        return json.dumps(text)

    # Show beginning and end with ellipsis in middle
    half_length = (max_length - 5) // 2  # Reserve 5 chars for " ... "
    beginning = text[:half_length]
    ending = text[-half_length:]
    new_text = beginning + " ... " + ending
    return json.dumps(new_text)
