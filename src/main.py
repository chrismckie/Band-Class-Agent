from agent.planner import plan
from agent.generator import generate
from agent.validator import validate
from agent.executor import execute
from agent.formatter import format_response

# ── Pipeline ───────────────────────────────────────────────────────────────────
# run()  → structured result dict (used internally and for testing)
# chat() → natural language string (the user-facing interface)
# ──────────────────────────────────────────────────────────────────────────────


def run(user_input: str) -> dict:
    """
    Run the full agent pipeline for a single user request.

    Returns an enriched result dict that always includes 'plan' and 'user_input'
    so the Formatter has full context to generate a natural language response.
    Any unhandled exception (e.g. LLM API failure) is caught here and returned
    as a failed result so the pipeline never crashes to the user.
    """
    try:
        structured_plan = plan(user_input)

        if structured_plan["requires_clarification"]:
            return {
                "success": False,
                "rows_affected": 0,
                "results": [],
                "error": structured_plan["clarification_question"],
                "plan": structured_plan,
                "user_input": user_input,
            }

        generated = generate(structured_plan)
        validation = validate(generated, structured_plan)

        if not validation["is_valid"]:
            return {
                "success": False,
                "rows_affected": 0,
                "results": [],
                "error": " | ".join(validation["errors"]),
                "plan": structured_plan,
                "user_input": user_input,
            }

        result = execute(generated)
        result["plan"] = structured_plan
        result["user_input"] = user_input
        return result

    except Exception as e:
        print(f"[Pipeline] unhandled error: {e}")
        return {
            "success": False,
            "rows_affected": 0,
            "results": [],
            "error": str(e),
            "plan": None,
            "user_input": user_input,
        }


def chat(user_input: str) -> str:
    """
    User-facing entry point. Runs the full pipeline and returns a natural
    language response addressed to the band director.
    """
    result = run(user_input)
    return format_response(result)
