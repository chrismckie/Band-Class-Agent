from agent.planner import plan
from agent.generator import generate
from agent.validator import validate
from agent.executor import execute
from agent.formatter import format_response
from agent.llm_client import test_llm
from database.connection import get_connection, test_connection

# ── Pipeline ───────────────────────────────────────────────────────────────────
# run()  → structured result dict (used internally and for testing)
# chat() → natural language string (the user-facing interface)
# ──────────────────────────────────────────────────────────────────────────────


def run(user_input: str) -> dict:
    """
    Run the full agent pipeline for a single user request.

    Returns an enriched result dict that always includes 'plan' and 'user_input'
    so the Formatter has full context to generate a natural language response.
    Any unhandled exception (e.g. LLM API failure) is caught here and returned
    as a failed result so the pipeline never crashes to the user.
    """
    try:
        structured_plan = plan(user_input)

        if structured_plan["requires_clarification"]:
            return {
                "success": False,
                "rows_affected": 0,
                "results": [],
                "error": structured_plan["clarification_question"],
                "plan": structured_plan,
                "user_input": user_input,
            }

        generated = generate(structured_plan)
        validation = validate(generated, structured_plan)

        if not validation["is_valid"]:
            return {
                "success": False,
                "rows_affected": 0,
                "results": [],
                "error": " | ".join(validation["errors"]),
                "plan": structured_plan,
                "user_input": user_input,
            }

        result = execute(generated)
        result["plan"] = structured_plan
        result["user_input"] = user_input
        return result

    except Exception as e:
        print(f"[Pipeline] unhandled error: {e}")
        return {
            "success": False,
            "rows_affected": 0,
            "results": [],
            "error": str(e),
            "plan": None,
            "user_input": user_input,
        }


def chat(user_input: str) -> str:
    """
    User-facing entry point. Runs the full pipeline and returns a natural
    language response addressed to the band director.
    """
    result = run(user_input)
    return format_response(result)


# ── Integration test ───────────────────────────────────────────────────────────

def test_integration():
    """
    End-to-end INSERT integration test.

    Runs three prompts through the full pipeline (single student, batch students,
    single music record), verifies each row landed in the database, then removes
    all test data so the DB is left unchanged.
    """
    print("\n=== Integration test: INSERT ===")
    passed = 0
    failed = 0

    # ── Case 1: single student ────────────────────────────────────────────────
    _print_case("1: single student INSERT")
    result = run("Add Integration Test, a 10th grader, to the student list.")
    print(f"  Response: {format_response(result)}")
    if _assert_success(result):
        if _assert_row_exists(
            "SELECT 1 FROM students WHERE first_name = %s AND last_name = %s",
            ("Integration", "Test"),
            "students row",
        ):
            passed += 1
        else:
            failed += 1
    else:
        failed += 1

    # ── Case 2: batch students ────────────────────────────────────────────────
    _print_case("2: batch student INSERT")
    result = run(
        "Add these students: "
        "Batch Alpha grade 9, Batch Beta grade 11, Batch Gamma grade 12."
    )
    print(f"  Response: {format_response(result)}")
    if _assert_success(result):
        if _assert_row_exists(
            "SELECT COUNT(*) FROM students WHERE last_name IN (%s, %s, %s)",
            ("Alpha", "Beta", "Gamma"),
            "3 batch rows",
            expected_count=3,
        ):
            passed += 1
        else:
            failed += 1
    else:
        failed += 1

    # ── Case 3: music record ──────────────────────────────────────────────────
    _print_case("3: music INSERT")
    result = run("Add the piece 'Integration March' by Test Composer, difficulty 2.")
    print(f"  Response: {format_response(result)}")
    if _assert_success(result):
        if _assert_row_exists(
            "SELECT 1 FROM music WHERE title = %s",
            ("Integration March",),
            "music row",
        ):
            passed += 1
        else:
            failed += 1
    else:
        failed += 1

    # ── Case 4: validation failure ────────────────────────────────────────────
    _print_case("4: validation failure (invalid grade)")
    result = run("Add Bad Grade, an 8th grader, to the student list.")
    print(f"  Response: {format_response(result)}")
    if not result["success"]:
        print("  [PASS] correctly rejected invalid input")
        passed += 1
    else:
        print("  [FAIL] should have been rejected")
        failed += 1

    # ── Cleanup ───────────────────────────────────────────────────────────────
    print("\n[Integration] cleaning up test data...")
    _cleanup()

    print(f"\n=== Integration test complete: {passed} passed, {failed} failed ===\n")


# ── Integration test: SELECT ──────────────────────────────────────────────────

