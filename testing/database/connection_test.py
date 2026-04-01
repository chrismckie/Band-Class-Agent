import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from database.connection import get_connection


def test_connection():
    """Smoke test — prints the Postgres server version and closes."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
            print(f"Connected: {version}")
    finally:
        conn.close()


if __name__ == "__main__":
    test_connection()
