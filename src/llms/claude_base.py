import logging
import anthropic
from dotenv import load_dotenv
from logging_utils import shorten_for_logging


load_dotenv()


def call_claude_base(
    prompt: str,
    model: str,
    max_tokens: int,
    stop_sequences: list[str],
    temperature: float = 0.7,
) -> str:
    """Call the Claude Completions API with constructed prompt."""

    logging.info(f"Sending request to Claude Completions API...")
    logging.info(f"  Prompt: {shorten_for_logging(prompt)}")
    logging.info(f"  Model: {model}")
    logging.info(f"  Max tokens: {max_tokens}")
    logging.info(f"  Temperature: {temperature}")

    client = anthropic.Anthropic()

    response = client.completions.create(
        model=model,
        max_tokens_to_sample=max_tokens,
        temperature=temperature,
        prompt=prompt,
        stop_sequences=stop_sequences,
    )

    response_text = response.completion
    stop_reason = response.stop_reason

    logging.info(
        f"Claude Completions API response: {shorten_for_logging(response_text)}"
    )

    # Check that we stopped at the expected sequence
    if stop_reason != "stop_sequence":
        raise RuntimeError(
            f"API call did not complete properly. Completion: {response_text}. Stop reason: {stop_reason}. Expected stop sequences: {stop_sequences}"
        )

    return response_text
