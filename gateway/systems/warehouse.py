"""Demo analytics backend: an in-memory SQLite database with synthetic data.

Stands in for the production warehouse. Free-form queries go through the SQL
gate; the schema helpers query metadata directly and validate table names
against the live table list rather than splicing caller input into SQL.
"""

import sqlite3

from .. import sqlgate

_conn = None

_STAFF = [
    ("ada@example.com", "Ada Chen", "Engineering", "us-east"),
    ("bo@example.com", "Bo Okafor", "Engineering", "eu-west"),
    ("cy@example.com", "Cy Marsh", "Support", "us-east"),
    ("dee@example.com", "Dee Novak", "Support", "eu-west"),
    ("eli@example.com", "Eli Fontaine", "Finance", "us-east"),
    ("fay@example.com", "Fay Iwata", "Operations", "ap-south"),
]


def _seed(conn):
    conn.executescript(
        """
        CREATE TABLE staff (
            email TEXT PRIMARY KEY, name TEXT, dept TEXT, region TEXT
        );
        CREATE TABLE tickets (
            id INTEGER PRIMARY KEY, opened_by TEXT, status TEXT,
            opened_day INTEGER, hours REAL
        );
        """
    )
    conn.executemany("INSERT INTO staff VALUES (?, ?, ?, ?)", _STAFF)
    statuses = ("open", "closed", "closed", "closed", "waiting")
    rows = []
    for i in range(1, 301):
        email = _STAFF[i % len(_STAFF)][0]
        rows.append((i, email, statuses[i % len(statuses)], i % 90, round((i % 7) * 0.5, 1)))
    conn.executemany("INSERT INTO tickets VALUES (?, ?, ?, ?, ?)", rows)
    conn.commit()


def get_db():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(":memory:", check_same_thread=False)
        _conn.row_factory = sqlite3.Row
        _seed(_conn)
    return _conn


def tables() -> list[str]:
    cur = get_db().execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    return [r["name"] for r in cur.fetchall()]


def schema(table: str) -> list[dict]:
    if table not in tables():
        raise KeyError(f"unknown table {table!r}")
    cur = get_db().execute(f"PRAGMA table_info({table})")
    return [{"name": r["name"], "type": r["type"]} for r in cur.fetchall()]


def query(sql: str) -> dict:
    return sqlgate.run(get_db(), sql)


def tickets_for(email: str) -> list[dict]:
    cur = get_db().execute(
        "SELECT id, status, opened_day, hours FROM tickets WHERE opened_by = ? ORDER BY id",
        (email,),
    )
    return [dict(r) for r in cur.fetchall()]
