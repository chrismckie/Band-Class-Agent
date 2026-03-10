import json
from .llm_client import call_llm

# ── Formatter ──────────────────────────────────────────────────────────────────
# Final stage of the pipeline.  Receives the enriched result dict from run()
# and returns a natural language string addressed to the band director.
#
# Uses an LLM for success responses and validation errors (where phrasing
# matters).  Returns a plain string for DB-level errors (system failures should
# be consistent, not creative).
# ──────────────────────────────────────────────────────────────────────────────

# Maximum rows passed to the LLM for SELECT responses; avoids token bloat on
# large result sets while still giving the model enough data to summarize.
_MAX_DISPLAY_ROWS = 25

_INSERT_SYSTEM_PROMPT = """\
You are a friendly assistant for a high school band director. The director just
added data to their inventory system. Confirm what was done in 1-2 sentences.

Use plain English — no SQL, no technical terms, no mention of "tables" or
"databases". Use the terms the director used: students, instruments, music, etc.
Include names or counts where available.\
"""

_SELECT_SYSTEM_PROMPT = """\
You are a friendly assistant for a high school band director. The director asked
a question about their inventory and you have the results.

Present the data clearly and concisely. Guidelines:
- If results are empty, say so plainly and suggest why there might be no matches.
- For a small number of results (1-5), list them by name or key detail.
- For larger results, give a summary (count + notable details).
- Use plain English — no SQL, no column names as-is, no mention of "tables".
- Format lists with line breaks if there are multiple items.
- If results were capped, mention how many total were found.\
"""

_ERROR_SYSTEM_PROMPT = """\
You are a friendly assistant for a high school band director. Their request could
not be completed. Explain what went wrong in 1-2 sentences using plain English.

Do not repeat the raw error message verbatim. Do not mention SQL or databases.
Tell them what to fix or try instead.\
"""


def format_response(result: dict) -> str:
    """
    Convert a pipeline result dict into a natural language response.

    Expects result to include 'plan' and 'user_input' keys (added by run()).
    Returns a plain string to show to the band director.
    """
    if result["success"]:
        return _format_success(result)

    if not result.get("plan"):
        return "Something went wrong on our end. Please try again."

    return _format_failure(result)


# ── Success ────────────────────────────────────────────────────────────────────

def _format_success(result: dict) -> str:
    intent = result["plan"]["intent"]
    if intent == "SELECT":
        return _format_select_success(result)
    return _format_insert_success(result)


def _format_insert_success(result: dict) -> str:
    plan = result["plan"]
    context = {
        "original_request": result["user_input"],
        "operation": plan["intent"],
        "entity": plan["entity"],
        "records": plan["records"],
        "rows_affected": result["rows_affected"],
    }
    return call_llm(
        system_prompt=_INSERT_SYSTEM_PROMPT,
        user_message=json.dumps(context),
    )


def _format_select_success(result: dict) -> str:
    plan = result["plan"]
    all_rows = result["results"]
    total_count = len(all_rows)
    displayed_rows = all_rows[:_MAX_DISPLAY_ROWS]

    context = {
        "original_request": result["user_input"],
        "entity": plan["entity"],
        "filters": plan["filters"],
        "total_found": total_count,
        "rows_shown": len(displayed_rows),
        "capped": total_count > _MAX_DISPLAY_ROWS,
        "results": displayed_rows,
    }
    return call_llm(
        system_prompt=_SELECT_SYSTEM_PROMPT,
        user_message=json.dumps(context),
    )


# ── Failure ────────────────────────────────────────────────────────────────────

def _format_failure(result: dict) -> str:
    plan = result["plan"]
    context = {
        "original_request": result["user_input"],
        "operation": plan.get("intent", "unknown"),
        "entity": plan.get("entity", "unknown"),
        "error_message": result.get("error", "Unknown error."),
    }
    return call_llm(
        system_prompt=_ERROR_SYSTEM_PROMPT,
        user_message=json.dumps(context),
    )


# ── Standalone test ────────────────────────────────────────────────────────────

def test_formatter():
    """Test the formatter against INSERT success, SELECT success, and failure shapes."""
    insert_plan = {
        "intent": "INSERT", "entity": "students", "is_batch": False,
        "records": [{"first_name": "Emma", "last_name": "Rodriguez", "grade": 10}],
        "filters": {}, "requires_clarification": False, "clarification_question": None,
    }
    select_plan = {
        "intent": "SELECT", "entity": "students", "is_batch": False,
        "records": [], "filters": {"grade": 11},
        "requires_clarification": False, "clarification_question": None,
    }

    cases = [
        (
            "INSERT success",
            {"success": True, "rows_affected": 1, "results": [], "error": None,
             "plan": insert_plan,
             "user_input": "Add Emma Rodriguez, a 10th grader, to the student list."},
        ),
        (
            "SELECT with results",
            {"success": True, "rows_affected": 0, "error": None,
             "results": [
                 {"student_id": 1, "first_name": "Jake", "last_name": "Alvarez", "grade": 11},
                 {"student_id": 2, "first_name": "Maria", "last_name": "Chen", "grade": 11},
             ],
             "plan": select_plan,
             "user_input": "Which students are in grade 11?"},
        ),
        (
            "SELECT with no results",
            {"success": True, "rows_affected": 0, "results": [], "error": None,
             "plan": select_plan,
             "user_input": "Which students are in grade 11?"},
        ),
        (
            "validation failure",
            {"success": False, "rows_affected": 0, "results": [],
             "error": "Record 1: grade must be an integer between 9 and 12 (got 8).",
             "plan": insert_plan,
             "user_input": "Add Tom Smith, an 8th grader, to the student list."},
        ),
    ]

    for label, result in cases:
        print(f"\n--- {label}")
        print(format_response(result))


if __name__ == "__main__":
    test_formatter()
