import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from agent.formatter import format_response


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
    delete_plan = {
        "intent": "DELETE", "entity": "students", "is_batch": False,
        "records": [], "filters": {"last_name": "Rodriguez"}, "updates": {},
        "requires_clarification": False, "clarification_question": None,
    }
    update_plan = {
        "intent": "UPDATE", "entity": "students", "is_batch": False,
        "records": [], "filters": {"last_name": "Rodriguez"}, "updates": {"grade": 11},
        "requires_clarification": False, "clarification_question": None,
    }

    cases = [
        (
            "DELETE success",
            {"success": True, "rows_affected": 1, "results": [], "error": None,
             "plan": delete_plan,
             "user_input": "Remove Emma Rodriguez from the student list."},
        ),
        (
            "UPDATE success",
            {"success": True, "rows_affected": 1, "results": [], "error": None,
             "plan": update_plan,
             "user_input": "Change Emma Rodriguez's grade to 11."},
        ),
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
