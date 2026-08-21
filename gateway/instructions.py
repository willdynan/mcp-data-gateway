"""Per-identity server instructions.

The MCP `instructions` field is generated from the caller's grants: a caller
reads about the systems they hold and nothing else. Instructions that describe
tools a caller cannot invoke train the model to attempt them and the user to
distrust the errors.
"""

from .authz import Grants
from .registry import TOOLS

SYSTEM_BLURBS = {
    "warehouse": (
        "warehouse: an analytics database of staff and support tickets. "
        "gw_warehouse_query accepts one read-only SELECT/WITH statement; "
        "results cap at 200 rows and report truncation."
    ),
    "directory": (
        "directory: the staff directory (name, department, title, active flag). "
        "Look people up by email."
    ),
}


def build(identity: str, grants: Grants) -> str:
    tools = grants.visible_tools(identity)
    systems = grants.systems_for(identity)
    lines = [
        f"You are connected to a read-only data gateway as {identity}.",
        "Every call is audited. Denied calls mean the identity lacks a grant —"
        " report that plainly rather than retrying.",
        "",
    ]
    for name in sorted(systems):
        if name in SYSTEM_BLURBS:
            lines.append(SYSTEM_BLURBS[name])
    lines.append("")
    lines.append("Granted tools: " + (", ".join(tools) if tools else "none") + ".")
    if "gw_feedback" in tools:
        lines.append(
            "gw_feedback is the one write tool: file an issue when a tool result "
            "is wrong, confusing, or missing data you expected."
        )
    return "\n".join(lines)
