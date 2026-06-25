"""Tests for advisory standards anchoring (level-aware references)."""
import unittest

from vrp_ir import StandardRef, parse_text, render_markdown, run_checks


def _telnet_cfg():
    return parse_text("telnet server enable\n", filename="t.cfg")


class TestStandardsAnchoring(unittest.TestCase):

    def test_known_check_carries_advisory_references(self):
        f = next(x for x in run_checks(_telnet_cfg()).findings
                 if x.check_id == "FW-MGMT-TELNET")
        self.assertTrue(f.references)
        frameworks = {r.framework for r in f.references}
        self.assertIn("等保", frameworks)
        levels = {r.level for r in f.references if r.framework == "等保"}
        self.assertEqual(levels, {"三级", "四级"})

    def test_references_are_advisory_and_unverified_no_clause_numbers(self):
        f = next(x for x in run_checks(_telnet_cfg()).findings
                 if x.check_id == "FW-MGMT-TELNET")
        for r in f.references:
            self.assertTrue(r.advisory_only)
            self.assertFalse(r.manual_verified)   # (B): unverified, no clause numbers yet
            # control is a description, not a bare numeric clause id
            self.assertFalse(r.control.strip()[:1].isdigit())

    def test_unseeded_check_has_no_references(self):
        cfg = parse_text("hrp interface GigabitEthernet0/0/7 remote 10.0.0.2\n")
        f = next(x for x in run_checks(cfg).findings if x.check_id == "HRP-ENABLED")
        self.assertEqual(f.references, [])

    def test_to_dict_serializes_structured_references(self):
        d = run_checks(_telnet_cfg()).to_dict()
        finding = next(x for x in d["findings"] if x["check_id"] == "FW-MGMT-TELNET")
        ref = finding["references"][0]
        for key in ("framework", "control", "level", "advisory_only", "manual_verified"):
            self.assertIn(key, ref)

    def test_markdown_shows_advisory_disclaimer_and_unverified(self):
        md = render_markdown(run_checks(_telnet_cfg()))
        self.assertIn("**Advisory references** (not a certification claim)", md)
        self.assertIn("unverified mapping", md)
        self.assertIn("not** a compliance certification", md)

    def test_standardref_defaults(self):
        r = StandardRef("等保", "远程管理：禁用明文管理协议", level="三级")
        self.assertTrue(r.advisory_only)
        self.assertFalse(r.manual_verified)


if __name__ == "__main__":
    unittest.main()
