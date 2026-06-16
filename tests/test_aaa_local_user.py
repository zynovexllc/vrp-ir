"""Tests for aaa local-user service-type parsing and FW-AAA-LOCAL-USER-TELNET check."""
import unittest

from vrp_ir.parser import parse_text
from vrp_ir.acceptance import run_checks


class TestAaaLocalUserParsing(unittest.TestCase):

    def test_local_user_ssh_and_telnet(self):
        cfg = parse_text(
            "aaa\n"
            " local-user admin service-type ssh telnet\n"
            "#\n"
        )
        self.assertEqual(len(cfg.local_users), 1)
        user = cfg.local_users[0]
        self.assertEqual(user.name.value, "admin")
        svc_values = [s.value for s in user.service_types]
        self.assertIn("ssh", svc_values)
        self.assertIn("telnet", svc_values)
        self.assertEqual(len(user.service_types), 2)

    def test_local_user_ssh_only(self):
        cfg = parse_text(
            "aaa\n"
            " local-user readonly service-type ssh\n"
            "#\n"
        )
        self.assertEqual(len(cfg.local_users), 1)
        user = cfg.local_users[0]
        self.assertEqual(user.name.value, "readonly")
        svc_values = [s.value for s in user.service_types]
        self.assertEqual(svc_values, ["ssh"])

    def test_no_aaa_block(self):
        cfg = parse_text("sysname router\n")
        self.assertEqual(cfg.local_users, [])

    def test_source_ref_on_service_types(self):
        text = "aaa\n local-user admin service-type ssh telnet\n#\n"
        cfg = parse_text(text, filename="test.cfg")
        user = cfg.local_users[0]
        for svc in user.service_types:
            self.assertEqual(svc.source.file, "test.cfg")
            self.assertEqual(svc.source.line, 2)

    def test_aaa_other_lines_ignored(self):
        cfg = parse_text(
            "aaa\n"
            " authentication-scheme default\n"
            " local-user admin service-type ssh\n"
            "#\n"
        )
        self.assertEqual(len(cfg.local_users), 1)

    def test_multiple_local_users(self):
        cfg = parse_text(
            "aaa\n"
            " local-user admin service-type ssh telnet\n"
            " local-user monitor service-type ssh\n"
            "#\n"
        )
        self.assertEqual(len(cfg.local_users), 2)
        names = [u.name.value for u in cfg.local_users]
        self.assertIn("admin", names)
        self.assertIn("monitor", names)


class TestFwAaaLocalUserTelnet(unittest.TestCase):

    def test_telnet_service_type_yields_warn(self):
        cfg = parse_text(
            "aaa\n"
            " local-user admin service-type ssh telnet\n"
            "#\n"
        )
        report = run_checks(cfg)
        findings = [f for f in report.findings if f.check_id == "FW-AAA-LOCAL-USER-TELNET"]
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].status, "warn")
        self.assertEqual(findings[0].severity, "medium")
        self.assertIn("admin", findings[0].detail)

    def test_telnet_finding_cites_source_line(self):
        text = "aaa\n local-user admin service-type ssh telnet\n#\n"
        cfg = parse_text(text, filename="fw.cfg")
        report = run_checks(cfg)
        findings = [f for f in report.findings if f.check_id == "FW-AAA-LOCAL-USER-TELNET"]
        self.assertEqual(len(findings), 1)
        self.assertEqual(len(findings[0].evidence), 1)
        self.assertEqual(findings[0].evidence[0].file, "fw.cfg")
        self.assertEqual(findings[0].evidence[0].line, 2)

    def test_ssh_only_no_finding(self):
        cfg = parse_text(
            "aaa\n"
            " local-user readonly service-type ssh\n"
            "#\n"
        )
        report = run_checks(cfg)
        findings = [f for f in report.findings if f.check_id == "FW-AAA-LOCAL-USER-TELNET"]
        self.assertEqual(len(findings), 0)

    def test_no_aaa_block_no_finding(self):
        cfg = parse_text("sysname router\n")
        report = run_checks(cfg)
        findings = [f for f in report.findings if f.check_id == "FW-AAA-LOCAL-USER-TELNET"]
        self.assertEqual(len(findings), 0)

    def test_multiple_users_only_telnet_user_flagged(self):
        cfg = parse_text(
            "aaa\n"
            " local-user admin service-type ssh telnet\n"
            " local-user monitor service-type ssh\n"
            "#\n"
        )
        report = run_checks(cfg)
        findings = [f for f in report.findings if f.check_id == "FW-AAA-LOCAL-USER-TELNET"]
        self.assertEqual(len(findings), 1)
        self.assertIn("admin", findings[0].detail)

    def test_two_telnet_users_two_findings(self):
        cfg = parse_text(
            "aaa\n"
            " local-user admin service-type telnet\n"
            " local-user guest service-type telnet\n"
            "#\n"
        )
        report = run_checks(cfg)
        findings = [f for f in report.findings if f.check_id == "FW-AAA-LOCAL-USER-TELNET"]
        self.assertEqual(len(findings), 2)


if __name__ == "__main__":
    unittest.main()
