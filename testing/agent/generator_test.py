import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from agent.generator import generate


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
        ("DELETE student by name", {
            "intent": "DELETE", "entity": "students", "is_batch": False,
            "records": [], "filters": {"first_name": "Emma", "last_name": "Rodriguez"},
            "updates": {}, "requires_clarification": False, "clarification_question": None,
        }),
        ("DELETE music by title", {
            "intent": "DELETE", "entity": "music", "is_batch": False,
            "records": [], "filters": {"title": "Commando March"},
            "updates": {}, "requires_clarification": False, "clarification_question": None,
        }),
        ("UPDATE student grade", {
            "intent": "UPDATE", "entity": "students", "is_batch": False,
            "records": [], "filters": {"first_name": "Emma", "last_name": "Rodriguez"},
            "updates": {"grade": 11},
            "requires_clarification": False, "clarification_question": None,
        }),
        ("UPDATE instrument condition", {
            "intent": "UPDATE", "entity": "instrument_inventory", "is_batch": False,
            "records": [], "filters": {"serial_number": "TR-4821"},
            "updates": {"condition": "damaged"},
            "requires_clarification": False, "clarification_question": None,
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
