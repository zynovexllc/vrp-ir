"""Tests for `vrp-ir checks` and `vrp-ir explain <CHECK_ID>`."""
import io
import json
import unittest
from contextlib import redirect_stdout, redirect_stderr

from vrp_ir import explain_check, list_checks
from vrp_ir.acceptance import CHECKS_META
from vrp_ir.cli import main


class TestListAndExplain(unittest.TestCase):

    def test_list_checks_covers_catalogue(self):
        ids = {c["check_id"] for c in list_checks()}
        self.assertEqual(ids, set(CHECKS_META))

    def test_explain_known_check(self):
        info = explain_check("FW-MGMT-TELNET")
        self.assertEqual(info["check_id"], "FW-MGMT-TELNET")
        self.assertTrue(info["intent"])
        self.assertTrue(any(r["framework"] == "等保" for r in info["references"]))

    def test_explain_unknown_check(self):
        self.assertIsNone(explain_check("NOPE"))


class TestCli(unittest.TestCase):

    def test_cli_checks_text_mode_unchanged(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["checks"])
        out = buf.getvalue()
        expected = "".join(
            f"{c['check_id']}  —  {c['intent']}\n"
            for c in list_checks()
        )
        self.assertEqual(code, 0)
        self.assertEqual(out, expected)

    def test_cli_checks_json_mode(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["checks", "--format", "json"])
        out = buf.getvalue()
        payload = json.loads(out)
        self.assertEqual(code, 0)
        self.assertIsInstance(payload, list)
        self.assertEqual(
            {c["check_id"] for c in payload},
            {c["check_id"] for c in list_checks()},
        )
        self.assertTrue(all("intent" in c for c in payload))

    def test_cli_explain_known(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["explain", "FW-MGMT-TELNET"])
        out = buf.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("FW-MGMT-TELNET", out)
        self.assertIn("Advisory references", out)
        self.assertIn("等保", out)

    def test_cli_explain_unknown_returns_2(self):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(["explain", "NOPE"])
        self.assertEqual(code, 2)
        self.assertIn("unknown check id", err.getvalue())


if __name__ == "__main__":
    unittest.main()
