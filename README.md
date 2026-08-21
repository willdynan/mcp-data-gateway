# mcp-data-gateway

Hand an AI client to one person and MCP is easy. Hand it to a team —
analysts, people-ops, leads, each entitled to different systems — and the
server needs an answer it can defend: who is calling, and what may they
touch? This repo is that answer, cut down to its load-bearing parts.

One `allows()` decision drives everything. It filters what each identity
sees *and* refuses what they try anyway, so the tool list is never the
only thing standing between a caller and a system. Grants fail closed: a
missing or corrupt store denies everyone except a break-glass superuser
who lives in code, precisely so no store outage can lock out the person
who fixes stores. Every call — and every denial — lands as a size-capped
audit line.

Opinions baked in:

- Grants name tools one by one. Globs get rejected at load time, because
  the write tool someone ships next quarter must not inherit its way into
  a read-only identity.
- A tool that joins two systems declares both, and the caller needs both.
  The reads are what leak, not the names.
- A snapshot test pins the tool surface, and a second one holds the write
  surface at exactly one tool.
- The SQL gate gives fast, specific refusals — but the real fence is the
  database identity's permissions. You can talk past a text scan. You
  cannot talk past IAM.

## Quickstart

```
python3 -m unittest discover -s tests   # no dependencies
python3 -m gateway.demo                 # three identities, one denial on the record
pip install mcp && GATEWAY_IDENTITY=analyst@example.com python3 -m gateway.server
```

## Going deeper

[docs/design.md](docs/design.md) walks the pieces with captured output.
[docs/rules.md](docs/rules.md) gives every rule its reason and its test.
[docs/lineage.md](docs/lineage.md) holds the honest limits and provenance.

Distilled August 2026 from production gateways that earned each rule the
hard way. The commit log starts at the distillation.
