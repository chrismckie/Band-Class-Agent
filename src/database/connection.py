import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    """Return a new psycopg2 connection using DATABASE_URL from .env."""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL is not set in .env")
    return psycopg2.connect(database_url)


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
