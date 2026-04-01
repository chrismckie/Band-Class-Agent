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
