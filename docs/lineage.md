---
type: Reference
title: Lineage
description: Honest limits and provenance.
---

# Honest limits

- Identity comes from `GATEWAY_IDENTITY` in the demo server. Production
  used per-request SSO. Wiring that is deployment-specific and out of
  scope. The point of this repo is everything downstream of knowing the
  caller.
- The demo backend is SQLite. "The real fence is database permissions" is
  prose here, not a demo. The gate and the caps are real.
- Grants re-read on each decision, cheap at this scale. Production cached
  with a short TTL. The fail-closed semantics are identical and the tests
  pin them.
- Single process, no rate limiting, no TLS. This is the authz and audit
  core, not a deployment.

# Lineage

This is a distillation, not a port. The pattern matured across several
production gateway servers built for different audiences during 2026. Each
one scoped an estate of internal systems to the people entitled to read
it. Every rule here earned its place by failing the easy way first,
somewhere real. The systems, counts, and incident details stay out of this
repo on purpose. The architecture is the artifact, and the demo backends
are synthetic.

Distilled: August 2026. This repository began at distillation. The dates
above describe the pattern's history, not this commit log.
