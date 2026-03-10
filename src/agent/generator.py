import json
from .llm_client import call_llm

# ── Generator ──────────────────────────────────────────────────────────────────
# Receives the structured plan from the Planner and returns parameterized SQL.
#
# Generated shape:
# {
#   "sql":          str,             # parameterized SQL string (%s placeholders)
#   "params":       list,            # values for a single execute()
#   "batch_params": list[list],      # values for executemany() — empty if not batch
#   "is_batch":     bool,
# }
#
# INSERT is built deterministically — no LLM needed because the Planner already
# extracted exact column names and values.
# SELECT uses an LLM call to handle joins and complex filtering.
# ──────────────────────────────────────────────────────────────────────────────

_SELECT_SYSTEM_PROMPT = """\
You are the SQL Generator for a band inventory database agent. Given a SELECT plan,
generate a valid parameterized PostgreSQL SELECT statement.

─── SCHEMA ─────────────────────────────────────────────────────────────────────

students(student_id PK, first_name, last_name, grade)
instrument_inventory(serial_number PK, instrument_name FK→instruments, condition)
checkout_history(checkout_id PK, student_id FK→students, serial_number FK→instrument_inventory,
                 checkout_date, return_date — NULL means currently checked out)
music(music_id PK, title, composer, difficulty)
plays(student_id FK→students, instrument_name FK→instruments)
arranged_for(music_id FK→music, instrument_name FK→instruments, parts_needed)
instruments(instrument_name PK, family_id FK→instrument_family)
instrument_family(family_id PK, family_name)

─── RULES ──────────────────────────────────────────────────────────────────────

1. Use %s placeholders for ALL filter values — never put values directly in SQL.
2. Join tables as needed. Use short aliases (s, ii, ch, m, p, af).
3. Special filter "checked_out": true → WHERE ch.return_date IS NULL (no %s needed).
4. Empty filters dict → no WHERE clause; return all rows from the entity table.
5. SELECT the most useful columns for the query — avoid SELECT * on joined queries.
6. Return ONLY valid JSON, no markdown, no explanation:
   {"sql": "SELECT ...", "params": [value, ...]}\
"""


def generate(plan: dict) -> dict:
    """
    Produce a parameterized SQL query from a structured plan.

    Dispatches to the appropriate generator based on plan intent.
    Returns a generated dict (see shape above).
    """
    print(f"[Generator] received plan: intent={plan['intent']}, entity={plan['entity']}, "
          f"is_batch={plan['is_batch']}")

    if plan["intent"] == "INSERT":
        return _generate_insert(plan)

    if plan["intent"] == "SELECT":
        return _generate_select(plan)

    raise NotImplementedError(f"Generator does not yet support intent: {plan['intent']!r}")


# ── INSERT ─────────────────────────────────────────────────────────────────────

def _generate_insert(plan: dict) -> dict:
    """
    Build a parameterized INSERT from the plan's entity and records.

    Column names come directly from the Planner's record keys, so the SQL
    reflects exactly what was extracted.  The Validator will confirm the
    table and columns are whitelisted before anything is executed.
    """
    entity = plan["entity"]
    records = plan["records"]

    columns = list(records[0].keys())
    col_list = ", ".join(columns)
    placeholders = ", ".join(["%s"] * len(columns))
    sql = f"INSERT INTO {entity} ({col_list}) VALUES ({placeholders})"

    if plan["is_batch"]:
        batch_params = [[rec[col] for col in columns] for rec in records]
        return {
            "sql": sql,
            "params": [],
            "batch_params": batch_params,
            "is_batch": True,
        }

    params = [records[0][col] for col in columns]
    return {
        "sql": sql,
        "params": params,
        "batch_params": [],
        "is_batch": False,
    }


# ── SELECT ─────────────────────────────────────────────────────────────────────

def _generate_select(plan: dict) -> dict:
    """
    Use an LLM to build a parameterized SELECT from the plan's entity and filters.

    The LLM handles JOINs, WHERE clauses, and special flags like checked_out.
    Returns a generated dict with the SQL string and ordered params list.
    """
    user_message = json.dumps({
        "entity": plan["entity"],
        "filters": plan["filters"],
    })

    raw = call_llm(system_prompt=_SELECT_SYSTEM_PROMPT, user_message=user_message)

    try:
        parsed = json.loads(_strip_markdown(raw))
        sql = parsed["sql"]
        params = parsed.get("params", [])
    except (json.JSONDecodeError, KeyError):
        # Fall back to a safe no-filter query on the entity table
        print(f"[Generator] failed to parse SELECT response, falling back to full table scan")
        sql = f"SELECT * FROM {plan['entity']}"
        params = []

    print(f"[Generator] sql: {sql!r}, params: {params}")
    return {
        "sql": sql,
        "params": params,
        "batch_params": [],
        "is_batch": False,
    }


def _strip_markdown(text: str) -> str:
    """Remove ```json ... ``` fences if the LLM wrapped its response in them."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1] == "```" else lines[1:])
    return text.strip()


# ── Standalone test ────────────────────────────────────────────────────────────

def test_generator():
    """Run the generator against INSERT and SELECT plans and print results."""
    plans = [
        ("single INSERT", {
            "intent": "INSERT", "entity": "students", "is_batch": False,
            "records": [{"first_name": "Emma", "last_name": "Rodriguez", "grade": 10}],
            "filters": {}, "requires_clarification": False, "clarification_question": None,
        }),
        ("batch INSERT", {
            "intent": "INSERT", "entity": "students", "is_batch": True,
            "records": [
                {"first_name": "Jake", "last_name": "Alvarez", "grade": 11},
                {"first_name": "Maria", "last_name": "Chen", "grade": 9},
            ],
            "filters": {}, "requires_clarification": False, "clarification_question": None,
        }),
        ("SELECT all students", {
            "intent": "SELECT", "entity": "students", "is_batch": False,
            "records": [], "filters": {},
            "requires_clarification": False, "clarification_question": None,
        }),
        ("SELECT by grade", {
            "intent": "SELECT", "entity": "students", "is_batch": False,
            "records": [], "filters": {"grade": 11},
            "requires_clarification": False, "clarification_question": None,
        }),
        ("SELECT students who play clarinet", {
            "intent": "SELECT", "entity": "students", "is_batch": False,
            "records": [], "filters": {"instrument_name": "clarinet"},
            "requires_clarification": False, "clarification_question": None,
        }),
        ("SELECT currently checked out", {
            "intent": "SELECT", "entity": "checkout_history", "is_batch": False,
            "records": [], "filters": {"checked_out": True},
            "requires_clarification": False, "clarification_question": None,
        }),
    ]

    for label, p in plans:
        print(f"\n--- {label}")
        result = generate(p)
        print(f"    sql:    {result['sql']}")
        print(f"    params: {result['params']}")


if __name__ == "__main__":
    test_generator()
