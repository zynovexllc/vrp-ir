"""Tests for FW-NTP-MISSING acceptance check."""
import json
import unittest

from vrp_ir import parse_text, render_markdown, run_checks
from vrp_ir.acceptance import CHECKS_META


class TestFwNtpMissing(unittest.TestCase):

    def test_check_id_registered(self):
        self.assertIn("FW-NTP-MISSING", CHECKS_META)

    def test_device_config_without_ntp_yields_medium_fail(self):
        cfg = parse_text(
            "interface GigabitEthernet0/0/1\n"
            " ip address 192.0.2.1 255.255.255.0\n"
            "#\n",
            filename="no-ntp.cfg",
        )

        finding = self._only_ntp_finding(cfg)

        self.assertEqual((finding.status, finding.severity), ("fail", "medium"))
        self.assertEqual(finding.evidence, [])
        self.assertIn("No NTP server", finding.detail)

    def test_ntp_server_present_yields_pass_with_evidence(self):
        cfg = parse_text(
            "interface GigabitEthernet0/0/1\n"
            " ip address 192.0.2.1 255.255.255.0\n"
            "#\n"
            "ntp-service unicast-server 10.0.0.1\n",
            filename="ntp.cfg",
        )

        finding = self._only_ntp_finding(cfg)

        self.assertEqual((finding.status, finding.severity), ("pass", "medium"))
        self.assertEqual(finding.evidence[0].line, 4)
        self.assertIn("ntp-service unicast-server", finding.evidence[0].raw)

    def test_minimal_snippet_without_device_scope_yields_no_ntp_finding(self):
        cfg = parse_text("sysname FW\n")

        self.assertEqual(self._ntp_findings(cfg), [])

    def test_report_and_json_include_ntp_missing(self):
        cfg = parse_text(
            "interface GigabitEthernet0/0/1\n"
            " ip address 192.0.2.1 255.255.255.0\n",
            filename="no-ntp.cfg",
        )

        report = run_checks(cfg)
        md = render_markdown(report)
        data = json.loads(json.dumps(report.to_dict(), ensure_ascii=False))

        self.assertEqual(report.result, "fail")
        self.assertIn("FW-NTP-MISSING", md)
        finding = next(f for f in data["findings"] if f["check_id"] == "FW-NTP-MISSING")
        self.assertEqual(finding["status"], "fail")
        self.assertEqual(finding["evidence"], [])

    def _ntp_findings(self, cfg):
        return [f for f in run_checks(cfg).findings if f.check_id == "FW-NTP-MISSING"]

    def _only_ntp_finding(self, cfg):
        findings = self._ntp_findings(cfg)
        self.assertEqual(len(findings), 1)
        return findings[0]


if __name__ == "__main__":
    unittest.main()
