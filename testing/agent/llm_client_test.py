import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from agent.llm_client import call_llm


def test_llm():
    """Smoke test — sends a minimal message and prints the response."""
    reply = call_llm(
        system_prompt="You are a helpful assistant.",
        user_message="Reply with exactly: LLM connection successful.",
    )
    print(reply)


if __name__ == "__main__":
    test_llm()
