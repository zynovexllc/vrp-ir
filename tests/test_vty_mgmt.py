"""Tests for FW-MGMT-VTY-TELNET and FW-MGMT-VTY-NO-ACL acceptance checks (issue #24 / v0.6)."""
import unittest

from vrp_ir.parser import parse_text
from vrp_ir.acceptance import run_checks, CHECKS_META


VTY_ALL_NO_ACL = """\
user-interface vty 0 4
 protocol inbound all
#
"""

VTY_TELNET_NO_ACL = """\
user-interface vty 0 4
 protocol inbound telnet
#
"""

VTY_SSH_WITH_ACL = """\
user-interface vty 0 4
 protocol inbound ssh
 acl 2000 inbound
#
"""

VTY_TELNET_WITH_ACL = """\
user-interface vty 0 4
 protocol inbound telnet
 acl 2000 inbound
#
"""

CON_WITH_TELNET = """\
user-interface con 0
 protocol inbound telnet
#
"""


class TestChecksMetaRegistered(unittest.TestCase):

    def test_vty_telnet_in_meta(self):
        self.assertIn("FW-MGMT-VTY-TELNET", CHECKS_META)

    def test_vty_no_acl_in_meta(self):
        self.assertIn("FW-MGMT-VTY-NO-ACL", CHECKS_META)


class TestVtyTelnetCheck(unittest.TestCase):

    def _findings(self, text, check_id):
        cfg = parse_text(text)
        report = run_checks(cfg)
        return [f for f in report.findings if f.check_id == check_id]

    def test_protocol_all_yields_high_fail(self):
        findings = self._findings(VTY_ALL_NO_ACL, "FW-MGMT-VTY-TELNET")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].status, "fail")
        self.assertEqual(findings[0].severity, "high")

    def test_protocol_telnet_yields_high_fail(self):
        findings = self._findings(VTY_TELNET_NO_ACL, "FW-MGMT-VTY-TELNET")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].status, "fail")
        self.assertEqual(findings[0].severity, "high")

    def test_protocol_all_evidence_cites_protocol_line(self):
        findings = self._findings(VTY_ALL_NO_ACL, "FW-MGMT-VTY-TELNET")
        self.assertEqual(len(findings[0].evidence), 1)
        self.assertIn("protocol inbound all", findings[0].evidence[0].raw)

    def test_protocol_ssh_yields_no_telnet_finding(self):
        findings = self._findings(VTY_SSH_WITH_ACL, "FW-MGMT-VTY-TELNET")
        self.assertEqual(len(findings), 0)

    def test_telnet_with_acl_still_yields_telnet_finding(self):
        """ACL presence does not suppress the telnet protocol finding."""
        findings = self._findings(VTY_TELNET_WITH_ACL, "FW-MGMT-VTY-TELNET")
        self.assertEqual(len(findings), 1)

    def test_con_line_never_flagged(self):
        findings = self._findings(CON_WITH_TELNET, "FW-MGMT-VTY-TELNET")
        self.assertEqual(len(findings), 0)


class TestVtyNoAclCheck(unittest.TestCase):

    def _findings(self, text, check_id):
        cfg = parse_text(text)
        report = run_checks(cfg)
        return [f for f in report.findings if f.check_id == check_id]

    def test_protocol_set_no_acl_yields_medium_warn(self):
        findings = self._findings(VTY_ALL_NO_ACL, "FW-MGMT-VTY-NO-ACL")
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].status, "warn")
        self.assertEqual(findings[0].severity, "medium")

    def test_no_acl_evidence_cites_vty_header_line(self):
        findings = self._findings(VTY_ALL_NO_ACL, "FW-MGMT-VTY-NO-ACL")
        self.assertEqual(len(findings[0].evidence), 1)
        self.assertIn("user-interface vty", findings[0].evidence[0].raw)

    def test_ssh_with_acl_yields_no_no_acl_finding(self):
        findings = self._findings(VTY_SSH_WITH_ACL, "FW-MGMT-VTY-NO-ACL")
        self.assertEqual(len(findings), 0)

    def test_telnet_with_acl_yields_no_no_acl_finding(self):
        findings = self._findings(VTY_TELNET_WITH_ACL, "FW-MGMT-VTY-NO-ACL")
        self.assertEqual(len(findings), 0)

    def test_con_line_never_flagged(self):
        findings = self._findings(CON_WITH_TELNET, "FW-MGMT-VTY-NO-ACL")
        self.assertEqual(len(findings), 0)


class TestVtyAllNoAclYieldsBothFindings(unittest.TestCase):
    """AC: protocol inbound all + no ACL -> one TELNET fail + one NO-ACL warn."""

    def setUp(self):
        cfg = parse_text(VTY_ALL_NO_ACL)
        report = run_checks(cfg)
        self.telnet = [f for f in report.findings if f.check_id == "FW-MGMT-VTY-TELNET"]
        self.no_acl = [f for f in report.findings if f.check_id == "FW-MGMT-VTY-NO-ACL"]

    def test_exactly_one_telnet_finding(self):
        self.assertEqual(len(self.telnet), 1)

    def test_exactly_one_no_acl_finding(self):
        self.assertEqual(len(self.no_acl), 1)

    def test_telnet_is_high_fail(self):
        self.assertEqual(self.telnet[0].severity, "high")
        self.assertEqual(self.telnet[0].status, "fail")

    def test_no_acl_is_medium_warn(self):
        self.assertEqual(self.no_acl[0].severity, "medium")
        self.assertEqual(self.no_acl[0].status, "warn")


class TestExistingConfigsUnchanged(unittest.TestCase):
    """Sample-safety: configs with no user-interface block yield no new findings."""

    def test_sysname_only_no_vty_findings(self):
        cfg = parse_text("sysname fw1\n")
        report = run_checks(cfg)
        vty_findings = [f for f in report.findings
                        if f.check_id in ("FW-MGMT-VTY-TELNET", "FW-MGMT-VTY-NO-ACL")]
        self.assertEqual(len(vty_findings), 0)


if __name__ == "__main__":
    unittest.main()
