"""Tests for NTP unicast-server parsing."""
import os
import unittest

from vrp_ir import NtpServer, parse_file
from vrp_ir.parser import parse_text


SAMPLE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "examples", "sample-vrp.cfg")


class TestNtpServerParsing(unittest.TestCase):

    def test_ntp_service_unicast_server_parses_address(self):
        cfg = parse_text("ntp-service unicast-server 10.0.0.1\n")

        self.assertEqual(len(cfg.ntp_servers), 1)
        self.assertIsInstance(cfg.ntp_servers[0], NtpServer)
        self.assertEqual(cfg.ntp_servers[0].address.value, "10.0.0.1")

    def test_ntp_service_unicast_server_parses_vpn_instance(self):
        cfg = parse_text("ntp-service unicast-server 10.0.0.2 vpn-instance MGMT\n")
        server = cfg.ntp_servers[0]

        self.assertEqual(server.address.value, "10.0.0.2")
        self.assertIsNotNone(server.vpn_instance)
        self.assertEqual(server.vpn_instance.value, "MGMT")

    def test_older_ntp_unicast_server_variant_parses(self):
        cfg = parse_text("ntp unicast-server 192.168.1.1\n")

        self.assertEqual([s.address.value for s in cfg.ntp_servers], ["192.168.1.1"])

    def test_source_refs_capture_line_and_columns(self):
        line = " ntp-service unicast-server 10.0.0.2 vpn-instance MGMT"
        cfg = parse_text("sysname FW\n" + line + "\n", filename="ntp.cfg")
        server = cfg.ntp_servers[0]

        self.assertEqual(server.address.source.file, "ntp.cfg")
        self.assertEqual(server.address.source.line, 2)
        self.assertEqual(server.address.source.col, line.index("10.0.0.2"))
        self.assertEqual(server.address.source.raw, line)
        self.assertEqual(server.vpn_instance.source.line, 2)
        self.assertEqual(server.vpn_instance.source.col, line.index("MGMT"))

    def test_to_dict_keeps_ntp_sources(self):
        cfg = parse_text("ntp unicast-server 192.168.1.1\n")
        data = cfg.to_dict()

        self.assertEqual(data["ntp_servers"][0]["address"]["value"], "192.168.1.1")
        self.assertEqual(data["ntp_servers"][0]["address"]["source"]["line"], 1)

    def test_sample_config_contains_both_supported_forms(self):
        cfg = parse_file(SAMPLE)

        self.assertEqual([s.address.value for s in cfg.ntp_servers],
                         ["10.0.0.1", "192.168.1.1"])
        self.assertEqual(cfg.ntp_servers[0].vpn_instance.value, "MGMT")

        with open(SAMPLE, encoding="utf-8") as f:
            lines = f.readlines()
        for server in cfg.ntp_servers:
            self.assertIn(server.address.value, lines[server.address.source.line - 1])


if __name__ == "__main__":
    unittest.main()
