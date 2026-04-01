import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from main import run
from agent.llm_client import call_llm
from agent.formatter import format_response
from database.connection import get_connection


# ── Connection smoke test ─────────────────────────────────────────────────────

def test_connections():
    """Verify both the LLM and database connections are reachable."""
    print("\n=== Connection tests ===")
    reply = call_llm(
        system_prompt="You are a helpful assistant.",
        user_message="Reply with exactly: LLM connection successful.",
    )
    print(reply)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
            print(f"Connected: {version}")
    finally:
        conn.close()
    print()


# ── Integration test: INSERT ──────────────────────────────────────────────────

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


# ── Integration test: UPDATE ──────────────────────────────────────────────────

def test_integration_update():
    """
    End-to-end UPDATE integration test.

    Seeds known rows, runs UPDATE prompts through the full pipeline, verifies
    the DB reflects the changes, tests validation rejection, then cleans up.
    """
    print("\n=== Integration test: UPDATE ===")
    passed = 0
    failed = 0

    _seed_update_data()

    # ── Case 9: UPDATE student grade ─────────────────────────────────────────
    _print_case("9: UPDATE student grade")
    result = run("Change Upd Tester's grade to 11.")
    print(f"  Response: {format_response(result)}")
    if _assert_success(result):
        if _assert_field_value(
            "SELECT grade FROM students WHERE first_name = %s AND last_name = %s",
            ("Upd", "Tester"),
            11,
            "updated grade",
        ):
            passed += 1
        else:
            failed += 1
    else:
        failed += 1

    # ── Case 10: UPDATE music difficulty ─────────────────────────────────────
    _print_case("10: UPDATE music difficulty")
    result = run("Update the difficulty of Upd Test March to 4.")
    print(f"  Response: {format_response(result)}")
    if _assert_success(result):
        if _assert_field_value(
            "SELECT difficulty FROM music WHERE title = %s",
            ("Upd Test March",),
            4,
            "updated difficulty",
        ):
            passed += 1
        else:
            failed += 1
    else:
        failed += 1

    # ── Case 11: validation failure (grade out of range) ─────────────────────
    _print_case("11: validation failure (UPDATE with invalid grade)")
    result = run("Change Upd Tester's grade to 7.")
    print(f"  Response: {format_response(result)}")
    if not result["success"]:
        print("  [PASS] correctly rejected invalid grade update")
        passed += 1
    else:
        print("  [FAIL] should have been rejected")
        failed += 1

    # ── Cleanup ───────────────────────────────────────────────────────────────
    print("\n[Integration] cleaning up UPDATE test data...")
    _cleanup_update_data()

    print(f"\n=== Integration test complete: {passed} passed, {failed} failed ===\n")


# ── Integration test: DELETE ──────────────────────────────────────────────────

def test_integration_delete():
    """
    End-to-end DELETE integration test.

    Seeds known rows (including a student with an active checkout), runs DELETE
    prompts through the full pipeline, verifies rows are removed or correctly
    blocked, then cleans up.
    """
    print("\n=== Integration test: DELETE ===")
    passed = 0
    failed = 0

    _seed_delete_data()

    # ── Case 12: DELETE music piece ───────────────────────────────────────────
    _print_case("12: DELETE music piece")
    result = run("Remove Del Test March from the music library.")
    print(f"  Response: {format_response(result)}")
    if _assert_success(result):
        if _assert_row_gone(
            "SELECT 1 FROM music WHERE title = %s",
            ("Del Test March",),
            "Del Test March",
        ):
            passed += 1
        else:
            failed += 1
    else:
        failed += 1

    # ── Case 13: DELETE student (no active checkouts) ─────────────────────────
    _print_case("13: DELETE student (no active checkouts)")
    result = run("Remove Del Clean from the student list.")
    print(f"  Response: {format_response(result)}")
    if _assert_success(result):
        if _assert_row_gone(
            "SELECT 1 FROM students WHERE first_name = %s AND last_name = %s",
            ("Del", "Clean"),
            "Del Clean",
        ):
            passed += 1
        else:
            failed += 1
    else:
        failed += 1

    # ── Case 14: DELETE student with active checkout (should be blocked) ──────
    _print_case("14: validation failure (DELETE student with active checkout)")
    result = run("Remove Del Blocked from the student list.")
    print(f"  Response: {format_response(result)}")
    if not result["success"]:
        print("  [PASS] correctly blocked delete of student with active checkout")
        passed += 1
    else:
        print("  [FAIL] should have been blocked")
        failed += 1

    # ── Cleanup ───────────────────────────────────────────────────────────────
    print("\n[Integration] cleaning up DELETE test data...")
    _cleanup_delete_data()

    print(f"\n=== Integration test complete: {passed} passed, {failed} failed ===\n")


