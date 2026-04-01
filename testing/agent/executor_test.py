import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from agent.executor import execute


def test_executor():
    """Test INSERT (single + batch) and SELECT against the live database."""
    single_insert = {
        "sql": "INSERT INTO students (first_name, last_name, grade) VALUES (%s, %s, %s)",
        "params": ["Test", "Student", 10],
        "batch_params": [],
        "is_batch": False,
    }
    batch_insert = {
        "sql": "INSERT INTO students (first_name, last_name, grade) VALUES (%s, %s, %s)",
        "params": [],
        "batch_params": [
            ["Batch", "One", 9],
            ["Batch", "Two", 11],
            ["Batch", "Three", 12],
        ],
        "is_batch": True,
    }
    select_all = {
        "sql": "SELECT * FROM students",
        "params": [],
        "batch_params": [],
        "is_batch": False,
    }
    select_filtered = {
        "sql": "SELECT * FROM students WHERE grade = %s",
        "params": [10],
        "batch_params": [],
        "is_batch": False,
    }
    cleanup = {
        "sql": "DELETE FROM students WHERE last_name IN (%s, %s, %s, %s)",
        "params": ["Student", "One", "Two", "Three"],
        "batch_params": [],
        "is_batch": False,
    }

    print("\n--- single INSERT")
    print(execute(single_insert))

    print("\n--- batch INSERT")
    print(execute(batch_insert))

    print("\n--- SELECT all students")
    result = execute(select_all)
    print(f"  returned {len(result['results'])} row(s): {result['results'][:2]} ...")

    print("\n--- SELECT grade 10 students")
    result = execute(select_filtered)
    print(f"  returned {len(result['results'])} row(s): {result['results']}")

    print("\n--- cleanup")
    print(execute(cleanup))


if __name__ == "__main__":
    test_executor()
