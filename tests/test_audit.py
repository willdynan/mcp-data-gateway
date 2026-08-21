import io
import json
import tempfile
import unittest
from pathlib import Path

import gateway.tools  # noqa: F401  (registers the surface)
from gateway.audit import MAX_LINE_BYTES, emit
from gateway.authz import Grants
from gateway.dispatch import audited_call

ANALYST = "analyst@example.com"


def grants_allowing(tmpdir, tools, systems):
    path = Path(tmpdir) / "grants.json"
    path.write_text(json.dumps({ANALYST: {"systems": systems, "tools": tools}}))
    return Grants(path)


class Emitter(unittest.TestCase):
    def test_args_become_a_json_string(self):
        stream = io.StringIO()
        emit({"event": "call", "args": {"sql": "SELECT 1", "n": 2}}, stream)
        record = json.loads(stream.getvalue())
        self.assertNotIn("args", record)
        self.assertIsInstance(record["args_json"], str)
        self.assertEqual(json.loads(record["args_json"]), {"sql": "SELECT 1", "n": 2})

    def test_oversize_line_is_capped_and_flagged(self):
        stream = io.StringIO()
        emit({"event": "call", "args": {"blob": "x" * (MAX_LINE_BYTES * 2)}}, stream)
        line = stream.getvalue().strip()
        self.assertLessEqual(len(line.encode()), MAX_LINE_BYTES)
        self.assertTrue(json.loads(line)["truncated"])


class AuditedCall(unittest.TestCase):
    def test_success_emits_call_then_result_sharing_request_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            grants = grants_allowing(tmp, ["gw_ping"], [])
            stream = io.StringIO()
            result = audited_call(grants, ANALYST, "gw_ping", {}, stream)
        self.assertTrue(result["ok"])
        events = [json.loads(l) for l in stream.getvalue().splitlines()]
        self.assertEqual([e["event"] for e in events], ["call", "result"])
        self.assertEqual(events[0]["request_id"], events[1]["request_id"])

    def test_tool_exception_leaves_call_and_error_on_the_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            grants = grants_allowing(tmp, ["gw_warehouse_schema"], ["warehouse"])
            stream = io.StringIO()
            with self.assertRaises(KeyError):
                audited_call(grants, ANALYST, "gw_warehouse_schema",
                             {"table": "no_such_table"}, stream)
        events = [json.loads(l) for l in stream.getvalue().splitlines()]
        self.assertEqual([e["event"] for e in events], ["call", "error"])
        self.assertEqual(events[1]["error_class"], "KeyError")


if __name__ == "__main__":
    unittest.main()
