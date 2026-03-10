from database.connection import get_connection

# ── Validator ─────────────────────────────────────────────────────────────────
# Three-layer validation before any SQL is executed:
#
#   Layer 1 — SQL Safety     (Python rules)
#   Layer 2 — Business Logic (Python rules)
#   Layer 3 — Data Integrity (Python rules + DB lookups)
#
# Returns:
# {
#   "is_valid": bool,
#   "errors":   [str, ...],   # empty list means all checks passed
# }
# ──────────────────────────────────────────────────────────────────────────────

ALLOWED_TABLES = {
    "students", "instrument_inventory", "instrument_family",
    "instruments", "checkout_history", "music", "arranged_for", "plays",
}

ALLOWED_OPERATIONS = {
    "students":             {"INSERT", "SELECT", "UPDATE", "DELETE"},
    "instrument_inventory": {"INSERT", "SELECT", "UPDATE"},
    "instrument_family":    {"SELECT"},
    "instruments":          {"SELECT"},
    "checkout_history":     {"INSERT", "SELECT", "UPDATE"},
    "music":                {"INSERT", "SELECT", "UPDATE", "DELETE"},
    "arranged_for":         {"INSERT", "SELECT", "DELETE"},
    "plays":                {"INSERT", "SELECT", "DELETE"},
}

DANGEROUS_KEYWORDS = {"DROP", "TRUNCATE", "ALTER", "EXEC", "EXECUTE"}

VALID_CONDITIONS = {"good", "fair", "damaged", "retired"}


def validate(generated: dict, plan: dict) -> dict:
    """
    Run all three validation layers against the generated SQL and plan.

    Returns a result dict with is_valid and a list of error strings.
    """
    errors: list[str] = []

    errors += _check_sql_safety(generated["sql"], plan["intent"], plan["entity"], generated["params"])
    errors += _check_business_logic(plan)
    errors += _check_data_integrity(plan)

    is_valid = len(errors) == 0
    print(f"[Validator] is_valid={is_valid}, errors={errors}")
    return {"is_valid": is_valid, "errors": errors}


# ── Layer 1: SQL Safety ────────────────────────────────────────────────────────

def _check_sql_safety(sql: str, intent: str, entity: str, params: list) -> list[str]:
    """Ensure the SQL targets an allowed table, uses no dangerous keywords, and is parameterized."""
    errors: list[str] = []

    if entity not in ALLOWED_TABLES:
        errors.append(f"Table '{entity}' is not allowed.")
        return errors  # no point checking further if the table itself is invalid

    if intent not in ALLOWED_OPERATIONS.get(entity, set()):
        errors.append(f"Operation '{intent}' is not allowed on table '{entity}'.")

    sql_upper = sql.upper()
    for keyword in DANGEROUS_KEYWORDS:
        if keyword in sql_upper:
            errors.append(f"SQL contains forbidden keyword: {keyword}.")

    if intent == "INSERT":
        if "VALUES" in sql_upper and "%s" not in sql:
            errors.append("INSERT statement is not parameterized — VALUES clause must use %s placeholders.")

    if intent == "SELECT":
        if not sql_upper.lstrip().startswith("SELECT"):
            errors.append("Expected a SELECT statement but the generated SQL does not start with SELECT.")
        placeholder_count = sql.count("%s")
        if placeholder_count != len(params):
            errors.append(
                f"SELECT has {placeholder_count} placeholder(s) but {len(params)} param(s) were provided."
            )

    return errors


# ── Layer 2: Business Logic ────────────────────────────────────────────────────

def _check_business_logic(plan: dict) -> list[str]:
    """Enforce domain rules for INSERT records and SELECT filter values."""
    errors: list[str] = []

    if plan["intent"] == "INSERT":
        entity = plan["entity"]
        for i, record in enumerate(plan["records"]):
            label = f"Record {i + 1}" if plan["is_batch"] else "Record"
            if entity == "students":
                errors += _validate_student(record, label)
            elif entity == "instrument_inventory":
                errors += _validate_instrument_inventory(record, label)
            elif entity == "music":
                errors += _validate_music(record, label)

    elif plan["intent"] == "SELECT":
        errors += _validate_select_filters(plan["filters"])

    return errors


