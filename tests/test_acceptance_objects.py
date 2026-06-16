"""Tests for object-aware acceptance checks (FW-ADDRESS-SET-ANY).

Kept in a dedicated file; uses inline configs so the shipped clean sample's
audit result is unaffected.
"""
import os
import unittest

from vrp_ir import parse_file, parse_text, run_checks

CLEAN = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples", "sample-usg.cfg")


class TestAddressSetAny(unittest.TestCase):
    def test_wildcard_member_flagged_with_evidence(self):
        cfg = parse_text(
            "ip address-set wide type group\n"
            " address 0 0.0.0.0 mask 0\n"
            "#\n")
        f = next(x for x in run_checks(cfg).findings
                 if x.check_id == "FW-ADDRESS-SET-ANY")
        self.assertEqual((f.status, f.severity), ("fail", "high"))
        self.assertIn("0.0.0.0 mask 0", f.evidence[0].raw)
        self.assertEqual(f.evidence[0].line, 2)

    def test_normal_members_not_flagged(self):
        cfg = parse_text(
            "ip address-set hosts type group\n"
            " address 0 10.0.0.0 mask 24\n"
            " address 1 192.168.1.1 mask 32\n"
            "#\n")
        self.assertEqual(
            [x for x in run_checks(cfg).findings if x.check_id == "FW-ADDRESS-SET-ANY"],
            [])

    def test_range_member_not_flagged(self):
        # A range member has no mask -> must not be guessed as any (no garbage).
        cfg = parse_text(
            "ip address-set pool type group\n"
            " address 0 10.0.0.1 10.0.0.9\n"
            "#\n")
        self.assertEqual(
            [x for x in run_checks(cfg).findings if x.check_id == "FW-ADDRESS-SET-ANY"],
            [])

    def test_clean_sample_has_no_address_set_any(self):
        # Shipped sample's sets are /32 and /24: no FW-ADDRESS-SET-ANY, still warn.
        r = run_checks(parse_file(CLEAN))
        self.assertEqual([x for x in r.findings if x.check_id == "FW-ADDRESS-SET-ANY"], [])
        self.assertFalse(any(x.status == "fail" for x in r.findings))


if __name__ == "__main__":
    unittest.main()
