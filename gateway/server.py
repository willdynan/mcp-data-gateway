"""MCP binding. Requires `pip install mcp`; everything upstream of it does not.

    GATEWAY_IDENTITY=analyst@example.com python3 -m gateway.server

The demo takes identity from the environment because per-request SSO is
deployment-specific; the design point demonstrated here is that BOTH the
registered tool list and the call path consult `allows()` — registration is a
convenience filter, the call-time check is the enforcement.
"""

import functools
import os
from pathlib import Path

from . import tools  # noqa: F401  (importing registers the tool surface)
from .authz import Grants
from .dispatch import audited_call
from .instructions import build
from .registry import TOOLS


def create_server(identity: str, grants_path):
    from mcp.server.fastmcp import FastMCP

    grants = Grants(grants_path)
    server = FastMCP("mcp-data-gateway", instructions=build(identity, grants))
    for name in grants.visible_tools(identity):
        spec = TOOLS[name]

        def make(tool_name):
            src = TOOLS[tool_name].fn

            @functools.wraps(src)
            def bound(**kwargs):
                return audited_call(grants, identity, tool_name, kwargs)

            return bound

        server.tool(name=name, description=spec.description)(make(name))
    return server


def main():
    identity = os.environ.get("GATEWAY_IDENTITY")
    if not identity:
        raise SystemExit("set GATEWAY_IDENTITY (see grants.example.json for demo identities)")
    grants_path = os.environ.get("GATEWAY_GRANTS",
                                 Path(__file__).resolve().parent.parent / "grants.example.json")
    create_server(identity, grants_path).run()


if __name__ == "__main__":
    main()
