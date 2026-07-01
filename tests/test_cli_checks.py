"""Tests for `vrp-ir checks` and `vrp-ir explain <CHECK_ID>`."""
import io
import unittest
from contextlib import redirect_stdout, redirect_stderr

from vrp_ir import explain_check, list_checks, __version__
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

    def test_cli_checks_lists_ids(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["checks"])
        out = buf.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("FW-DEFAULT-DENY", out)
        self.assertIn("FW-SNMP-WEAK-COMMUNITY", out)

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

    def test_cli_version_long(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            with self.assertRaises(SystemExit) as cm:
                main(["--version"])
        self.assertEqual(cm.exception.code, 0)
        self.assertIn(f"vrp-ir {__version__}", buf.getvalue())

    def test_cli_version_short(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            with self.assertRaises(SystemExit) as cm:
                main(["-V"])
        self.assertEqual(cm.exception.code, 0)
        self.assertIn(f"vrp-ir {__version__}", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
