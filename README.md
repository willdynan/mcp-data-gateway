# mcp-data-gateway

An identity-scoped, read-only MCP server. One `allows()` decision, enforced
on both sides, with an audit line for every call and a snapshot test that
pins the tool surface.

Built for handing an AI client to people with different privileges over the
same systems. The grant model stops a caller, not the prompt.

## Quickstart

```
python3 -m unittest discover -s tests   # no dependencies
python3 -m gateway.demo                 # three identities, one denial on the record
pip install mcp && GATEWAY_IDENTITY=analyst@example.com python3 -m gateway.server
```

## Design

Every rule exists because the easy version fails in a specific way, and
each rule carries a test. The walkthrough: [docs/design.md](docs/design.md).
The rules: [docs/rules.md](docs/rules.md). Limits and provenance:
[docs/lineage.md](docs/lineage.md).

## Layout

```
gateway/registry.py       tool registry and the write-surface set
gateway/authz.py          grants store, fail-closed, allows()
gateway/audit.py          one JSON line per event, size-capped
gateway/dispatch.py       the audited call path
gateway/sqlgate.py        read-only SQL gate and row cap
gateway/instructions.py   per-identity server instructions
gateway/systems/          demo backends: sqlite warehouse, directory
tests/tool_names.txt      the pinned tool surface
```

Distilled August 2026 from production practice. The commit log starts at
distillation.
