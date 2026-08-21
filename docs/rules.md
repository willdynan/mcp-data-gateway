---
type: Reference
title: Rules
description: The reasoning behind every rule.
---

# The rules, with their citations

Every rule exists because the easy version fails in a specific way. The
test file after each rule is the citation.

## Fail closed (`tests/test_authz.py`)

A missing or corrupt grants store denies everyone except the break-glass
superuser. No parse error ever widens access. A read failure serves the
last good map — an outage must not change anyone's access in either
direction. No map at all denies.

## Two-sided enforcement (`tests/test_authz.py`)

The same `allows()` decision filters `tools/list` and refuses
`tools/call`. The filter is never the only thing standing between an
identity and a tool. A client that ignores the filter meets the refusal.

## Explicit tool grants, never globs (`tests/test_authz.py`)

A grant is a list of tool names. The parser rejects `gw_warehouse_*` at
load time. The failure this prevents is quiet and delayed. Someone ships a
write tool under that prefix next quarter, and every glob-holder inherits
it without anyone deciding that.

## Combo tools declare every system they read (`tests/test_registry.py`)

`gw_staff_footprint` joins the directory record with warehouse rows, so it
declares both systems and the caller must hold both. A tool name says one
system. Its reads can say another, and the reads are what leak.

## A snapshot pins the write surface (`tests/test_registry.py`)

`tests/tool_names.txt` holds the full tool list. Growing, shrinking, or
renaming the surface fails the suite until the change lands in both places
on purpose. A second pin holds the write surface at exactly one tool:
`gw_feedback`, append-only, local.

## Audit survives bad inputs (`tests/test_audit.py`)

One JSON line per event, size-capped at 8 KB:

```json
{"request_id":"f1de...","identity":"lead@example.com","tool":"gw_ping",
 "event":"call","ts":"...","args_json":"{\"email\": \"cy@example.com\"}"}
```

Arguments ride as a JSON string, never a nested object. Argument shapes
vary per tool, and a sink that infers one schema for the stream will
eventually collide and divert rows. The call event lands before execution:
a crash still leaves the attempt on the record. Denials carry
`error_class` and `latency_ms: 0`, so probing looks different from
breakage.

## The SQL gate is for clear errors, not safety (`tests/test_sqlgate.py`)

`gw_warehouse_query` accepts free-form SQL through an allowlist gate. One
statement, SELECT or WITH first, write and DDL verbs banned even inside
strings, 200-row cap with a truncation flag. In production the real fence
is the database identity's own permissions. A caller can talk past a text
scan, never past an IAM role. The gate exists so a blocked caller gets a
fast, specific message instead of a driver error.

## Instructions follow identity (`tests/test_instructions.py`)

The gateway builds the MCP `instructions` field per identity from the same
grants. A caller reads about the systems they hold and nothing else. Prose
that covers tools a caller cannot invoke trains the model to attempt them
and the user to distrust the errors.

## Extending it

Adding a tool is one decorated function plus one snapshot line:

```python
@tool("gw_warehouse_regions", systems=("warehouse",),
      description="Distinct regions with staff counts.")
def gw_warehouse_regions() -> dict:
    return warehouse.query("SELECT region, COUNT(*) AS n FROM staff GROUP BY region")
```

The suite forces the deliberate parts: the snapshot line, then the grants.
A new backend is a module under `gateway/systems/` plus entries in the
`systems` tuples and `SYSTEM_BLURBS`.
