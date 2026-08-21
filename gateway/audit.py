"""Structured audit: one JSON line per event, size-capped.

The emitter writes call arguments as a JSON string (`args_json`), never as a
nested object. Argument shapes vary per tool, and a sink that infers one schema
for the whole stream will eventually collide and silently divert rows.
"""

import json
import sys
from datetime import datetime, timezone

MAX_LINE_BYTES = 8192
_TRUNCATED_ARGS = 1024


def emit(event: dict, stream=None) -> None:
    record = dict(event)
    record.setdefault("ts", datetime.now(timezone.utc).isoformat())
    if "args" in record:
        record["args_json"] = json.dumps(record.pop("args"), default=str)
    line = json.dumps(record, default=str, separators=(",", ":"))
    if len(line.encode("utf-8")) > MAX_LINE_BYTES:
        record["args_json"] = record.get("args_json", "")[:_TRUNCATED_ARGS] + "...[truncated]"
        record["truncated"] = True
        line = json.dumps(record, default=str, separators=(",", ":"))
    print(line, file=stream or sys.stdout, flush=True)
