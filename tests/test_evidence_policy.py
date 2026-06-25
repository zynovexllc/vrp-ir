"""Tests for the audit evidence policy: 'no source, no claim'."""
import os
import unittest

from vrp_ir import parse_file, parse_text, run_checks
from vrp_ir.acceptance import Finding

RISKY = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                     "examples", "sample-usg-risky.cfg")
CLEAN = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                     "examples", "sample-usg.cfg")


class TestEvidencePolicy(unittest.TestCase):

    def test_asserting_finding_without_evidence_requires_rationale(self):
        with self.assertRaises(ValueError):
            Finding("X", "high", "fail", "bare claim", [])

    def test_na_finding_may_have_no_evidence_or_rationale(self):
        # Should not raise.
        Finding("X", "info", "na", "not applicable", [])
        Finding("X", "info", "unchecked", "not checked", [])

    def test_no_bare_claims_across_sample_configs(self):
        for path in (RISKY, CLEAN):
            for f in run_checks(parse_file(path)).findings:
                if f.status in ("pass", "warn", "fail"):
                    self.assertTrue(
                        f.evidence or f.rationale,
                        f"{path}:{f.check_id} is a bare claim (no evidence, no rationale)")

    def test_cited_finding_is_high_confidence(self):
        f = next(x for x in run_checks(parse_file(RISKY)).findings
                 if x.check_id == "FW-MGMT-TELNET" or x.check_id == "FW-DEFAULT-DENY")
        self.assertTrue(f.evidence)
        self.assertEqual(f.confidence, "high")

    def test_absence_ntp_finding_is_low_confidence_with_rationale(self):
        cfg = parse_text(
            "interface GigabitEthernet0/0/1\n ip address 192.0.2.1 255.255.255.0\n#\n")
        f = next(x for x in run_checks(cfg).findings if x.check_id == "FW-NTP-MISSING")

        self.assertEqual((f.status, f.confidence), ("fail", "low"))
        self.assertEqual(f.evidence, [])
        self.assertIsNotNone(f.rationale)

    def test_implicit_default_deny_is_low_confidence_with_rationale(self):
        # security-policy present, but no explicit 'default action' line.
        cfg = parse_text(
            "security-policy\n rule name scoped\n  source-zone trust\n"
            "  destination-zone untrust\n  source-address 10.0.0.0 mask 24\n"
            "  destination-address 192.0.2.1 mask 32\n  action permit\n"
            "  session logging\n#\n")
        f = next(x for x in run_checks(cfg).findings if x.check_id == "FW-DEFAULT-DENY")

        self.assertEqual((f.status, f.confidence), ("pass", "low"))
        self.assertEqual(f.evidence, [])
        self.assertIsNotNone(f.rationale)

    def test_to_dict_exposes_confidence_rationale_references(self):
        d = run_checks(parse_file(RISKY)).to_dict()
        finding = d["findings"][0]

        self.assertIn("confidence", finding)
        self.assertIn("rationale", finding)
        self.assertIn("references", finding)
        self.assertIsInstance(finding["references"], list)

    def test_markdown_shows_confidence_and_basis(self):
        cfg = parse_text(
            "interface GigabitEthernet0/0/1\n ip address 192.0.2.1 255.255.255.0\n#\n")
        from vrp_ir import render_markdown
        md = render_markdown(run_checks(cfg))

        self.assertIn("Confidence:", md)
        self.assertIn("Basis:", md)


if __name__ == "__main__":
    unittest.main()
