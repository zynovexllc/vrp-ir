"""Tests for HTTP server IR parsing and FW-MGMT-HTTP acceptance check."""
import unittest

from vrp_ir.parser import parse_text
from vrp_ir.acceptance import run_checks


class TestHttpParsing(unittest.TestCase):

    def test_http_enable_sets_true(self):
        cfg = parse_text("http server enable\n")
        h = cfg.http_server_enabled
        self.assertIsNotNone(h)
        self.assertTrue(h.value)

    def test_http_enable_sourceref_points_to_line(self):
        cfg = parse_text("sysname fw1\nhttp server enable\n")
        h = cfg.http_server_enabled
        self.assertIsNotNone(h)
        self.assertEqual(h.source.line, 2)
        self.assertIn("http server enable", h.source.raw)

    def test_undo_http_enable_sets_false(self):
        cfg = parse_text("undo http server enable\n")
        h = cfg.http_server_enabled
        self.assertIsNotNone(h)
        self.assertFalse(h.value)

    def test_no_http_line_yields_none(self):
        cfg = parse_text("sysname fw1\n")
        self.assertIsNone(cfg.http_server_enabled)


class TestHttpAcceptance(unittest.TestCase):

    def test_http_enabled_yields_high_fail(self):
        cfg = parse_text("http server enable\n")
        report = run_checks(cfg)
        http_findings = [f for f in report.findings if f.check_id == "FW-MGMT-HTTP"]
        self.assertEqual(len(http_findings), 1)
        finding = http_findings[0]
        self.assertEqual(finding.status, "fail")
        self.assertEqual(finding.severity, "high")
        self.assertEqual(len(finding.evidence), 1)
        self.assertIn("http server enable", finding.evidence[0].raw)

    def test_undo_http_yields_no_finding(self):
        cfg = parse_text("undo http server enable\n")
        report = run_checks(cfg)
        http_findings = [f for f in report.findings if f.check_id == "FW-MGMT-HTTP"]
        self.assertEqual(len(http_findings), 0)

    def test_no_http_line_yields_no_finding(self):
        cfg = parse_text("sysname fw1\n")
        report = run_checks(cfg)
        http_findings = [f for f in report.findings if f.check_id == "FW-MGMT-HTTP"]
        self.assertEqual(len(http_findings), 0)


if __name__ == "__main__":
    unittest.main()
