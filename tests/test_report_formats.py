"""Tests for SARIF and JUnit audit output formats."""
import io
import json
import os
import unittest
import xml.etree.ElementTree as ET
from contextlib import redirect_stdout

from vrp_ir import parse_file, render_junit, render_sarif, run_checks
from vrp_ir.cli import main

RISKY = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                     "examples", "sample-usg-risky.cfg")


class TestSarif(unittest.TestCase):
    def setUp(self):
        self.report = run_checks(parse_file(RISKY))
        self.doc = json.loads(render_sarif(self.report))

    def test_sarif_envelope(self):
        self.assertEqual(self.doc["version"], "2.1.0")
        driver = self.doc["runs"][0]["tool"]["driver"]
        self.assertEqual(driver["name"], "vrp-ir")
        self.assertTrue(driver["rules"])

    def test_fail_result_has_error_level_and_location(self):
        results = self.doc["runs"][0]["results"]
        dd = next(r for r in results if r["ruleId"] == "FW-DEFAULT-DENY")
        self.assertEqual(dd["level"], "error")
        region = dd["locations"][0]["physicalLocation"]["region"]
        self.assertEqual(region["startLine"], 14)

    def test_pass_and_na_are_not_results(self):
        rule_ids = {r["ruleId"] for r in self.doc["runs"][0]["results"]}
        # only fail/warn/unchecked become results
        for r in self.doc["runs"][0]["results"]:
            self.assertIn(r["level"], ("error", "warning", "note"))
        self.assertIn("FW-DEFAULT-DENY", rule_ids)


class TestJunit(unittest.TestCase):
    def setUp(self):
        self.xml = ET.fromstring(render_junit(run_checks(parse_file(RISKY))))

    def test_testsuite_counts(self):
        suite = self.xml.find("testsuite")
        self.assertIsNotNone(suite)
        self.assertGreater(int(suite.get("failures")), 0)

    def test_fail_testcase_has_failure(self):
        cases = self.xml.iter("testcase")
        dd = next(c for c in cases if c.get("name") == "FW-DEFAULT-DENY")
        self.assertIsNotNone(dd.find("failure"))

    def test_na_testcase_is_skipped(self):
        # mgmt-cn style: use a config where default-deny is NA
        from vrp_ir import parse_text
        xml = ET.fromstring(render_junit(run_checks(parse_text("sysname X\n"))))
        dd = next(c for c in xml.iter("testcase") if c.get("name") == "FW-DEFAULT-DENY")
        self.assertIsNotNone(dd.find("skipped"))


class TestCliFormats(unittest.TestCase):
    def _run(self, fmt):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["audit", RISKY, "--format", fmt])
        return code, buf.getvalue()

    def test_cli_sarif_is_valid_json(self):
        code, out = self._run("sarif")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["version"], "2.1.0")

    def test_cli_junit_is_valid_xml(self):
        code, out = self._run("junit")
        self.assertEqual(code, 0)
        self.assertEqual(ET.fromstring(out).tag, "testsuites")

    def test_cli_strict_exit_code_on_fail(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["audit", RISKY, "--format", "sarif", "--strict"])
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
