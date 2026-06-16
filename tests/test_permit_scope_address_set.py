"""Tests for FW-PERMIT-SCOPE dereference of address-set references (issue #12).

A permit rule whose only narrowing is an address-set that resolves to any
(contains a 0.0.0.0/0 member) must still be flagged as not narrowed.
"""
import unittest

from vrp_ir import parse_text, run_checks


class TestPermitScopeAddressSetDeref(unittest.TestCase):

    def test_any_resolving_dst_address_set_flags_rule(self):
        """A destination address-set containing 0.0.0.0/0 must yield a finding."""
        cfg = parse_text(
            "ip address-set wildcard type object\n"
            " address 0 0.0.0.0 mask 0\n"
            "#\n"
            "security-policy\n"
            " rule name hidden-any\n"
            "  source-zone trust\n"
            "  destination-address address-set wildcard\n"
            "  action permit\n"
            "#\n"
        )
        findings = [f for f in run_checks(cfg).findings if f.check_id == "FW-PERMIT-SCOPE"]
        self.assertEqual(len(findings), 1)
        self.assertIn("hidden-any", findings[0].detail)

    def test_any_resolving_src_address_set_flags_rule(self):
        """A source address-set containing 0.0.0.0/0 must yield a finding."""
        cfg = parse_text(
            "ip address-set allsrc type object\n"
            " address 0 0.0.0.0 mask 0\n"
            "#\n"
            "security-policy\n"
            " rule name src-hidden-any\n"
            "  source-address address-set allsrc\n"
            "  destination-zone untrust\n"
            "  action permit\n"
            "#\n"
        )
        findings = [f for f in run_checks(cfg).findings if f.check_id == "FW-PERMIT-SCOPE"]
        self.assertEqual(len(findings), 1)
        self.assertIn("src-hidden-any", findings[0].detail)

    def test_normal_address_set_not_flagged(self):
        """A permit rule referencing a /32 address-set must NOT be flagged."""
        cfg = parse_text(
            "ip address-set hosts type object\n"
            " address 0 10.0.0.1 mask 32\n"
            "#\n"
            "security-policy\n"
            " rule name specific-host\n"
            "  source-zone trust\n"
            "  destination-address address-set hosts\n"
            "  action permit\n"
            "  session logging\n"
            "#\n"
        )
        findings = [f for f in run_checks(cfg).findings if f.check_id == "FW-PERMIT-SCOPE"]
        self.assertEqual(findings, [])

    def test_both_sides_any_address_set_gives_high_fail(self):
        """Both sides resolved to any -> high severity fail."""
        cfg = parse_text(
            "ip address-set everywhere type object\n"
            " address 0 0.0.0.0 mask 0\n"
            "#\n"
            "security-policy\n"
            " rule name full-any\n"
            "  source-address address-set everywhere\n"
            "  destination-address address-set everywhere\n"
            "  action permit\n"
            "#\n"
        )
        findings = [f for f in run_checks(cfg).findings if f.check_id == "FW-PERMIT-SCOPE"]
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].status, "fail")
        self.assertEqual(findings[0].severity, "high")

    def test_finding_cites_rule_source_line(self):
        """The finding evidence must reference the rule definition line."""
        cfg = parse_text(
            "ip address-set open type object\n"
            " address 0 0.0.0.0 mask 0\n"
            "#\n"
            "security-policy\n"
            " rule name wide-open\n"
            "  source-zone trust\n"
            "  destination-address address-set open\n"
            "  action permit\n"
            "#\n"
        )
        findings = [f for f in run_checks(cfg).findings if f.check_id == "FW-PERMIT-SCOPE"]
        self.assertEqual(len(findings), 1)
        self.assertTrue(findings[0].evidence, "finding must have evidence")
        # Evidence must point at the rule line
        self.assertIsNotNone(findings[0].evidence[0].line)

    def test_unknown_address_set_name_treated_as_narrowing(self):
        """An address-set reference whose set is not defined is conservatively kept as narrowing."""
        cfg = parse_text(
            "security-policy\n"
            " rule name ref-unknown\n"
            "  source-zone trust\n"
            "  destination-address address-set ghost\n"
            "  action permit\n"
            "#\n"
        )
        findings = [f for f in run_checks(cfg).findings if f.check_id == "FW-PERMIT-SCOPE"]
        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
