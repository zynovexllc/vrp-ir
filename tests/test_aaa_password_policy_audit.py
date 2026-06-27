"""Tests for explicit-weakening audit checks in local-aaa-user password policy views."""
import unittest

from vrp_ir import parse_text, run_checks
from vrp_ir.acceptance import CHECKS_META


class TestAaaPasswordPolicyAudit(unittest.TestCase):

    def _findings(self, text: str):
        return run_checks(parse_text(text, filename="audit.cfg")).findings

    def test_catalogue_contains_new_checks(self):
        self.assertIn("FW-AAA-PASSWORD-EXPIRE-DISABLED", CHECKS_META)
        self.assertIn("FW-AAA-PASSWORD-ALERT-DISABLED", CHECKS_META)
        self.assertIn("FW-AAA-PASSWORD-INITIAL-CHANGE-DISABLED", CHECKS_META)
        self.assertIn("FW-AAA-PASSWORD-HISTORY-DISABLED", CHECKS_META)

    def test_explicit_password_expire_zero_warns(self):
        findings = [
            f for f in self._findings(
                "aaa\n"
                " local-aaa-user password policy administrator\n"
                "  password expire 0\n"
                "  quit\n"
                "#\n"
            )
            if f.check_id == "FW-AAA-PASSWORD-EXPIRE-DISABLED"
        ]

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].status, "warn")
        self.assertIn("administrator", findings[0].detail)
        self.assertEqual(findings[0].evidence[0].line, 3)

    def test_explicit_alert_zero_warns(self):
        findings = [
            f for f in self._findings(
                "aaa\n"
                " local-aaa-user password policy administrator\n"
                "  password alert before-expire 0\n"
                "  quit\n"
                "#\n"
            )
            if f.check_id == "FW-AAA-PASSWORD-ALERT-DISABLED"
        ]

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].severity, "low")
        self.assertIn("no expiry warning", findings[0].detail)

    def test_undo_password_alert_original_warns(self):
        findings = [
            f for f in self._findings(
                "aaa\n"
                " local-aaa-user password policy administrator\n"
                "  undo password alert original\n"
                "  quit\n"
                "#\n"
            )
            if f.check_id == "FW-AAA-PASSWORD-INITIAL-CHANGE-DISABLED"
        ]

        self.assertEqual(len(findings), 1)
        self.assertIn("undo password alert original", findings[0].detail)

    def test_password_history_zero_warns_and_preserves_scope(self):
        findings = [
            f for f in self._findings(
                "aaa\n"
                " local-aaa-user password policy access-user\n"
                "  password history record number 0\n"
                "  quit\n"
                "#\n"
            )
            if f.check_id == "FW-AAA-PASSWORD-HISTORY-DISABLED"
        ]

        self.assertEqual(len(findings), 1)
        self.assertIn("access-user", findings[0].detail)
        self.assertEqual(findings[0].evidence[0].line, 3)

    def test_no_finding_without_explicit_weakening(self):
        findings = [
            f for f in self._findings(
                "aaa\n"
                " local-aaa-user password policy administrator\n"
                "  password expire 30\n"
                "  password alert before-expire 15\n"
                "  password alert original\n"
                "  password history record number 5\n"
                "  quit\n"
                "#\n"
            )
            if f.check_id.startswith("FW-AAA-PASSWORD-")
        ]

        self.assertEqual(findings, [])

    def test_no_finding_on_undo_parent_only(self):
        findings = [
            f for f in self._findings(
                "aaa\n"
                " undo local-aaa-user password policy administrator\n"
                "#\n"
            )
            if f.check_id.startswith("FW-AAA-PASSWORD-")
        ]

        self.assertEqual(findings, [])

    def test_fixture_like_case_returns_warn_with_four_findings(self):
        report = run_checks(parse_text(
            "sysname AP-POLICY-01\n"
            "ntp-service unicast-server 192.0.2.10\n"
            "aaa\n"
            " local-aaa-user password policy administrator\n"
            "  password expire 0\n"
            "  password alert before-expire 0\n"
            "  undo password alert original\n"
            "  password history record number 0\n"
            "  quit\n"
            " local-aaa-user password policy access-user\n"
            "  password history record number 3\n"
            "  quit\n"
            " local-user ops service-type ssh\n"
            "#\n"
        ))

        findings = [f for f in report.findings if f.check_id.startswith("FW-AAA-PASSWORD-")]
        self.assertEqual(report.result, "warn")
        self.assertEqual(len(findings), 4)


if __name__ == "__main__":
    unittest.main()
