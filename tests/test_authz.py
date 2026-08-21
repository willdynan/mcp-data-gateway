import io
import json
import tempfile
import unittest
from pathlib import Path

import gateway.tools  # noqa: F401  (registers the surface)
from gateway.authz import Grants
from gateway.dispatch import audited_call

ANALYST = "analyst@example.com"
SUPER = "break-glass@example.com"

GOOD = {
    ANALYST: {
        "systems": ["warehouse"],
        "tools": ["gw_ping", "gw_warehouse_tables", "gw_staff_footprint"],
    }
}


class TempGrants(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = Path(self.dir.name) / "grants.json"

    def tearDown(self):
        self.dir.cleanup()

    def write(self, content):
        self.path.write_text(content if isinstance(content, str) else json.dumps(content))


class FailClosed(TempGrants):
    def test_missing_store_denies_everyone_but_superuser(self):
        grants = Grants(self.path)
        self.assertFalse(grants.allows(ANALYST, "gw_ping"))
        self.assertTrue(grants.allows(SUPER, "gw_ping"))

    def test_empty_map_denies(self):
        self.write({})
        self.assertFalse(Grants(self.path).allows(ANALYST, "gw_ping"))

    def test_corrupt_store_with_no_prior_good_denies(self):
        self.write("{not json")
        self.assertFalse(Grants(self.path).allows(ANALYST, "gw_ping"))

    def test_corrupt_store_serves_last_good(self):
        self.write(GOOD)
        grants = Grants(self.path)
        self.assertTrue(grants.allows(ANALYST, "gw_ping"))
        self.write("{not json")
        self.assertTrue(grants.allows(ANALYST, "gw_ping"),
                        "a store outage must not change access")

    def test_glob_rejects_the_store(self):
        self.write({ANALYST: {"systems": ["warehouse"], "tools": ["gw_warehouse_*"]}})
        self.assertFalse(Grants(self.path).allows(ANALYST, "gw_warehouse_tables"))

    def test_glob_edit_after_good_load_serves_last_good(self):
        self.write(GOOD)
        grants = Grants(self.path)
        self.assertTrue(grants.allows(ANALYST, "gw_ping"))
        self.write({ANALYST: {"systems": ["warehouse"], "tools": ["gw_*"]}})
        self.assertTrue(grants.allows(ANALYST, "gw_ping"))
        self.assertFalse(grants.allows(ANALYST, "gw_directory_get_user"))


class ComboSystems(TempGrants):
    def test_granted_tool_without_all_systems_denies(self):
        # The combo tool reads both systems. This grant holds one.
        self.write(GOOD)
        self.assertFalse(Grants(self.path).allows(ANALYST, "gw_staff_footprint"))

    def test_granted_tool_with_all_systems_allows(self):
        entry = dict(GOOD[ANALYST], systems=["warehouse", "directory"])
        self.write({ANALYST: entry})
        self.assertTrue(Grants(self.path).allows(ANALYST, "gw_staff_footprint"))


class TwoSided(TempGrants):
    def test_visible_tools_and_call_share_the_decision(self):
        self.write(GOOD)
        grants = Grants(self.path)
        visible = grants.visible_tools(ANALYST)
        self.assertIn("gw_ping", visible)
        self.assertNotIn("gw_staff_footprint", visible)
        self.assertNotIn("gw_directory_get_user", visible)

    def test_call_path_refuses_independently(self):
        self.write(GOOD)
        grants = Grants(self.path)
        stream = io.StringIO()
        with self.assertRaises(PermissionError):
            audited_call(grants, ANALYST, "gw_directory_get_user",
                         {"email": "ada@example.com"}, stream)
        event = json.loads(stream.getvalue())
        self.assertEqual(event["event"], "denied")
        self.assertEqual(event["error_class"], "GrantDenied")
        self.assertEqual(event["latency_ms"], 0)


if __name__ == "__main__":
    unittest.main()
