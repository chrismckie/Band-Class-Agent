import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from agent.validator import validate


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
        # DELETE cases
        (
            "valid DELETE student",
            {"sql": "DELETE FROM students WHERE last_name = %s",
             "params": ["Rodriguez"], "batch_params": [], "is_batch": False},
            {"intent": "DELETE", "entity": "students", "is_batch": False,
             "records": [], "filters": {"last_name": "Rodriguez"}, "updates": {},
             "requires_clarification": False, "clarification_question": None},
        ),
        (
            "invalid DELETE no WHERE clause",
            {"sql": "DELETE FROM students",
             "params": [], "batch_params": [], "is_batch": False},
            {"intent": "DELETE", "entity": "students", "is_batch": False,
             "records": [], "filters": {}, "updates": {},
             "requires_clarification": False, "clarification_question": None},
        ),
        (
            "valid DELETE music",
            {"sql": "DELETE FROM music WHERE title = %s",
             "params": ["Commando March"], "batch_params": [], "is_batch": False},
            {"intent": "DELETE", "entity": "music", "is_batch": False,
             "records": [], "filters": {"title": "Commando March"}, "updates": {},
             "requires_clarification": False, "clarification_question": None},
        ),
        # UPDATE cases
        (
            "valid UPDATE student grade",
            {"sql": "UPDATE students SET grade = %s WHERE last_name = %s",
             "params": [11, "Rodriguez"], "batch_params": [], "is_batch": False},
            {"intent": "UPDATE", "entity": "students", "is_batch": False,
             "records": [], "filters": {"last_name": "Rodriguez"}, "updates": {"grade": 11},
             "requires_clarification": False, "clarification_question": None},
        ),
        (
            "invalid UPDATE grade out of range",
            {"sql": "UPDATE students SET grade = %s WHERE last_name = %s",
             "params": [8, "Rodriguez"], "batch_params": [], "is_batch": False},
            {"intent": "UPDATE", "entity": "students", "is_batch": False,
             "records": [], "filters": {"last_name": "Rodriguez"}, "updates": {"grade": 8},
             "requires_clarification": False, "clarification_question": None},
        ),
        (
            "invalid UPDATE no WHERE clause",
            {"sql": "UPDATE students SET grade = %s",
             "params": [11], "batch_params": [], "is_batch": False},
            {"intent": "UPDATE", "entity": "students", "is_batch": False,
             "records": [], "filters": {}, "updates": {"grade": 11},
             "requires_clarification": False, "clarification_question": None},
        ),
        (
            "valid UPDATE instrument condition",
            {"sql": "UPDATE instrument_inventory SET condition = %s WHERE serial_number = %s",
             "params": ["damaged", "TR-4821"], "batch_params": [], "is_batch": False},
            {"intent": "UPDATE", "entity": "instrument_inventory", "is_batch": False,
             "records": [], "filters": {"serial_number": "TR-4821"}, "updates": {"condition": "damaged"},
             "requires_clarification": False, "clarification_question": None},
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
