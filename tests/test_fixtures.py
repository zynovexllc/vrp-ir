"""Regression tests for checked-in de-identified golden fixtures."""
import os
import unittest

from vrp_ir import parse_file, run_checks


FIXTURE = os.path.join(
    os.path.dirname(__file__), "fixtures", "deidentified-golden-vrp.cfg")


class TestDeidentifiedGoldenFixture(unittest.TestCase):

    def test_fixture_parses_with_source_refs(self):
        cfg = parse_file(FIXTURE)

        self.assertEqual(cfg.hostname.value, "FW-EDGE-01")
        self.assertEqual(cfg.ntp_servers[0].address.value, "192.0.2.10")
        self.assertEqual(cfg.log_hosts[0].address.value, "192.0.2.20")
        self.assertEqual(cfg.interfaces[0].description.value, "上联核心-示例")
        self.assertIn("上联核心-示例", cfg.interfaces[0].description.source.raw)
        self.assertEqual(cfg.unparsed_lines, [])

    def test_fixture_audit_has_full_parser_coverage(self):
        report = run_checks(parse_file(FIXTURE))

        self.assertEqual(report.parser_coverage()["coverage_percent"], 100.0)
        self.assertFalse(any(f.status == "unchecked" for f in report.findings))


if __name__ == "__main__":
    unittest.main()
