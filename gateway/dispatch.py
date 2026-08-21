"""The audited execution path — the second side of two-sided enforcement.

`tools/list` filtering and this call-time check consume the same `allows()`
decision; the filter is never the only thing standing between an identity and
a tool. Denials are logged with an error class and zero latency, so an
identity probing forbidden tools is distinguishable from a broken backend.
The call event is emitted BEFORE execution: a tool that crashes the process
still leaves the attempt on the record.
"""

import uuid
from time import perf_counter

from .audit import emit
from .authz import Grants
from .registry import TOOLS


def audited_call(grants: Grants, identity: str, tool_name: str, args: dict, stream=None):
    request_id = uuid.uuid4().hex
    base = {"request_id": request_id, "identity": identity, "tool": tool_name}
    if not grants.allows(identity, tool_name):
        emit({**base, "event": "denied", "args": args,
              "error_class": "GrantDenied", "latency_ms": 0}, stream)
        raise PermissionError(f"{identity} is not granted {tool_name}")
    emit({**base, "event": "call", "args": args}, stream)
    started = perf_counter()
    try:
        result = TOOLS[tool_name].fn(**args)
    except Exception as exc:
        emit({**base, "event": "error", "error_class": type(exc).__name__,
              "latency_ms": round((perf_counter() - started) * 1000, 2)}, stream)
        raise
    emit({**base, "event": "result",
          "latency_ms": round((perf_counter() - started) * 1000, 2)}, stream)
    return result
