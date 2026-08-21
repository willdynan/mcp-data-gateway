import unittest

from gateway.sqlgate import ROW_CAP, SqlGateError, check, run
from gateway.systems import warehouse


class Gate(unittest.TestCase):
    def test_select_and_with_pass(self):
        check("SELECT 1 AS x")
        check("WITH t AS (SELECT 1 AS x) SELECT * FROM t")
        check("SELECT 1;")  # single trailing semicolon is fine

    def test_write_and_ddl_verbs_rejected(self):
        for sql in (
            "DELETE FROM tickets",
            "INSERT INTO tickets VALUES (1)",
            "UPDATE staff SET name = 'x'",
            "DROP TABLE staff",
            "PRAGMA table_info(staff)",
            "CREATE TABLE t (x)",
            "ATTACH DATABASE 'x' AS y",
        ):
            with self.assertRaises(SqlGateError, msg=sql):
                check(sql)

    def test_statement_chaining_rejected(self):
        with self.assertRaises(SqlGateError):
            check("SELECT 1; DROP TABLE staff")

    def test_comments_are_stripped_before_judging(self):
        check("SELECT 1 AS x -- drop table staff")
        check("SELECT 1 AS x /* delete everything */")

    def test_banned_word_in_string_still_rejected(self):
        # Deliberately conservative: a false refusal costs a reword.
        with self.assertRaises(SqlGateError):
            check("SELECT 'drop' AS x")

    def test_must_begin_select_or_with(self):
        with self.assertRaises(SqlGateError):
            check("EXPLAIN SELECT 1")


class RowCap(unittest.TestCase):
    def test_cap_and_truncation_flag(self):
        result = run(warehouse.get_db(), "SELECT * FROM tickets")
        self.assertEqual(len(result["rows"]), ROW_CAP)
        self.assertTrue(result["truncated"])

    def test_under_cap_not_flagged(self):
        result = run(warehouse.get_db(), "SELECT * FROM staff")
        self.assertEqual(len(result["rows"]), 6)
        self.assertFalse(result["truncated"])


if __name__ == "__main__":
    unittest.main()
