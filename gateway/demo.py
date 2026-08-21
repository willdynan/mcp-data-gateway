"""Run a few audited calls as different identities against the demo grants.

    python3 -m gateway.demo
"""

import json
from pathlib import Path

from . import tools  # noqa: F401  (importing registers the tool surface)
from .authz import Grants
from .dispatch import audited_call
from .instructions import build

GRANTS = Path(__file__).resolve().parent.parent / "grants.example.json"


def main():
    grants = Grants(GRANTS)
    for identity in ("analyst@example.com", "people-ops@example.com", "lead@example.com"):
        print(f"\n### {identity}")
        print("visible:", ", ".join(grants.visible_tools(identity)))
        try:
            result = audited_call(grants, identity, "gw_staff_footprint", {"email": "cy@example.com"})
            print("gw_staff_footprint ->", json.dumps(result)[:120], "...")
        except PermissionError as exc:
            print("gw_staff_footprint -> DENIED:", exc)
    print("\n### instructions for analyst@example.com\n")
    print(build("analyst@example.com", grants))


if __name__ == "__main__":
    main()
