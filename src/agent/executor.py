from database.connection import get_connection

# ── Executor ───────────────────────────────────────────────────────────────────
# Receives validated, parameterized SQL and executes it against the database.
# Single ops use cursor.execute(); batch ops use cursor.executemany() inside a
# transaction so failures roll back the entire batch.
#
# Returns:
# {
#   "success":       bool,
#   "rows_affected": int,        # INSERT / UPDATE / DELETE
#   "results":       list[dict], # SELECT rows; empty for write ops
#   "error":         str | None,
# }
# ──────────────────────────────────────────────────────────────────────────────


def execute(generated: dict) -> dict:
    """
    Run parameterized SQL against the Neon Postgres database.

    SELECT:       fetches rows, no commit.
    INSERT single: execute + commit.
    INSERT batch:  executemany inside a transaction; any failure rolls back all rows.
    Returns an execution result dict (see shape above).
    """
    sql = generated["sql"]
    is_select = sql.strip().upper().startswith("SELECT")
    print(f"[Executor] received SQL: {sql!r}, is_batch={generated['is_batch']}")

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if is_select:
                results = _execute_select(cur, sql, generated["params"])
                print(f"[Executor] success — {len(results)} row(s) returned")
                return {
                    "success": True,
                    "rows_affected": 0,
                    "results": results,
                    "error": None,
                }
            elif generated["is_batch"]:
                rows_affected = _execute_batch(cur, sql, generated["batch_params"])
            else:
                rows_affected = _execute_single(cur, sql, generated["params"])

        conn.commit()
        print(f"[Executor] success — rows affected: {rows_affected}")
        return {
            "success": True,
            "rows_affected": rows_affected,
            "results": [],
            "error": None,
        }
    except Exception as e:
        conn.rollback()
        print(f"[Executor] error — rolling back: {e}")
        return {
            "success": False,
            "rows_affected": 0,
            "results": [],
            "error": str(e),
        }
    finally:
        conn.close()


# ── Helpers ────────────────────────────────────────────────────────────────────

def _execute_select(cur, sql: str, params: list) -> list[dict]:
    """Execute a SELECT and return rows as a list of dicts keyed by column name."""
    cur.execute(sql, params)
    columns = [desc[0] for desc in cur.description]
    return [dict(zip(columns, row)) for row in cur.fetchall()]


def _execute_single(cur, sql: str, params: list) -> int:
    """Execute one write statement and return the number of rows affected."""
    cur.execute(sql, params)
    return cur.rowcount


def _execute_batch(cur, sql: str, batch_params: list[list]) -> int:
    """Execute a batch write statement and return the total number of rows affected."""
    cur.executemany(sql, batch_params)
    return cur.rowcount


# ── Standalone test ────────────────────────────────────────────────────────────

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
