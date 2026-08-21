---
type: Reference
title: Design notes
description: How the pieces fit together.
---

# Design notes

## What this is

An MCP server is a tool surface an AI client can call. The moment two
people with different privileges share one server, it needs an answer to a
hard question. Who is calling, and what may they touch? This repo is that
answer, reduced to its load-bearing parts.

The shape: a registry of tools, a grants store keyed by identity, one
authorization function, an audited dispatch path, and a generated
instructions field. Everything else — the SQLite warehouse, the static
directory — is a synthetic stand-in so the whole thing runs with no
credentials and no network.

## How it works

```
             tools/list                       tools/call
                 |                                |
                 v                                v
          visible_tools(id)               audited_call(id, tool, args)
                 |                                |
                 +----------> allows(id, tool) <--+
                                   |
                    grants.json (fail-closed load)
                    + SUPERUSERS (hardcoded)
                    + TOOL_SYSTEMS (from the registry)
```

One decision, two consumers. `visible_tools()` filters what the client
sees. `audited_call()` refuses what the client tries anyway. Both call
`allows()`, so no state exists where the filter and the enforcement
disagree.

`allows()` answers yes only when three things hold at once:

1. The tool exists in the registry.
2. The identity's grant lists that tool by name.
3. The identity holds every system the tool declares it reads.

A superuser bypasses 2 and 3 but not 1. The superuser set lives in code,
not in the store, so no store outage can lock out the person who fixes
stores. The grants file maps identity to explicit lists:

```json
{"analyst@example.com": {"systems": ["warehouse"],
 "tools": ["gw_ping", "gw_warehouse_query", "gw_feedback"]}}
```

## Worked example

`python3 -m gateway.demo` runs three identities against the example
grants. Real output, trimmed:

```
### analyst@example.com
visible: gw_feedback, gw_ping, gw_warehouse_query, gw_warehouse_schema, ...
{"request_id":"1054...","tool":"gw_staff_footprint","event":"denied",
 "error_class":"GrantDenied","latency_ms":0,...}
gw_staff_footprint -> DENIED: analyst@example.com is not granted gw_staff_footprint

### lead@example.com
visible: ..., gw_staff_footprint, gw_warehouse_query, ...
{"request_id":"f1de...","tool":"gw_staff_footprint","event":"call",...}
{"request_id":"f1de...","tool":"gw_staff_footprint","event":"result","latency_ms":0.72,...}
```

The analyst holds the warehouse. The people-ops identity holds the
directory. Only the lead holds both, and `gw_staff_footprint` reads both,
so only the lead's call goes through. The denial is on the record with the
arguments the caller tried.

Every rule and its citation: [rules.md](rules.md). Limits and provenance:
[lineage.md](lineage.md).
