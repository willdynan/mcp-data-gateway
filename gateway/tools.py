"""The tool surface. Importing this module registers every tool.

The surface is pinned by tests/tool_names.txt: adding, removing, or renaming a
tool fails the snapshot test until the change is made deliberately in both
places. gw_feedback is the only tool that writes, and a second test pins that.
"""

import json
import os
from datetime import datetime, timezone

from . import __version__
from .registry import tool
from .systems import directory, warehouse


@tool("gw_ping", systems=(), description="Liveness and version check.")
def gw_ping() -> dict:
    return {"ok": True, "version": __version__}


@tool("gw_warehouse_tables", systems=("warehouse",), description="List warehouse tables.")
def gw_warehouse_tables() -> dict:
    return {"tables": warehouse.tables()}


@tool("gw_warehouse_schema", systems=("warehouse",), description="Column names and types for one table.")
def gw_warehouse_schema(table: str) -> dict:
    return {"table": table, "columns": warehouse.schema(table)}


@tool("gw_warehouse_query", systems=("warehouse",),
      description="Run one read-only SELECT/WITH statement. Results cap at 200 rows.")
def gw_warehouse_query(sql: str) -> dict:
    return warehouse.query(sql)


@tool("gw_directory_list_users", systems=("directory",),
      description="List staff, optionally filtered by department.")
def gw_directory_list_users(dept: str | None = None) -> dict:
    return {"users": directory.list_users(dept)}


@tool("gw_directory_get_user", systems=("directory",),
      description="Look up one person by email.")
def gw_directory_get_user(email: str) -> dict:
    user = directory.get_user(email)
    return {"found": user is not None, "user": user}


@tool("gw_staff_footprint", systems=("warehouse", "directory"),
      description="One person's directory record joined with their ticket history. Reads BOTH systems.")
def gw_staff_footprint(email: str) -> dict:
    user = directory.get_user(email)
    if user is None:
        return {"found": False}
    tickets = warehouse.tickets_for(email)
    return {"found": True, "user": user, "ticket_count": len(tickets), "tickets": tickets}


@tool("gw_feedback", systems=(), writes=True,
      description="File an issue about a tool result: wrong, confusing, or missing data. Append-only.")
def gw_feedback(message: str, identity: str = "") -> dict:
    path = os.environ.get("GATEWAY_FEEDBACK_PATH", "feedback.jsonl")
    record = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "identity": identity,
        "message": message,
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return {"filed": True}
