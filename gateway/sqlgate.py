"""Read-only SQL gate.

This gate exists for fast, specific error messages — not for safety. The real
fence in production is the database identity's permissions; a text scan can be
talked past, an IAM role cannot. Deliberately conservative: banned verbs are
rejected even inside string literals, because a false refusal costs a reword
and a false pass costs an incident.
"""

import re


class SqlGateError(ValueError):
    pass


ROW_CAP = 200

_BANNED = re.compile(
    r"\b(insert|update|delete|drop|alter|create|attach|detach|pragma|vacuum"
    r"|replace|reindex|grant|revoke|truncate|merge)\b",
    re.IGNORECASE,
)
_LINE_COMMENT = re.compile(r"--[^\n]*")
_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)


def check(sql: str) -> str:
    body = _BLOCK_COMMENT.sub(" ", _LINE_COMMENT.sub(" ", sql)).strip()
    if not body:
        raise SqlGateError("empty statement")
    if body.rstrip().rstrip(";").count(";") > 0:
        raise SqlGateError("one statement per call")
    first = body.split(None, 1)[0].lower()
    if first not in ("select", "with"):
        raise SqlGateError("statement must begin with SELECT or WITH")
    hit = _BANNED.search(body)
    if hit:
        raise SqlGateError(
            f"{hit.group(0)!r} is not allowed here (banned even inside strings; reword the query)"
        )
    return body


def run(conn, sql: str) -> dict:
    body = check(sql)
    cursor = conn.execute(body)
    rows = cursor.fetchmany(ROW_CAP + 1)
    truncated = len(rows) > ROW_CAP
    rows = rows[:ROW_CAP]
    return {
        "rows": [dict(r) for r in rows],
        "truncated": truncated,
        "row_cap": ROW_CAP,
    }
