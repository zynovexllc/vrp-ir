"""Tests for the v0.4 security acceptance checks and report rendering."""
import json
import os
import unittest

from vrp_ir import parse_file, parse_text, render_markdown, run_checks

RISKY = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples", "sample-usg-risky.cfg")
CLEAN = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples", "sample-usg.cfg")


class TestAcceptance(unittest.TestCase):
    def test_risky_overall_fail_counts(self):
        r = run_checks(parse_file(RISKY))
        self.assertEqual(r.result, "fail")
        c = r.counts()
        self.assertEqual(c["fail"], 3)
        self.assertEqual(c["warn"], 2)

    def test_default_deny_fail_with_line_evidence(self):
        r = run_checks(parse_file(RISKY))
        f = next(x for x in r.findings if x.check_id == "FW-DEFAULT-DENY")
        self.assertEqual((f.status, f.severity), ("fail", "critical"))
        self.assertIn("default action permit", f.evidence[0].raw)  # evidenceRef

    def test_zone_iface_conflict_cites_both_lines(self):
        r = run_checks(parse_file(RISKY))
        f = next(x for x in r.findings if x.check_id == "FW-ZONE-IFACE-UNIQUE")
        self.assertEqual(f.status, "fail")
        self.assertEqual(len(f.evidence), 2)
        self.assertNotEqual(f.evidence[0].line, f.evidence[1].line)

    def test_only_unscoped_permit_rule_flagged(self):
        r = run_checks(parse_file(RISKY))
        scope = [x for x in r.findings if x.check_id == "FW-PERMIT-SCOPE"]
        self.assertEqual(len(scope), 1)            # any-to-any only, not web-in
        self.assertIn("any-to-any", scope[0].detail)

    def test_explicit_any_permit_flagged(self):
        # `source-zone any` is NON-empty yet means "all zones": must still flag.
        cfg = parse_text(
            "security-policy\n rule name allow-any\n  source-zone any\n"
            "  destination-zone any\n  action permit\n#\n")
        f = next(x for x in run_checks(cfg).findings if x.check_id == "FW-PERMIT-SCOPE")
        self.assertEqual((f.status, f.severity), ("fail", "high"))

    def test_address_only_permit_not_flagged(self):
        # Constrained by address (no zone) is NOT permit-any -> no FW-PERMIT-SCOPE.
        cfg = parse_text(
            "security-policy\n rule name addr-scoped\n"
            "  source-address 192.168.1.0 mask 24\n"
            "  destination-address 10.0.0.5 mask 32\n"
            "  action permit\n  session logging\n#\n")
        r = run_checks(cfg)
        self.assertEqual([x for x in r.findings if x.check_id == "FW-PERMIT-SCOPE"], [])

    def test_one_side_open_permit_warns(self):
        cfg = parse_text(
            "security-policy\n rule name half-open\n  source-zone trust\n"
            "  action permit\n#\n")
        f = next(x for x in run_checks(cfg).findings if x.check_id == "FW-PERMIT-SCOPE")
        self.assertEqual((f.status, f.severity), ("warn", "medium"))

    def test_zone_iface_same_zone_repeat_not_flagged(self):
        cfg = parse_text(
            "firewall zone trust\n add interface GigabitEthernet0/0/1\n"
            " add interface GigabitEthernet0/0/1\n#\n")
        r = run_checks(cfg)
        self.assertEqual([x for x in r.findings if x.check_id == "FW-ZONE-IFACE-UNIQUE"], [])

    def test_empty_report_renders_na_note(self):
        md = render_markdown(run_checks(parse_text("sysname X\n")))
        self.assertIn("No applicable", md)
        self.assertNotIn("PASS", md)   # must not claim PASS when nothing was checked

    def test_markdown_surfaces_parser_coverage(self):
        cfg = parse_text("sysname X\nunknown-security-feature enable\n", filename="cov.cfg")

        md = render_markdown(run_checks(cfg))

        self.assertIn("Parser coverage", md)
        self.assertIn("1/2 recognized (50.0%)", md)
        self.assertIn("cov.cfg:2", md)
        self.assertIn("unknown-security-feature enable", md)

    def test_clean_sample_warns_not_fails(self):
        r = run_checks(parse_file(CLEAN))
        self.assertEqual(r.result, "warn")
        self.assertFalse(any(x.status == "fail" for x in r.findings))
        dd = next(x for x in r.findings if x.check_id == "FW-DEFAULT-DENY")
        self.assertEqual(dd.status, "pass")        # explicit deny-all, no permit default

    def test_no_security_policy_yields_no_fw_findings(self):
        r = run_checks(parse_text("sysname X\n"))
        self.assertEqual([x.check_id for x in r.findings], [])

    def test_hrp_configured_but_disabled_warns(self):
        r = run_checks(parse_text("hrp interface GigabitEthernet0/0/7 remote 10.0.0.2\n"))
        hrp = next(x for x in r.findings if x.check_id == "HRP-ENABLED")
        self.assertEqual(hrp.status, "warn")

    def test_render_markdown_with_evidence(self):
        md = render_markdown(run_checks(parse_file(RISKY)))
        self.assertIn("Security Acceptance Report", md)
        self.assertIn("FW-DEFAULT-DENY", md)
        self.assertIn("default action permit", md)   # raw evidence line rendered

    def test_to_dict_json_roundtrip(self):
        r = run_checks(parse_file(RISKY))
        d = json.loads(json.dumps(r.to_dict(), ensure_ascii=False))
        self.assertEqual(d["result"], "fail")
        self.assertEqual(d["counts"]["fail"], 3)
        self.assertIn("raw", d["findings"][0]["evidence"][0])

    def test_to_dict_includes_parser_coverage(self):
        cfg = parse_text("sysname X\nunknown-security-feature enable\n", filename="cov.cfg")

        d = run_checks(cfg).to_dict()

        self.assertEqual(d["parser_coverage"]["analyzed_lines"], 2)
        self.assertEqual(d["parser_coverage"]["recognized_lines"], 1)
        self.assertEqual(d["parser_coverage"]["unparsed_lines"], 1)
        self.assertEqual(d["parser_coverage"]["coverage_percent"], 50.0)
        self.assertEqual(d["parser_coverage"]["unparsed"][0]["line"], 2)


if __name__ == "__main__":
    unittest.main()
