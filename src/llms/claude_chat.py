import logging
import anthropic
from dotenv import load_dotenv
from src.logging_utils import shorten_for_logging
from .api_response import LlmResponse


load_dotenv()


def call_claude_chat(
    system_prompt: str,
    messages: list[dict[str, str]],
    model: str,
    max_tokens: int,
    stop_sequences: list[str],
    temperature: float = 0.7,
) -> LlmResponse:
    """Call the Claude API with a chat model simulating a base model using CLI simulation.
    
    Returns:
        LlmResponse containing the response text and the stop sequence that ended generation.
        
    Raises:
        RuntimeError: If the API doesn't stop at one of the expected sequences.
    """
    logging.info(f"Sending request to Claude Chat Model API...")
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
    # The API provides stop_sequence attribute when stopped by a stop sequence
    stop_sequence = response.stop_sequence

    logging.info(
        f"Claude Chat Model API response: {shorten_for_logging(response_text)}"
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
