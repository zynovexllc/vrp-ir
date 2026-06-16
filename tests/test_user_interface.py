"""Tests for user-interface con/vty block parsing (issue #22 / v0.6)."""
import unittest

from vrp_ir.parser import parse_text


VTY_CONFIG = """\
user-interface vty 0 4
 protocol inbound telnet
 acl 2000 inbound
 authentication-mode aaa
 user privilege level 15
#
"""

CON_CONFIG = """\
user-interface con 0
 authentication-mode password
#
"""

MULTI_PROTOCOL_CONFIG = """\
user-interface vty 0 4
 protocol inbound ssh
 protocol inbound telnet
#
"""


class TestUserInterfaceVtyParsing(unittest.TestCase):

    def setUp(self):
        self.cfg = parse_text(VTY_CONFIG)
        self.assertGreater(len(self.cfg.user_interfaces), 0)
        self.ui = self.cfg.user_interfaces[0]

    def test_kind_is_vty(self):
        self.assertEqual(self.ui.kind.value, "vty")

    def test_first_is_0(self):
        self.assertEqual(self.ui.first.value, 0)

    def test_last_is_4(self):
        self.assertIsNotNone(self.ui.last)
        self.assertEqual(self.ui.last.value, 4)

    def test_protocol_inbound_contains_telnet(self):
        values = [t.value for t in self.ui.protocol_inbound]
        self.assertIn("telnet", values)

    def test_acl_inbound_is_2000(self):
        self.assertIsNotNone(self.ui.acl_inbound)
        self.assertEqual(self.ui.acl_inbound.value, "2000")

    def test_authentication_mode_is_aaa(self):
        self.assertIsNotNone(self.ui.authentication_mode)
        self.assertEqual(self.ui.authentication_mode.value, "aaa")

    def test_privilege_level_is_15(self):
        self.assertIsNotNone(self.ui.privilege_level)
        self.assertEqual(self.ui.privilege_level.value, 15)

    def test_kind_sourceref_line(self):
        self.assertEqual(self.ui.kind.source.line, 1)

    def test_protocol_inbound_sourceref_line(self):
        self.assertEqual(self.ui.protocol_inbound[0].source.line, 2)

    def test_acl_inbound_sourceref_line(self):
        self.assertEqual(self.ui.acl_inbound.source.line, 3)

    def test_authentication_mode_sourceref_line(self):
        self.assertEqual(self.ui.authentication_mode.source.line, 4)

    def test_privilege_level_sourceref_line(self):
        self.assertEqual(self.ui.privilege_level.source.line, 5)

    def test_acl_inbound_sourceref_raw(self):
        self.assertIn("acl 2000 inbound", self.ui.acl_inbound.source.raw)

    def test_authentication_mode_sourceref_raw(self):
        self.assertIn("authentication-mode aaa", self.ui.authentication_mode.source.raw)

    def test_privilege_level_sourceref_raw(self):
        self.assertIn("user privilege level 15", self.ui.privilege_level.source.raw)


class TestUserInterfaceConParsing(unittest.TestCase):

    def setUp(self):
        self.cfg = parse_text(CON_CONFIG)
        self.assertGreater(len(self.cfg.user_interfaces), 0)
        self.ui = self.cfg.user_interfaces[0]

    def test_kind_is_con(self):
        self.assertEqual(self.ui.kind.value, "con")

    def test_first_is_0(self):
        self.assertEqual(self.ui.first.value, 0)

    def test_last_is_none(self):
        self.assertIsNone(self.ui.last)

    def test_authentication_mode_is_password(self):
        self.assertIsNotNone(self.ui.authentication_mode)
        self.assertEqual(self.ui.authentication_mode.value, "password")


class TestUserInterfaceMultiProtocol(unittest.TestCase):

    def setUp(self):
        self.cfg = parse_text(MULTI_PROTOCOL_CONFIG)
        self.ui = self.cfg.user_interfaces[0]

    def test_both_protocols_collected(self):
        values = [t.value for t in self.ui.protocol_inbound]
        self.assertIn("ssh", values)
        self.assertIn("telnet", values)
        self.assertEqual(len(values), 2)


class TestUserInterfaceEmptyConfig(unittest.TestCase):

    def test_no_user_interface_block_yields_empty_list(self):
        cfg = parse_text("sysname fw1\n")
        self.assertEqual(cfg.user_interfaces, [])

    def test_existing_parse_unaffected(self):
        cfg = parse_text("sysname fw1\ninterface GigabitEthernet0/0/0\n ip address 10.0.0.1 255.255.255.0\n#\n")
        self.assertEqual(cfg.user_interfaces, [])
        self.assertEqual(len(cfg.interfaces), 1)


if __name__ == "__main__":
    unittest.main()
