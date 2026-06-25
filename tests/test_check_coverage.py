"""Tests for check-coverage transparency (CHECKED / NA / UNCHECKED)."""
import os
import unittest

from vrp_ir import parse_file, parse_text, render_markdown, run_checks

RISKY = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                     "examples", "sample-usg-risky.cfg")


class TestCheckCoverage(unittest.TestCase):

    def test_counts_na_and_unchecked(self):
        cfg = parse_text("sysname X\nunknown-security-feature enable\n", filename="c.cfg")
        cc = run_checks(cfg).check_coverage()

        self.assertEqual(cc["asserted"], 0)
        self.assertEqual(cc["na"], 1)          # FW-DEFAULT-DENY (no security-policy)
        self.assertEqual(cc["unchecked"], 1)   # PARSER-UNCHECKED-LINES
        self.assertIn("FW-DEFAULT-DENY", cc["na_checks"])
        self.assertIn("PARSER-UNCHECKED-LINES", cc["unchecked_checks"])

    def test_asserting_config_reports_asserted(self):
        cc = run_checks(parse_file(RISKY)).check_coverage()
        self.assertGreaterEqual(cc["asserted"], 1)

    def test_markdown_has_coverage_limitations_section(self):
        cfg = parse_text("sysname X\nunknown-security-feature enable\n", filename="c.cfg")
        md = render_markdown(run_checks(cfg))

        self.assertIn("## Coverage & limitations", md)
        self.assertIn("Checks asserted", md)
        self.assertIn("Not asserted", md)
        self.assertIn("FW-DEFAULT-DENY", md)
        self.assertIn("PARSER-UNCHECKED-LINES", md)

    def test_to_dict_has_check_coverage(self):
        d = run_checks(parse_file(RISKY)).to_dict()

        self.assertIn("check_coverage", d)
        cc = d["check_coverage"]
        self.assertIn("asserted", cc)
        self.assertIn("na_checks", cc)
        self.assertIn("unchecked_checks", cc)
        self.assertGreaterEqual(cc["asserted"], 1)


if __name__ == "__main__":
    unittest.main()
