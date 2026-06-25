"""Tests for FW-SNMP-WEAK-COMMUNITY acceptance check."""
import json
import unittest

from vrp_ir import parse_text, render_markdown, run_checks
from vrp_ir.acceptance import CHECKS_META


class TestFwSnmpWeakCommunity(unittest.TestCase):

    def test_check_id_registered(self):
        self.assertIn("FW-SNMP-WEAK-COMMUNITY", CHECKS_META)

    def test_public_community_yields_medium_warn(self):
        cfg = parse_text("snmp-agent community read public\n", filename="snmp.cfg")

        finding = self._only_snmp_finding(cfg)

        self.assertEqual((finding.status, finding.severity), ("warn", "medium"))
        self.assertIn("public", finding.detail)
        self.assertIn("read", finding.detail)

    def test_private_community_is_case_insensitive(self):
        cfg = parse_text("snmp-agent community write PRIVATE\n")

        finding = self._only_snmp_finding(cfg)

        self.assertIn("PRIVATE", finding.detail)

    def test_custom_plaintext_community_yields_no_finding(self):
        cfg = parse_text("snmp-agent community read CustomerReadOnly\n")

        self.assertEqual(self._snmp_findings(cfg), [])

    def test_cipher_community_is_not_flagged(self):
        cfg = parse_text("snmp-agent community read cipher %^%#secret%^%#\n")

        self.assertEqual(self._snmp_findings(cfg), [])

    def test_each_finding_cites_offending_line(self):
        line = " snmp-agent community read public"
        cfg = parse_text("sysname FW\n" + line + "\n", filename="snmp.cfg")

        finding = self._only_snmp_finding(cfg)

        self.assertEqual(finding.evidence[0].file, "snmp.cfg")
        self.assertEqual(finding.evidence[0].line, 2)
        self.assertEqual(finding.evidence[0].raw, line)

    def test_multiple_defaults_yield_multiple_findings(self):
        cfg = parse_text(
            "snmp-agent community read public\n"
            "snmp-agent community write private\n"
        )

        self.assertEqual(len(self._snmp_findings(cfg)), 2)

    def test_rendered_reports_include_check(self):
        cfg = parse_text("snmp-agent community read public\n", filename="snmp.cfg")

        md = render_markdown(run_checks(cfg))
        data = json.loads(json.dumps(run_checks(cfg).to_dict(), ensure_ascii=False))

        self.assertIn("FW-SNMP-WEAK-COMMUNITY", md)
        self.assertIn("snmp.cfg:1", md)
        self.assertEqual(data["findings"][0]["check_id"], "FW-SNMP-WEAK-COMMUNITY")
        self.assertEqual(data["findings"][0]["evidence"][0]["line"], 1)

    def _snmp_findings(self, cfg):
        return [f for f in run_checks(cfg).findings
                if f.check_id == "FW-SNMP-WEAK-COMMUNITY"]

    def _only_snmp_finding(self, cfg):
        findings = self._snmp_findings(cfg)
        self.assertEqual(len(findings), 1)
        return findings[0]


if __name__ == "__main__":
    unittest.main()