def _validate_select_filters(filters: dict) -> list[str]:
    """Check that filter values fall within allowed ranges."""
    errors: list[str] = []

    grade = filters.get("grade")
    if grade is not None:
        if not isinstance(grade, int) or not (9 <= grade <= 12):
            errors.append(f"Filter grade must be between 9 and 12 (got {grade!r}).")

    condition = filters.get("condition")
    if condition is not None:
        if condition not in VALID_CONDITIONS:
            errors.append(
                f"Filter condition '{condition}' is invalid. "
                f"Must be one of: {', '.join(sorted(VALID_CONDITIONS))}."
            )

    difficulty = filters.get("difficulty")
    if difficulty is not None:
        if not isinstance(difficulty, int) or not (1 <= difficulty <= 6):
            errors.append(f"Filter difficulty must be between 1 and 6 (got {difficulty!r}).")

    return errors


def _validate_student(record: dict, label: str) -> list[str]:
    errors: list[str] = []
    if not record.get("first_name", "").strip():
        errors.append(f"{label}: first_name is required.")
    if not record.get("last_name", "").strip():
        errors.append(f"{label}: last_name is required.")
    grade = record.get("grade")
    if grade is None:
        errors.append(f"{label}: grade is required.")
    elif not isinstance(grade, int) or not (9 <= grade <= 12):
        errors.append(f"{label}: grade must be an integer between 9 and 12 (got {grade!r}).")
    return errors


def _validate_instrument_inventory(record: dict, label: str) -> list[str]:
    errors: list[str] = []
    if not record.get("serial_number", "").strip():
        errors.append(f"{label}: serial_number is required.")
    if not record.get("instrument_name", "").strip():
        errors.append(f"{label}: instrument_name is required.")
    condition = record.get("condition", "good")
    if condition not in VALID_CONDITIONS:
        errors.append(
            f"{label}: condition '{condition}' is invalid. Must be one of: {', '.join(sorted(VALID_CONDITIONS))}."
        )
    return errors


def _validate_music(record: dict, label: str) -> list[str]:
    errors: list[str] = []
    if not record.get("title", "").strip():
        errors.append(f"{label}: title is required.")
    difficulty = record.get("difficulty")
    if difficulty is not None:
        if not isinstance(difficulty, int) or not (1 <= difficulty <= 6):
            errors.append(f"{label}: difficulty must be an integer between 1 and 6 (got {difficulty!r}).")
    return errors


# ── Layer 3: Data Integrity ────────────────────────────────────────────────────

def _check_data_integrity(plan: dict) -> list[str]:
    """Check for batch-internal duplicates and FK existence in the database.

    SELECT is intentionally skipped — an empty result set is valid, not an error.
    """
    errors: list[str] = []

    if plan["intent"] != "INSERT":
        return errors

    entity = plan["entity"]
    records = plan["records"]

    if plan["is_batch"]:
        errors += _check_batch_duplicates(entity, records)

    if entity == "instrument_inventory":
        errors += _check_instrument_names_exist([r.get("instrument_name") for r in records])

    return errors


def _check_batch_duplicates(entity: str, records: list[dict]) -> list[str]:
    """Detect duplicate records within a batch before any are inserted."""
    errors: list[str] = []

    # Key fields that define uniqueness per table
    key_fields = {
        "students":             ("first_name", "last_name"),
        "instrument_inventory": ("serial_number",),
        "music":                ("title",),
    }

    fields = key_fields.get(entity)
    if not fields:
        return errors

    seen: set[tuple] = set()
    for i, record in enumerate(records):
        key = tuple(str(record.get(f, "")).strip().lower() for f in fields)
        if key in seen:
            errors.append(
                f"Batch contains duplicate entry at record {i + 1}: "
                f"{', '.join(f'{f}={record.get(f)!r}' for f in fields)}."
            )
        seen.add(key)

    return errors


