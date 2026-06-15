"""Tests for the v0.1 VRP parser, including SourceRef provenance assertions."""
import os
import unittest

from vrp_ir import parse_file, parse_text

SAMPLE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples", "sample-vrp.cfg")


class TestParser(unittest.TestCase):
    def setUp(self):
        self.cfg = parse_file(SAMPLE)

    def test_hostname(self):
        self.assertIsNotNone(self.cfg.hostname)
        self.assertEqual(self.cfg.hostname.value, "CORE-FW-01")

    def test_interface_count(self):
        names = [i.name.value for i in self.cfg.interfaces]
        self.assertEqual(
            names,
            ["GigabitEthernet0/0/1", "GigabitEthernet0/0/2",
             "GigabitEthernet0/0/3", "LoopBack0"])

    def test_ip_and_prefix(self):
        ge2 = self.cfg.interfaces[1]
        self.assertEqual(ge2.ipv4[0].address.value, "192.168.20.254")
        self.assertEqual(ge2.ipv4[0].prefix_length.value, 24)
        ge1 = self.cfg.interfaces[0]
        # dotted mask 255.255.255.0 must normalise to /24
        self.assertEqual(ge1.ipv4[0].prefix_length.value, 24)

    def test_description_vrf_vlan_shutdown(self):
        ge2 = self.cfg.interfaces[1]
        self.assertEqual(ge2.description.value, "Office-Segment")
        self.assertEqual(ge2.vpn_instance.value, "OFFICE")
        self.assertEqual(ge2.access_vlan.value, 20)
        ge3 = self.cfg.interfaces[2]
        self.assertTrue(ge3.shutdown.value)

    def test_sourceref_points_to_correct_line(self):
        # The differentiator: every value traces back to its exact source line.
        ge1 = self.cfg.interfaces[0]
        ref = ge1.ipv4[0].address.source
        self.assertEqual(ref.file, SAMPLE)
        # Read the raw file and confirm the referenced line really holds the value.
        with open(SAMPLE, encoding="utf-8") as f:
            lines = f.readlines()
        self.assertIn("10.10.10.1", lines[ref.line - 1])

    def test_loopback_32(self):
        lo = self.cfg.interfaces[3]
        self.assertEqual(lo.ipv4[0].prefix_length.value, 32)

    def test_to_dict_roundtrip_has_sources(self):
        d = self.cfg.to_dict()
        itf0 = d["interfaces"][0]
        self.assertIn("source", itf0)
        self.assertIn("line", itf0["source"])

    def test_invalid_mask_ignored(self):
        cfg = parse_text(
            "interface GE0/0/9\n ip address 10.0.0.1 999.0.0.0\n#\n")
        self.assertEqual(cfg.interfaces[0].ipv4, [])


if __name__ == "__main__":
    unittest.main()
