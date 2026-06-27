"""Tests for scope-aware user-password complexity-check parsing and audit."""
import os
import unittest

from vrp_ir import parse_file, parse_text, run_checks
from vrp_ir.acceptance import CHECKS_META


FIXTURE = os.path.join(
    os.path.dirname(__file__), "fixtures", "aaa-complexity-scope.cfg")


class TestUserPasswordComplexityParsing(unittest.TestCase):

    def test_parse_aaa_scope_three_of_kinds(self):
        cfg = parse_text(
            "aaa\n"
            " user-password complexity-check three-of-kinds\n"
            "#\n",
            filename="complexity.cfg",
        )

        self.assertEqual(len(cfg.user_password_complexity_checks), 1)
        check = cfg.user_password_complexity_checks[0]
        self.assertEqual(check.scope.value, "aaa")
        self.assertTrue(check.enabled.value)
        self.assertEqual(check.strength_mode.value, "three-of-kinds")
        self.assertEqual(check.source.file, "complexity.cfg")
        self.assertEqual(check.source.line, 2)

    def test_parse_local_aaa_server_scope_disable(self):
        cfg = parse_text(
            "local-aaa-server\n"
            " undo user-password complexity-check\n"
            "#\n"
        )

        self.assertEqual(len(cfg.user_password_complexity_checks), 1)
        check = cfg.user_password_complexity_checks[0]
        self.assertEqual(check.scope.value, "local-aaa-server")
        self.assertFalse(check.enabled.value)
        self.assertIsNone(check.strength_mode)

    def test_scope_preserved_for_both_views(self):
        cfg = parse_text(
            "aaa\n"
            " user-password complexity-check\n"
            "#\n"
            "local-aaa-server\n"
            " undo user-password complexity-check\n"
            "#\n"
        )

        self.assertEqual(len(cfg.user_password_complexity_checks), 2)
        by_scope = {c.scope.value: c for c in cfg.user_password_complexity_checks}
        self.assertTrue(by_scope["aaa"].enabled.value)
        self.assertFalse(by_scope["local-aaa-server"].enabled.value)

    def test_fixture_parses_without_unparsed_lines(self):
        cfg = parse_file(FIXTURE)

        self.assertEqual(cfg.unparsed_lines, [])
        by_scope = {c.scope.value: c for c in cfg.user_password_complexity_checks}
        self.assertEqual(sorted(by_scope), ["aaa", "local-aaa-server"])
        self.assertEqual(by_scope["aaa"].strength_mode.value, "three-of-kinds")
        self.assertFalse(by_scope["local-aaa-server"].enabled.value)


class TestUserPasswordComplexityAudit(unittest.TestCase):

    def test_catalogue_contains_new_check(self):
        self.assertIn("FW-AAA-PASSWORD-COMPLEXITY-DISABLED", CHECKS_META)

    def test_warns_only_on_explicit_disable(self):
        report = run_checks(parse_text(
            "aaa\n"
            " user-password complexity-check three-of-kinds\n"
            "#\n"
            "local-aaa-server\n"
            " undo user-password complexity-check\n"
            "#\n",
            filename="audit.cfg",
        ))
        findings = [f for f in report.findings if f.check_id == "FW-AAA-PASSWORD-COMPLEXITY-DISABLED"]

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].status, "warn")
        self.assertIn("local-aaa-server", findings[0].detail)
        self.assertEqual(findings[0].evidence[0].file, "audit.cfg")
        self.assertEqual(findings[0].evidence[0].line, 5)

    def test_no_finding_for_enabled_command(self):
        report = run_checks(parse_text(
            "aaa\n"
            " user-password complexity-check\n"
            "#\n"
        ))
        findings = [f for f in report.findings if f.check_id == "FW-AAA-PASSWORD-COMPLEXITY-DISABLED"]
        self.assertEqual(findings, [])

    def test_no_absence_based_finding(self):
        report = run_checks(parse_text("sysname X\n", filename="absent.cfg"))
        findings = [f for f in report.findings if f.check_id == "FW-AAA-PASSWORD-COMPLEXITY-DISABLED"]
        self.assertEqual(findings, [])


if __name__ == "__main__":
    unittest.main()
