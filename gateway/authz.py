"""Grants store and the one authorization decision.

Semantics, in order of precedence:
- Superusers are hardcoded here, not in the store, so no store outage, empty
  file, or UI mistake can lock the administrator out of the thing that fixes it.
- No map at all (file absent, or never successfully parsed) denies everyone else.
- A store read/parse failure serves the last good map — an outage must not
  change anyone's access in either direction.
- A grant names tools explicitly. Globs are rejected at parse time: a write tool
  added later under a granted prefix must not silently ride into a read-only
  identity.
- A tool call needs the tool AND every system the tool reads.
"""

import json
from pathlib import Path

from .registry import TOOLS

SUPERUSERS = frozenset({"break-glass@example.com"})


def all_systems() -> frozenset:
    # Computed on demand: tools register after this module imports.
    return frozenset(s for spec in TOOLS.values() for s in spec.systems)


class GrantError(ValueError):
    pass


def _parse(raw) -> dict:
    if not isinstance(raw, dict):
        raise GrantError("grants root must be an object")
    parsed = {}
    for identity, entry in raw.items():
        tools = entry.get("tools", [])
        systems = entry.get("systems", [])
        for t in tools:
            if "*" in t or "?" in t:
                raise GrantError(f"glob {t!r} in grants for {identity}: grants name tools explicitly")
        parsed[identity] = {"tools": frozenset(tools), "systems": frozenset(systems)}
    return parsed


class Grants:
    def __init__(self, path):
        self.path = Path(path)
        self._last_good = None

    def current(self):
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None
        except (OSError, json.JSONDecodeError):
            return self._last_good
        try:
            parsed = _parse(raw)
        except GrantError:
            return self._last_good
        self._last_good = parsed
        return parsed

    def allows(self, identity: str, tool_name: str) -> bool:
        spec = TOOLS.get(tool_name)
        if spec is None:
            return False
        if identity in SUPERUSERS:
            return True
        current = self.current()
        if not current:
            return False
        entry = current.get(identity)
        if not entry:
            return False
        return tool_name in entry["tools"] and set(spec.systems) <= entry["systems"]

    def visible_tools(self, identity: str) -> list[str]:
        return sorted(name for name in TOOLS if self.allows(identity, name))

    def systems_for(self, identity: str) -> frozenset:
        if identity in SUPERUSERS:
            return all_systems()
        current = self.current()
        if not current or identity not in current:
            return frozenset()
        return current[identity]["systems"]
