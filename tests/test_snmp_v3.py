"""Tests for SNMPv3 parsing and the FW-SNMP-V3 acceptance check."""
import unittest

from vrp_ir import SnmpUsmUser, parse_text, run_checks
from vrp_ir.acceptance import CHECKS_META


class TestSnmpV3Parsing(unittest.TestCase):

    def test_usm_user_with_auth_and_privacy(self):
        cfg = parse_text(
            "snmp-agent usm-user v3 alice authentication-mode sha2-256 cipher AA "
            "privacy-mode aes128 cipher BB\n", filename="s.cfg")
        self.assertEqual(len(cfg.snmp_usm_users), 1)
        u = cfg.snmp_usm_users[0]
        self.assertIsInstance(u, SnmpUsmUser)
        self.assertEqual(u.name.value, "alice")
        self.assertEqual(u.auth_mode.value, "sha2-256")
        self.assertEqual(u.privacy_mode.value, "aes128")
        self.assertEqual(u.name.source.line, 1)

    def test_usm_user_multiline_merge(self):
        cfg = parse_text(
            "snmp-agent usm-user v3 carol authentication-mode sha2-256 cipher AA\n"
            "snmp-agent usm-user v3 carol privacy-mode aes128 cipher BB\n")
        self.assertEqual(len(cfg.snmp_usm_users), 1)
        u = cfg.snmp_usm_users[0]
        self.assertEqual(u.auth_mode.value, "sha2-256")
        self.assertEqual(u.privacy_mode.value, "aes128")

    def test_sys_info_version_tokens(self):
        cfg = parse_text("snmp-agent sys-info version v2c v3\n")
        self.assertEqual([v.value for v in cfg.snmp_versions], ["v2c", "v3"])

    def test_to_dict_keeps_usm_users(self):
        cfg = parse_text("snmp-agent usm-user v3 dan authentication-mode sha cipher X\n")
        data = cfg.to_dict()
        self.assertEqual(data["snmp_usm_users"][0]["name"]["value"], "dan")


class TestFwSnmpV3(unittest.TestCase):

    def _v3(self, cfg):
        return [f for f in run_checks(cfg).findings if f.check_id == "FW-SNMP-V3"]

    def test_check_registered(self):
        self.assertIn("FW-SNMP-V3", CHECKS_META)

    def test_v2c_enabled_flagged(self):
        cfg = parse_text("snmp-agent sys-info version v2c v3\n", filename="s.cfg")
        findings = self._v3(cfg)
        self.assertTrue(any("v2c" in f.detail for f in findings))
        v2c = next(f for f in findings if "v2c" in f.detail)
        self.assertEqual((v2c.status, v2c.severity), ("warn", "medium"))
        self.assertEqual(v2c.evidence[0].line, 1)

    def test_user_without_privacy_flagged(self):
        cfg = parse_text(
            "snmp-agent usm-user v3 eve authentication-mode sha2-256 cipher AA\n")
        findings = self._v3(cfg)
        self.assertEqual(len(findings), 1)
        self.assertIn("privacy", findings[0].detail)

    def test_fully_configured_user_not_flagged(self):
        cfg = parse_text(
            "snmp-agent sys-info version v3\n"
            "snmp-agent usm-user v3 frank authentication-mode sha2-256 cipher AA "
            "privacy-mode aes128 cipher BB\n")
        self.assertEqual(self._v3(cfg), [])

    def test_references_present(self):
        cfg = parse_text("snmp-agent sys-info version v2c\n")
        f = next(x for x in self._v3(cfg))
        self.assertTrue(any(r.framework == "等保" for r in f.references))


if __name__ == "__main__":
    unittest.main()
