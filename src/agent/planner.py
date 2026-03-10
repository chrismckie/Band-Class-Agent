import json
from .llm_client import call_llm

# ── Planner ────────────────────────────────────────────────────────────────────
# Receives raw user input and returns a structured plan dict that describes
# what the user wants to do.  The Generator reads this plan to build SQL.
#
# Plan shape:
# {
#   "intent":                 "INSERT" | "SELECT" | "UPDATE" | "DELETE",
#   "entity":                 "students" | "instrument_inventory" | "checkout_history"
#                             | "music" | "plays" | "arranged_for",
#   "is_batch":               bool,
#   "records":                [{"field": value, ...}, ...],   # INSERT only
#   "filters":                {"field": value, ...},          # SELECT only; {} means no filter (return all)
#   "requires_clarification": bool,
#   "clarification_question": str | None,
# }
# ──────────────────────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are the Planner for a band inventory database agent. A band director will give
you a natural language request. Your job is to analyze the request and return a
structured JSON plan so the next stage can generate the correct SQL.

─── SUPPORTED OPERATIONS ───────────────────────────────────────────────────────

INSERT — director wants to add new data ("add", "create", "register", "put in")
SELECT — director wants to look something up ("show", "list", "find", "how many",
         "which", "what", "do we have", "who")

─── SCHEMA ─────────────────────────────────────────────────────────────────────

students:             student_id, first_name, last_name, grade (9-12)
instrument_inventory: serial_number, instrument_name, condition (good/fair/damaged/retired)
checkout_history:     checkout_id, student_id, serial_number, checkout_date, return_date
                      (return_date is NULL while the instrument is still checked out)
music:                music_id, title, composer, difficulty (1-6)
plays:                student_id, instrument_name  (which student plays which instrument)
arranged_for:         music_id, instrument_name, parts_needed

─── INSERT RULES ───────────────────────────────────────────────────────────────

1. Set "is_batch" to true if the request contains multiple records.
2. Each entry in "records" must use the exact column names from the schema above.
3. Required fields by table:
   - students:             first_name, last_name, grade
   - instrument_inventory: serial_number, instrument_name  (condition defaults to "good")
   - music:                title  (composer and difficulty are optional)
4. Leave "filters" as {}.

─── SELECT RULES ───────────────────────────────────────────────────────────────

1. Set "intent" to "SELECT" and "is_batch" to false.
2. Set "entity" to the primary table being queried.
3. Populate "filters" with any conditions the director mentioned, using exact
   column names from the schema. Examples:
   - "grade 10 students"       → {"grade": 10}
   - "trumpets in fair condition" → {"instrument_name": "trumpet", "condition": "fair"}
   - "currently checked out"   → {"checked_out": true}   ← special flag for return_date IS NULL
   - "difficulty 3 pieces"     → {"difficulty": 3}
   - "students who play flute" → entity "students", filters {"instrument_name": "flute"}
4. If the director wants everything with no conditions, leave "filters" as {}.
5. Leave "records" as [].

─── GENERAL RULES ──────────────────────────────────────────────────────────────

- If a required field cannot be determined, set "requires_clarification" to true
  and provide a specific question in "clarification_question".
- Return ONLY valid JSON — no markdown, no explanation, no extra text.

─── OUTPUT FORMAT ──────────────────────────────────────────────────────────────

{
  "intent": "INSERT" | "SELECT",
  "entity": "<table_name>",
  "is_batch": false,
  "records": [],
  "filters": {},
  "requires_clarification": false,
  "clarification_question": null
}\
"""


def plan(user_input: str) -> dict:
    """
    Classify the user's intent and extract structured data from their request.

    Calls the LLM to parse natural language into a machine-readable plan.
    Returns a plan dict (see shape above).
    """
    print(f"[Planner] received: {user_input!r}")

    raw = call_llm(system_prompt=_SYSTEM_PROMPT, user_message=user_input)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "intent": "unknown",
            "entity": "",
            "is_batch": False,
            "records": [],
            "filters": {},
            "requires_clarification": True,
            "clarification_question": "I couldn't understand that request. Could you rephrase it?",
        }

    print(f"[Planner] plan: {result}")
    return result


# ── Standalone test ────────────────────────────────────────────────────────────

def test_planner():
    """Run the planner against INSERT and SELECT prompts and print each result."""
    prompts = [
        # INSERT
        "Add Emma Rodriguez, a 10th grader, to the student list.",
        "Add a new trumpet to inventory with serial number TR-4821, condition is fair.",
        "Add these students: Jake Alvarez grade 11, Maria Chen grade 9, Devon Hill grade 12.",
        "Add the piece Commando March by Karl King, difficulty 3.",
        # SELECT
        "Show me all students.",
        "Which students are in grade 11?",
        "How many trumpets do we have in good condition?",
        "Show me all pieces with difficulty 4.",
        "Which students play clarinet?",
        "What instruments are currently checked out?",
    ]
    for prompt in prompts:
        print(f"\n--- prompt: {prompt!r}")
        result = plan(prompt)
        print(f"    intent={result['intent']}, entity={result['entity']}, "
              f"filters={result['filters']}, records={result['records']}, "
              f"clarification={result['requires_clarification']}")


if __name__ == "__main__":
    test_planner()
