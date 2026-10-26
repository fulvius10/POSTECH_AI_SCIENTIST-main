from pathlib import Path
import sys
import unittest

import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from quality import join_profile


class JoinContractTests(unittest.TestCase):
    def setUp(self):
        self.con = duckdb.connect()
        self.addCleanup(self.con.close)
        self.con.execute("CREATE TABLE l(id VARCHAR); INSERT INTO l VALUES ('A'),('B'),('C')")
        self.con.execute("CREATE TABLE r(id VARCHAR); INSERT INTO r VALUES ('A'),('B')")

    def profile(self, allowed=()):
        return join_profile(self.con, "test", "SELECT * FROM l", "SELECT * FROM r", ["id"], allowed)

    def test_known_absence_has_explicit_raw_rate_and_threshold(self):
        result = self.profile([("C",)])
        self.assertEqual(result["blocking_violations"], 0)
        self.assertEqual(result["matched_rows"], 2)
        self.assertEqual(result["match_rate"], 2/3)
        self.assertEqual(result["minimum_match_rate"], 2/3)

    def test_different_missing_key_does_not_pass_on_same_count(self):
        self.con.execute("DELETE FROM r WHERE id='B'; INSERT INTO r VALUES ('C')")
        result = self.profile([("C",)])
        self.assertGreater(result["blocking_violations"], 0)
        self.assertEqual(result["unexpected_missing_keys"], [["B"]])

    def test_duplicate_right_side_cannot_multiply_records(self):
        self.con.execute("INSERT INTO r VALUES ('A')")
        result = self.profile([("C",)])
        self.assertGreater(result["blocking_violations"], 0)
        self.assertEqual(result["output_rows_left_join"], 4)

    def test_null_join_keys_are_not_accepted_as_matching(self):
        self.con.execute("INSERT INTO l VALUES (NULL); INSERT INTO r VALUES (NULL)")
        result = self.profile([("C",)])
        self.assertGreater(result["blocking_violations"], 0)
        self.assertEqual(result["matched_rows"], 2)


if __name__ == "__main__":
    unittest.main()
