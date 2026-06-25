"""Tests for info-center loghost parsing."""
import os
import unittest

from vrp_ir import LogHost, parse_file
from vrp_ir.parser import parse_text


SAMPLE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "examples", "sample-vrp.cfg")


class TestInfoCenterLoghostParsing(unittest.TestCase):

    def test_loghost_parses_address(self):
        cfg = parse_text("info-center loghost 10.0.0.10\n")

        self.assertEqual(len(cfg.log_hosts), 1)
        self.assertIsInstance(cfg.log_hosts[0], LogHost)
        self.assertEqual(cfg.log_hosts[0].address.value, "10.0.0.10")

    def test_loghost_parses_vpn_instance(self):
        cfg = parse_text("info-center loghost 10.0.0.10 vpn-instance MGMT\n")
        host = cfg.log_hosts[0]

        self.assertEqual(host.address.value, "10.0.0.10")
        self.assertIsNotNone(host.vpn_instance)
        self.assertEqual(host.vpn_instance.value, "MGMT")

    def test_trailing_facility_option_is_ignored(self):
        cfg = parse_text("info-center loghost 10.0.0.11 facility local5\n")
        host = cfg.log_hosts[0]

        self.assertEqual(host.address.value, "10.0.0.11")
        self.assertIsNone(host.vpn_instance)

    def test_source_refs_capture_line_and_columns(self):
        line = " info-center loghost 10.0.0.10 vpn-instance MGMT"
        cfg = parse_text("sysname FW\n" + line + "\n", filename="loghost.cfg")
        host = cfg.log_hosts[0]

        self.assertEqual(host.address.source.file, "loghost.cfg")
        self.assertEqual(host.address.source.line, 2)
        self.assertEqual(host.address.source.col, line.index("10.0.0.10"))
        self.assertEqual(host.address.source.raw, line)
        self.assertEqual(host.vpn_instance.source.line, 2)
        self.assertEqual(host.vpn_instance.source.col, line.index("MGMT"))

    def test_to_dict_keeps_loghost_sources(self):
        cfg = parse_text("info-center loghost 192.0.2.10\n")
        data = cfg.to_dict()

        self.assertEqual(data["log_hosts"][0]["address"]["value"], "192.0.2.10")
        self.assertEqual(data["log_hosts"][0]["address"]["source"]["line"], 1)

    def test_incomplete_loghost_line_is_skipped_cleanly(self):
        cfg = parse_text("info-center loghost\n")

        self.assertEqual(cfg.log_hosts, [])

    def test_sample_config_contains_loghosts(self):
        cfg = parse_file(SAMPLE)

        self.assertEqual([h.address.value for h in cfg.log_hosts],
                         ["10.0.0.10", "10.0.0.11"])
        self.assertEqual(cfg.log_hosts[0].vpn_instance.value, "MGMT")

        with open(SAMPLE, encoding="utf-8") as f:
            lines = f.readlines()
        for host in cfg.log_hosts:
            self.assertIn(host.address.value, lines[host.address.source.line - 1])


if __name__ == "__main__":
    unittest.main()
