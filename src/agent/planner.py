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
UPDATE — director wants to change existing data ("update", "change", "set",
         "mark", "rename", "move to grade", "fix", "correct")
DELETE — director wants to remove existing data ("remove", "delete", "drop",
         "take out", "get rid of")

─── SCHEMA ─────────────────────────────────────────────────────────────────────

students:             student_id, first_name, last_name, grade (9-12)
instrument_inventory: serial_number, instrument_name, condition (good/fair/damaged/retired)
checkout_history:     checkout_id, student_id, serial_number, checkout_date, return_date
                      (return_date is NULL while the instrument is still checked out)
music:                music_id, title, composer, difficulty (1-6)
plays:                student_id, instrument_name  (which student plays which instrument)
arranged_for:         music_id, instrument_name, parts_needed
instruments:          instrument_name, family_id  (reference table linking instruments to families)
instrument_family:    family_id, family_name  (e.g. Woodwinds, Brass, Strings, Percussion)

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

─── UPDATE RULES ───────────────────────────────────────────────────────────────

1. Set "intent" to "UPDATE" and "is_batch" to false.
2. Populate "filters" with the conditions that identify which row(s) to change,
   using exact column names from the schema. This becomes the WHERE clause.
   - REQUIRED: if no filter can be determined, set "requires_clarification" to
     true — never generate an unfiltered UPDATE.
3. Populate "updates" with the fields to change and their new values. This
   becomes the SET clause. Use exact column names from the schema.
4. Leave "records" as [].

─── DELETE RULES ───────────────────────────────────────────────────────────────

1. Set "intent" to "DELETE" and "is_batch" to false.
2. Populate "filters" with the conditions that identify which row(s) to remove.
   This becomes the WHERE clause.
   - REQUIRED: if no filter can be determined, set "requires_clarification" to
     true — never generate an unfiltered DELETE.
3. Leave "records" as [] and "updates" as {}.

─── GENERAL RULES ──────────────────────────────────────────────────────────────

- Always extract field values exactly as stated by the user, even if a value
  appears out of range or invalid (e.g. grade 8, difficulty 9). Do NOT set
  "requires_clarification" for values that are present but seem wrong — field
  validation is handled by a downstream stage. Only set "requires_clarification"
  if a required field is completely absent from the request.
- If a required field cannot be determined at all, set "requires_clarification"
  to true and provide a specific question in "clarification_question".
- Return ONLY valid JSON — no markdown, no explanation, no extra text.

─── OUTPUT FORMAT ──────────────────────────────────────────────────────────────

{
  "intent": "INSERT" | "SELECT" | "UPDATE" | "DELETE",
  "entity": "<table_name>",
  "is_batch": false,
  "records": [],
  "filters": {},
  "updates": {},
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
    raw = _strip_markdown(raw)

    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        return {
            "intent": "unknown",
            "entity": "",
            "is_batch": False,
            "records": [],
            "filters": {},
            "updates": {},
            "requires_clarification": True,
            "clarification_question": "I couldn't understand that request. Could you rephrase it?",
        }

    print(f"[Planner] plan: {result}")
    return result


def _strip_markdown(text: str) -> str:
    """Remove ```json ... ``` fences if the LLM wrapped its response in them."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
    return text.strip()

