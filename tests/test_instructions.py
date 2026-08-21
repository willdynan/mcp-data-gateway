import unittest
from pathlib import Path

import gateway.tools  # noqa: F401  (registers the surface)
from gateway.authz import Grants
from gateway.instructions import build

GRANTS = Path(__file__).resolve().parent.parent / "grants.example.json"


class PerIdentityInstructions(unittest.TestCase):
    def setUp(self):
        self.grants = Grants(GRANTS)

    def test_identities_get_different_prose(self):
        analyst = build("analyst@example.com", self.grants)
        people = build("people-ops@example.com", self.grants)
        self.assertNotEqual(analyst, people)

    def test_unheld_systems_are_not_described(self):
        analyst = build("analyst@example.com", self.grants)
        self.assertIn("analytics database", analyst)
        self.assertNotIn("staff directory", analyst)
        people = build("people-ops@example.com", self.grants)
        self.assertIn("staff directory", people)
        self.assertNotIn("analytics database", people)

    def test_tool_list_matches_grants(self):
        analyst = build("analyst@example.com", self.grants)
        self.assertIn("gw_warehouse_query", analyst)
        self.assertNotIn("gw_directory_get_user", analyst)


if __name__ == "__main__":
    unittest.main()
