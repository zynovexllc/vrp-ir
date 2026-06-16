"""Tests for telnet server IR parsing and FW-MGMT-TELNET acceptance check."""
import unittest

from vrp_ir.parser import parse_text
from vrp_ir.acceptance import run_checks


class TestTelnetParsing(unittest.TestCase):

    def test_telnet_enable_sets_true(self):
        cfg = parse_text("telnet server enable\n")
        t = cfg.telnet_server_enabled
        self.assertIsNotNone(t)
        self.assertTrue(t.value)

    def test_telnet_enable_sourceref_points_to_line(self):
        cfg = parse_text("sysname fw1\ntelnet server enable\n")
        t = cfg.telnet_server_enabled
        self.assertIsNotNone(t)
        self.assertEqual(t.source.line, 2)
        self.assertIn("telnet server enable", t.source.raw)

    def test_undo_telnet_enable_sets_false(self):
        cfg = parse_text("undo telnet server enable\n")
        t = cfg.telnet_server_enabled
        self.assertIsNotNone(t)
        self.assertFalse(t.value)

    def test_no_telnet_line_yields_none(self):
        cfg = parse_text("sysname fw1\n")
        self.assertIsNone(cfg.telnet_server_enabled)


class TestTelnetAcceptance(unittest.TestCase):

    def test_telnet_enabled_yields_high_fail(self):
        cfg = parse_text("telnet server enable\n")
        report = run_checks(cfg)
        telnet_findings = [f for f in report.findings if f.check_id == "FW-MGMT-TELNET"]
        self.assertEqual(len(telnet_findings), 1)
        finding = telnet_findings[0]
        self.assertEqual(finding.status, "fail")
        self.assertEqual(finding.severity, "high")
        self.assertEqual(len(finding.evidence), 1)
        self.assertIn("telnet server enable", finding.evidence[0].raw)

    def test_undo_telnet_yields_no_finding(self):
        cfg = parse_text("undo telnet server enable\n")
        report = run_checks(cfg)
        telnet_findings = [f for f in report.findings if f.check_id == "FW-MGMT-TELNET"]
        self.assertEqual(len(telnet_findings), 0)

    def test_no_telnet_line_yields_no_finding(self):
        cfg = parse_text("sysname fw1\n")
        report = run_checks(cfg)
        telnet_findings = [f for f in report.findings if f.check_id == "FW-MGMT-TELNET"]
        self.assertEqual(len(telnet_findings), 0)


if __name__ == "__main__":
    unittest.main()
