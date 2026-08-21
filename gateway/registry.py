"""Tool registry.

Every tool declares every system it reads. A combo tool that joins two systems
lists both, because the reads are what leak — a name prefix says one system,
the implementation can touch another.
"""

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class ToolSpec:
    name: str
    fn: Callable
    systems: tuple
    description: str
    writes: bool = False


TOOLS: dict[str, ToolSpec] = {}


def tool(name: str, systems=(), description: str = "", writes: bool = False):
    def register(fn):
        if name in TOOLS:
            raise ValueError(f"duplicate tool {name}")
        TOOLS[name] = ToolSpec(name, fn, tuple(systems), description, writes)
        return fn
    return register


def write_surface() -> set[str]:
    return {spec.name for spec in TOOLS.values() if spec.writes}
