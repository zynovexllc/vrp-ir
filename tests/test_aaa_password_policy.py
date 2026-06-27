"""Tests for local-aaa-user password-policy view parsing."""
import os
import unittest

from vrp_ir import parse_file, parse_text


FIXTURE = os.path.join(
    os.path.dirname(__file__), "fixtures", "aaa-password-policy.cfg")


class TestAaaPasswordPolicyParsing(unittest.TestCase):

    def test_parse_administrator_policy_view(self):
        cfg = parse_text(
            "aaa\n"
            " local-aaa-user password policy administrator\n"
            "  password expire 0\n"
            "  password alert before-expire 0\n"
            "  undo password alert original\n"
            "  password history record number 0\n"
            "  quit\n"
            "#\n",
            filename="policy.cfg",
        )

        self.assertEqual(len(cfg.local_aaa_password_policies), 1)
        policy = cfg.local_aaa_password_policies[0]
        self.assertEqual(policy.scope.value, "administrator")
        self.assertTrue(policy.enabled.value)
        self.assertEqual(policy.password_expire_days.value, 0)
        self.assertEqual(policy.password_alert_before_expire_days.value, 0)
        self.assertFalse(policy.password_alert_original.value)
        self.assertEqual(policy.password_history_record_number.value, 0)
        self.assertEqual(policy.password_expire_days.source.file, "policy.cfg")
        self.assertEqual(policy.password_expire_days.source.line, 3)

    def test_parse_access_user_scope_separately(self):
        cfg = parse_text(
            "aaa\n"
            " local-aaa-user password policy administrator\n"
            "  password history record number 5\n"
            "  quit\n"
            " local-aaa-user password policy access-user\n"
            "  password history record number 3\n"
            "  quit\n"
            "#\n"
        )

        self.assertEqual(len(cfg.local_aaa_password_policies), 2)
        by_scope = {p.scope.value: p for p in cfg.local_aaa_password_policies}
        self.assertEqual(by_scope["administrator"].password_history_record_number.value, 5)
        self.assertEqual(by_scope["access-user"].password_history_record_number.value, 3)

    def test_quit_restores_aaa_context_for_local_user(self):
        cfg = parse_text(
            "aaa\n"
            " local-aaa-user password policy administrator\n"
            "  password history record number 4\n"
            "  quit\n"
            " local-user ops service-type ssh\n"
            "#\n"
        )

        self.assertEqual(len(cfg.local_users), 1)
        self.assertEqual(cfg.local_users[0].name.value, "ops")
        self.assertEqual(cfg.unparsed_lines, [])

    def test_undo_parent_records_disabled_policy(self):
        cfg = parse_text(
            "aaa\n"
            " undo local-aaa-user password policy administrator\n"
            "#\n"
        )

        self.assertEqual(len(cfg.local_aaa_password_policies), 1)
        policy = cfg.local_aaa_password_policies[0]
        self.assertEqual(policy.scope.value, "administrator")
        self.assertFalse(policy.enabled.value)

    def test_to_dict_includes_password_policy_fields(self):
        cfg = parse_text(
            "aaa\n"
            " local-aaa-user password policy administrator\n"
            "  password expire 30\n"
            "  quit\n"
            "#\n"
        )

        data = cfg.to_dict()
        self.assertEqual(data["local_aaa_password_policies"][0]["scope"]["value"], "administrator")
        self.assertEqual(data["local_aaa_password_policies"][0]["password_expire_days"]["value"], 30)


class TestAaaPasswordPolicyFixture(unittest.TestCase):

    def test_fixture_parses_without_unparsed_lines(self):
        cfg = parse_file(FIXTURE)

        by_scope = {p.scope.value: p for p in cfg.local_aaa_password_policies}
        self.assertEqual(sorted(by_scope), ["access-user", "administrator"])
        self.assertEqual(by_scope["administrator"].password_expire_days.value, 0)
        self.assertEqual(by_scope["administrator"].password_alert_before_expire_days.value, 0)
        self.assertFalse(by_scope["administrator"].password_alert_original.value)
        self.assertEqual(by_scope["administrator"].password_history_record_number.value, 0)
        self.assertEqual(by_scope["access-user"].password_history_record_number.value, 3)
        self.assertEqual(cfg.local_users[0].service_types[0].value, "ssh")
        self.assertEqual(cfg.unparsed_lines, [])


if __name__ == "__main__":
    unittest.main()
