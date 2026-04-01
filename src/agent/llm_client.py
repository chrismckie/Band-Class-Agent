import os
import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1024


def get_client():
    """Return an Anthropic client using ANTHROPIC_API_KEY from .env."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is not set in .env")
    return anthropic.Anthropic(api_key=api_key)


def call_llm(system_prompt: str, user_message: str, max_tokens: int = MAX_TOKENS) -> str:
    """
    Send a single-turn message to Claude and return the response text.

    Args:
        system_prompt: Instructions that define the LLM's role/behavior.
        user_message:  The user's input for this call.
        max_tokens:    Maximum tokens in the response.

    Returns:
        The assistant's response as a plain string.

    Raises:
        RuntimeError: If the API call fails for any reason (network, auth, rate limit, etc.)
    """
    try:
        client = get_client()
        response = client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        return response.content[0].text
    except Exception as e:
        raise RuntimeError(f"LLM call failed: {e}") from e