def _check_instrument_names_exist(instrument_names: list[str]) -> list[str]:
    """Verify each instrument_name exists in the instruments reference table."""
    errors: list[str] = []
    unknown = []

    try:
        conn = get_connection()
        with conn.cursor() as cur:
            for name in instrument_names:
                if not name:
                    continue
                cur.execute(
                    "SELECT 1 FROM instruments WHERE instrument_name = %s",
                    (name,),
                )
                if cur.fetchone() is None:
                    unknown.append(name)
        conn.close()
    except Exception as e:
        errors.append(f"Could not verify instrument names against database: {e}")
        return errors

    for name in unknown:
        errors.append(
            f"Instrument '{name}' does not exist in the instruments table. "
            "Add it there first, or check the spelling."
        )

    return errors


# ── Standalone test ────────────────────────────────────────────────────────────

def test_validator():
    """Test the validator against valid and invalid INSERT and SELECT scenarios."""
    cases = [
        (
            "valid single student",
            {"sql": "INSERT INTO students (first_name, last_name, grade) VALUES (%s, %s, %s)",
             "params": ["Emma", "Rodriguez", 10], "batch_params": [], "is_batch": False},
            {"intent": "INSERT", "entity": "students", "is_batch": False,
             "records": [{"first_name": "Emma", "last_name": "Rodriguez", "grade": 10}],
             "filters": {}, "requires_clarification": False, "clarification_question": None},
        ),
        (
            "invalid grade",
            {"sql": "INSERT INTO students (first_name, last_name, grade) VALUES (%s, %s, %s)",
             "params": ["Tom", "Smith", 8], "batch_params": [], "is_batch": False},
            {"intent": "INSERT", "entity": "students", "is_batch": False,
             "records": [{"first_name": "Tom", "last_name": "Smith", "grade": 8}],
             "filters": {}, "requires_clarification": False, "clarification_question": None},
        ),
        (
            "batch with internal duplicate",
            {"sql": "INSERT INTO students (first_name, last_name, grade) VALUES (%s, %s, %s)",
             "params": [], "batch_params": [["Emma", "Rodriguez", 10], ["Emma", "Rodriguez", 11]],
             "is_batch": True},
            {"intent": "INSERT", "entity": "students", "is_batch": True,
             "records": [{"first_name": "Emma", "last_name": "Rodriguez", "grade": 10},
                         {"first_name": "Emma", "last_name": "Rodriguez", "grade": 11}],
             "filters": {}, "requires_clarification": False, "clarification_question": None},
        ),
        (
            "forbidden keyword",
            {"sql": "DROP TABLE students; INSERT INTO students VALUES (%s)", "params": ["x"],
             "batch_params": [], "is_batch": False},
            {"intent": "INSERT", "entity": "students", "is_batch": False,
             "records": [{"first_name": "x"}],
             "filters": {}, "requires_clarification": False, "clarification_question": None},
        ),
        # SELECT cases
        (
            "valid SELECT all students",
            {"sql": "SELECT * FROM students", "params": [], "batch_params": [], "is_batch": False},
            {"intent": "SELECT", "entity": "students", "is_batch": False,
             "records": [], "filters": {},
             "requires_clarification": False, "clarification_question": None},
        ),
        (
            "valid SELECT with grade filter",
            {"sql": "SELECT * FROM students WHERE grade = %s", "params": [11],
             "batch_params": [], "is_batch": False},
            {"intent": "SELECT", "entity": "students", "is_batch": False,
             "records": [], "filters": {"grade": 11},
             "requires_clarification": False, "clarification_question": None},
        ),
        (
            "invalid SELECT filter grade out of range",
            {"sql": "SELECT * FROM students WHERE grade = %s", "params": [7],
             "batch_params": [], "is_batch": False},
            {"intent": "SELECT", "entity": "students", "is_batch": False,
             "records": [], "filters": {"grade": 7},
             "requires_clarification": False, "clarification_question": None},
        ),
        (
            "invalid SELECT param count mismatch",
            {"sql": "SELECT * FROM students WHERE grade = %s AND last_name = %s",
             "params": [11], "batch_params": [], "is_batch": False},
            {"intent": "SELECT", "entity": "students", "is_batch": False,
             "records": [], "filters": {"grade": 11},
             "requires_clarification": False, "clarification_question": None},
        ),
    ]

    for label, generated, plan in cases:
        print(f"\n--- {label}")
        result = validate(generated, plan)
        status = "PASS" if result["is_valid"] else "FAIL"
        print(f"    {status} — errors: {result['errors']}")


if __name__ == "__main__":
    test_validator()
