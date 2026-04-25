"""Database connection utilities."""

import sqlite3


def connect_db(db_path: str) -> sqlite3.Connection:
    """Open a SQLite connection, handling :memory: correctly.

    SQLite :memory: databases are per-connection. To allow multiple
    connections to share the same in-memory database (e.g. during
    testing), we use the shared-cache URI form.
    """
    if db_path == ":memory:":
        return sqlite3.connect("file::memory:?cache=shared", uri=True)
    return sqlite3.connect(db_path)
