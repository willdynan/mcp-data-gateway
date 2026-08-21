import json
import os
import tempfile
import unittest
from pathlib import Path

import gateway.tools  # noqa: F401  (registers the surface)
from gateway.registry import TOOLS, write_surface

SNAPSHOT = Path(__file__).parent / "tool_names.txt"


class ToolSurface(unittest.TestCase):
    def test_surface_matches_snapshot(self):
        pinned = SNAPSHOT.read_text().split()
        self.assertEqual(sorted(TOOLS), pinned,
                         "tool surface changed: update tests/tool_names.txt deliberately")

    def test_write_surface_is_exactly_feedback(self):
        self.assertEqual(write_surface(), {"gw_feedback"})

    def test_every_tool_has_description(self):
        for spec in TOOLS.values():
            self.assertTrue(spec.description, f"{spec.name} has no description")

    def test_combo_tool_declares_both_systems(self):
        self.assertEqual(set(TOOLS["gw_staff_footprint"].systems),
                         {"warehouse", "directory"})


class Feedback(unittest.TestCase):
    def test_feedback_appends_jsonl(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "fb.jsonl")
            os.environ["GATEWAY_FEEDBACK_PATH"] = path
            try:
                TOOLS["gw_feedback"].fn(message="row cap surprised me", identity="a@example.com")
                TOOLS["gw_feedback"].fn(message="second", identity="a@example.com")
            finally:
                del os.environ["GATEWAY_FEEDBACK_PATH"]
            lines = Path(path).read_text().splitlines()
            self.assertEqual(len(lines), 2)
            self.assertEqual(json.loads(lines[0])["message"], "row cap surprised me")


if __name__ == "__main__":
    unittest.main()