# ── Helpers ───────────────────────────────────────────────────────────────────

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


def _assert_field_value(sql: str, params: tuple, expected, label: str) -> bool:
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
        conn.close()
        if row and row[0] == expected:
            print(f"  [PASS] verified {label} = {expected!r} in database")
            return True
        actual = row[0] if row else None
        print(f"  [FAIL] {label}: expected {expected!r}, got {actual!r}")
        return False
    except Exception as e:
        print(f"  [FAIL] DB verification error: {e}")
        return False


def _assert_row_gone(sql: str, params: tuple, label: str) -> bool:
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
        conn.close()
        if row is None:
            print(f"  [PASS] verified {label!r} was removed from database")
            return True
        print(f"  [FAIL] {label!r} still exists in database")
        return False
    except Exception as e:
        print(f"  [FAIL] DB verification error: {e}")
        return False


def _seed_update_data():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO students (first_name, last_name, grade) VALUES (%s, %s, %s)",
                ("Upd", "Tester", 10),
            )
            cur.execute(
                "INSERT INTO music (title, composer, difficulty) VALUES (%s, %s, %s)",
                ("Upd Test March", "Test Composer", 2),
            )
        conn.commit()
        print("  [OK] UPDATE test data seeded")
    except Exception as e:
        conn.rollback()
        print(f"  [WARN] seeding failed: {e}")
    finally:
        conn.close()


def _cleanup_update_data():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM students WHERE last_name = %s", ("Tester",))
            cur.execute("DELETE FROM music WHERE title = %s", ("Upd Test March",))
        conn.commit()
        print("  [OK] UPDATE test data removed")
    except Exception as e:
        conn.rollback()
        print(f"  [WARN] cleanup failed: {e}")
    finally:
        conn.close()


def _seed_delete_data():
    """Seed data for DELETE tests.

    Inserts:
    - "Del Clean"   (grade 9)  — no checkouts, safe to delete
    - "Del Blocked" (grade 10) — has active checkout, delete must be blocked
    - "Del Test March" music piece
    - "DELTEST-001" trumpet in instrument_inventory (for the checkout FK)
    - checkout_history row linking Del Blocked to DELTEST-001 (return_date NULL)
    """
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO students (first_name, last_name, grade) VALUES (%s, %s, %s)",
                ("Del", "Clean", 9),
            )
            cur.execute(
                "INSERT INTO students (first_name, last_name, grade) VALUES (%s, %s, %s) RETURNING student_id",
                ("Del", "Blocked", 10),
            )
            blocked_id = cur.fetchone()[0]
            cur.execute(
                "INSERT INTO music (title, composer, difficulty) VALUES (%s, %s, %s)",
                ("Del Test March", "Test Composer", 1),
            )
            cur.execute(
                "INSERT INTO instrument_inventory (serial_number, instrument_name, condition) "
                "VALUES (%s, %s, %s)",
                ("DELTEST-001", "trumpet", "good"),
            )
            cur.execute(
                "INSERT INTO checkout_history (student_id, serial_number, checkout_date) "
                "VALUES (%s, %s, CURRENT_DATE)",
                (blocked_id, "DELTEST-001"),
            )
        conn.commit()
        print("  [OK] DELETE test data seeded")
    except Exception as e:
        conn.rollback()
        print(f"  [WARN] seeding failed: {e}")
    finally:
        conn.close()


def _cleanup_delete_data():
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Remove checkout and instrument first (FK constraints)
            cur.execute(
                "DELETE FROM checkout_history WHERE serial_number = %s",
                ("DELTEST-001",),
            )
            cur.execute(
                "DELETE FROM instrument_inventory WHERE serial_number = %s",
                ("DELTEST-001",),
            )
            # Del Clean may already be gone (deleted by case 13)
            cur.execute(
                "DELETE FROM students WHERE last_name IN (%s, %s)",
                ("Clean", "Blocked"),
            )
            # Del Test March may already be gone (deleted by case 12)
            cur.execute("DELETE FROM music WHERE title = %s", ("Del Test March",))
        conn.commit()
        print("  [OK] DELETE test data removed")
    except Exception as e:
        conn.rollback()
        print(f"  [WARN] cleanup failed: {e}")
    finally:
        conn.close()


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


if __name__ == "__main__":
    test_connections()
    test_integration()
    test_integration_select()
    test_integration_update()
    test_integration_delete()
