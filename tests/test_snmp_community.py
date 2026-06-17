"""Tests for snmp-agent community parsing."""
import os
import unittest

from vrp_ir import SnmpCommunity, parse_file
from vrp_ir.parser import parse_text


SAMPLE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "examples", "sample-vrp.cfg")


class TestSnmpCommunityParsing(unittest.TestCase):

    def test_read_community_parses_plain_value(self):
        cfg = parse_text("snmp-agent community read public\n")

        self.assertEqual(len(cfg.snmp_communities), 1)
        community = cfg.snmp_communities[0]
        self.assertIsInstance(community, SnmpCommunity)
        self.assertEqual(community.access_mode.value, "read")
        self.assertEqual(community.community.value, "public")
        self.assertIsNone(community.encrypted)

    def test_write_community_parses_plain_value(self):
        cfg = parse_text("snmp-agent community write MyRwCommunity\n")

        community = cfg.snmp_communities[0]
        self.assertEqual(community.access_mode.value, "write")
        self.assertEqual(community.community.value, "MyRwCommunity")

    def test_cipher_community_tracks_encrypted_fact(self):
        cfg = parse_text("snmp-agent community write cipher %^%#secret%^%#\n")

        community = cfg.snmp_communities[0]
        self.assertEqual(community.access_mode.value, "write")
        self.assertIsNone(community.community)
        self.assertIsNotNone(community.encrypted)
        self.assertTrue(community.encrypted.value)

    def test_source_refs_capture_line_and_columns(self):
        line = " snmp-agent community read public"
        cfg = parse_text("sysname FW\n" + line + "\n", filename="snmp.cfg")
        community = cfg.snmp_communities[0]

        self.assertEqual(community.access_mode.source.file, "snmp.cfg")
        self.assertEqual(community.access_mode.source.line, 2)
        self.assertEqual(community.access_mode.source.col, line.index("read"))
        self.assertEqual(community.access_mode.source.raw, line)
        self.assertEqual(community.community.source.line, 2)
        self.assertEqual(community.community.source.col, line.index("public"))

    def test_cipher_source_ref_points_to_cipher_token(self):
        line = "snmp-agent community write cipher %^%#secret%^%#"
        cfg = parse_text(line + "\n", filename="snmp.cfg")
        community = cfg.snmp_communities[0]

        self.assertEqual(community.encrypted.source.line, 1)
        self.assertEqual(community.encrypted.source.col, line.index("cipher"))

    def test_to_dict_keeps_snmp_sources(self):
        cfg = parse_text("snmp-agent community read public\n")
        data = cfg.to_dict()

        self.assertEqual(data["snmp_communities"][0]["access_mode"]["value"], "read")
        self.assertEqual(data["snmp_communities"][0]["community"]["value"], "public")
        self.assertEqual(data["snmp_communities"][0]["community"]["source"]["line"], 1)

    def test_invalid_or_incomplete_lines_are_skipped(self):
        cfg = parse_text(
            "snmp-agent community public\n"
            "snmp-agent community read\n"
            "snmp-agent community admin public\n"
        )

        self.assertEqual(cfg.snmp_communities, [])

    def test_sample_config_contains_snmp_community(self):
        cfg = parse_file(SAMPLE)

        self.assertEqual([c.access_mode.value for c in cfg.snmp_communities], ["read"])
        self.assertEqual([c.community.value for c in cfg.snmp_communities], ["public"])

        with open(SAMPLE, encoding="utf-8") as f:
            lines = f.readlines()
        community = cfg.snmp_communities[0]
        self.assertIn(community.community.value, lines[community.community.source.line - 1])


if __name__ == "__main__":
    unittest.main()
