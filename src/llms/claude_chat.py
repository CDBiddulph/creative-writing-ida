import logging
import anthropic
from dotenv import load_dotenv
from logging_utils import shorten_for_logging


load_dotenv()


def call_claude_chat(
    system_prompt: str,
    messages: list[dict[str, str]],
    model: str,
    max_tokens: int,
    stop_sequences: list[str],
    temperature: float = 0.7,
) -> str:
    """Call the Claude API in base model mode using CLI simulation."""
    logging.info(f"Sending request to Claude Base Model API...")
    logging.info(f"  Messages:")
    for message in messages:
        logging.info(
            f"    {message['role']}: {shorten_for_logging(message['content'])}"
        )
    logging.info(f"  Model: {model}")
    logging.info(f"  Max tokens: {max_tokens}")
    logging.info(f"  Temperature: {temperature}")

    client = anthropic.Anthropic()

    response = client.messages.create(
        messages=messages,
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=system_prompt,
        stop_sequences=stop_sequences,
    )

    if len(response.content) != 1:
        raise ValueError(f"Unexpected response format from Claude API: {response}")

    response_text = response.content[0].text
    stop_reason = response.stop_reason

    logging.info(
        f"Claude Base Model API response: {shorten_for_logging(response_text)}"
    )

    # Check that we stopped at the expected sequence
    if stop_reason != "stop_sequence":
        raise RuntimeError(
            f"API call did not complete properly. Completion: {response_text}. Stop reason: {stop_reason}. Expected stop sequences: {stop_sequences}"
        )

    return response_text
