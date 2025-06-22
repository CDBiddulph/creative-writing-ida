import logging
import anthropic
from dotenv import load_dotenv
from src.logging_utils import shorten_for_logging
from .api_response import LlmResponse


load_dotenv()


def call_claude_base(
    prompt: str,
    model: str,
    max_tokens: int,
    stop_sequences: list[str],
    temperature: float = 0.7,
) -> LlmResponse:
    """Call the Claude Completions API with constructed prompt.
    
    Returns:
        LlmResponse containing the response text and the stop sequence that ended generation.
        
    Raises:
        RuntimeError: If the API doesn't stop at one of the expected sequences.
    """

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
    # The API provides stop_sequence attribute when stopped by a stop sequence
    stop_sequence = response.stop_sequence

    logging.info(
        f"Claude Completions API response: {shorten_for_logging(response_text)}"
    )

    # Check that we stopped at the expected sequence
    if stop_reason != "stop_sequence":
        raise RuntimeError(
            f"API call did not complete properly. Completion: {response_text}. Stop reason: {stop_reason}. Expected stop sequences: {stop_sequences}"
        )
    
    # Check that we have a valid stop sequence
    if stop_sequence is None:
        raise RuntimeError(
            f"API stopped with 'stop_sequence' reason but no stop sequence provided. Completion: {response_text}. Expected stop sequences: {stop_sequences}"
        )

    return LlmResponse(text=response_text, stop_sequence=stop_sequence)