def test_integration_select():
    """
    End-to-end SELECT integration test.

    Inserts a known set of students and a music piece, runs SELECT queries
    through the full pipeline, asserts on the returned results, then cleans up.
    """
    print("\n=== Integration test: SELECT ===")
    passed = 0
    failed = 0

    # Seed known data so SELECT assertions are deterministic
    _seed_select_data()

    # ── Case 5: SELECT all students ───────────────────────────────────────────
    _print_case("5: SELECT all students")
    result = run("Show me all students.")
    print(f"  Response: {format_response(result)}")
    if _assert_success(result):
        if _assert_results_min(result, 1, "at least one student"):
            passed += 1
        else:
            failed += 1
    else:
        failed += 1

    # ── Case 6: SELECT with grade filter ─────────────────────────────────────
    _print_case("6: SELECT students in grade 10")
    result = run("Which students are in grade 10?")
    print(f"  Response: {format_response(result)}")
    if _assert_success(result):
        if _assert_result_contains(result, "last_name", "SelectTest", "grade 10 student"):
            passed += 1
        else:
            failed += 1
    else:
        failed += 1

    # ── Case 7: SELECT with no results ────────────────────────────────────────
    _print_case("7: SELECT students named Zzz (no results)")
    result = run("Show me students with the last name Zzz.")
    print(f"  Response: {format_response(result)}")
    if _assert_success(result):
        if _assert_results_count(result, 0, "empty result set"):
            passed += 1
        else:
            failed += 1
    else:
        failed += 1

    # ── Case 8: SELECT music with difficulty filter ───────────────────────────
    _print_case("8: SELECT music at difficulty 3")
    result = run("Show me all pieces with difficulty 3.")
    print(f"  Response: {format_response(result)}")
    if _assert_success(result):
        if _assert_result_contains(result, "title", "Select Test March", "difficulty 3 piece"):
            passed += 1
        else:
            failed += 1
    else:
        failed += 1

    # ── Cleanup ───────────────────────────────────────────────────────────────
    print("\n[Integration] cleaning up SELECT test data...")
    _cleanup_select_data()

    print(f"\n=== Integration test complete: {passed} passed, {failed} failed ===\n")


# ── Helpers ────────────────────────────────────────────────────────────────────

def _print_case(label: str):
    print(f"\n--- Case {label}")


def _assert_success(result: dict) -> bool:
    if result.get("success"):
        print(f"  [PASS] pipeline returned success, rows_affected={result.get('rows_affected')}")
        return True
    print(f"  [FAIL] pipeline error: {result.get('error')}")
    return False


def _assert_row_exists(sql: str, params: tuple, label: str, expected_count: int = 1) -> bool:
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
        conn.close()

        actual = row[0] if row else 0
        if actual >= expected_count:
            print(f"  [PASS] verified {label} in database")
            return True
        print(f"  [FAIL] {label} not found in database")
        return False
    except Exception as e:
        print(f"  [FAIL] DB verification error: {e}")
        return False


def _assert_results_min(result: dict, min_count: int, label: str) -> bool:
    actual = len(result.get("results", []))
    if actual >= min_count:
        print(f"  [PASS] {label}: {actual} row(s) returned")
        return True
    print(f"  [FAIL] {label}: expected >= {min_count} row(s), got {actual}")
    return False


def _assert_results_count(result: dict, expected: int, label: str) -> bool:
    actual = len(result.get("results", []))
    if actual == expected:
        print(f"  [PASS] {label}: {actual} row(s) returned")
        return True
    print(f"  [FAIL] {label}: expected {expected} row(s), got {actual}")
    return False


def _assert_result_contains(result: dict, field: str, value, label: str) -> bool:
    rows = result.get("results", [])
    if any(str(row.get(field, "")).lower() == str(value).lower() for row in rows):
        print(f"  [PASS] {label} found in results")
        return True
    print(f"  [FAIL] {label} not found — no row with {field}={value!r}")
    return False


def _seed_select_data():
    """Insert known rows used by the SELECT integration test cases."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO students (first_name, last_name, grade) VALUES (%s, %s, %s)",
                ("Select", "SelectTest", 10),
            )
            cur.execute(
                "INSERT INTO music (title, composer, difficulty) VALUES (%s, %s, %s)",
                ("Select Test March", "Test Composer", 3),
            )
        conn.commit()
        print("  [OK] SELECT test data seeded")
    except Exception as e:
        conn.rollback()
        print(f"  [WARN] seeding failed: {e}")
    finally:
        conn.close()


def _cleanup_select_data():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM students WHERE last_name = %s", ("SelectTest",))
            cur.execute("DELETE FROM music WHERE title = %s", ("Select Test March",))
        conn.commit()
        print("  [OK] SELECT test data removed")
    except Exception as e:
        conn.rollback()
        print(f"  [WARN] cleanup failed: {e}")
    finally:
        conn.close()


def _cleanup():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM students WHERE last_name IN (%s, %s, %s, %s)",
                ("Test", "Alpha", "Beta", "Gamma"),
            )
            cur.execute("DELETE FROM music WHERE title = %s", ("Integration March",))
        conn.commit()
        print("  [OK] test data removed")
    except Exception as e:
        conn.rollback()
        print(f"  [WARN] cleanup failed: {e}")
    finally:
        conn.close()


# ── Connection smoke test ──────────────────────────────────────────────────────

def test_connections():
    """Verify both the LLM and database connections are reachable."""
    print("\n=== Connection tests ===")
    test_llm()
    test_connection()
    print()


if __name__ == "__main__":
    test_connections()
    test_integration()
    test_integration_select()
