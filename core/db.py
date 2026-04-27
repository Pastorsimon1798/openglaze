"""Database connection utilities."""

import sqlite3
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# PRAGMAs applied once per connection to improve reliability
_CONNECTION_PRAGMAS = """
    PRAGMA journal_mode=WAL;
    PRAGMA busy_timeout=5000;
    PRAGMA foreign_keys=ON;
    PRAGMA synchronous=NORMAL;
"""


def connect_db(db_path: str) -> sqlite3.Connection:
    """Open a SQLite connection with recommended PRAGMAs.

    Enables WAL mode for better write concurrency, sets a busy timeout
    to avoid immediate "database is locked" errors, and enforces foreign
    keys.  Handles :memory: databases via shared-cache URI for testing.
    """
    if db_path == ":memory:":
        conn = sqlite3.connect("file::memory:?cache=shared", uri=True)
    else:
        conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(_CONNECTION_PRAGMAS)
    return conn


@contextmanager
def get_connection(db_path: str):
    """Context manager that yields a connection and ensures cleanup."""
    conn = connect_db(db_path)
    try:
        yield conn
    finally:
        conn.close()
