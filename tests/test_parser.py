"""Tests for the v0.2 VRP parser, including SourceRef provenance assertions."""
import os
import unittest

from vrp_ir import parse_file, parse_text

SAMPLE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples", "sample-vrp.cfg")


class TestParser(unittest.TestCase):
    def setUp(self):
        self.cfg = parse_file(SAMPLE)

    def test_header_and_hostname(self):
        self.assertEqual(self.cfg.software_version.value, "V800R012C10SPC300")
        self.assertEqual(self.cfg.hostname.value, "CORE-SW-01")  # tolerates leading space

    def test_vlan_batches_with_range(self):
        spans = [(r.start, r.end) for r in self.cfg.vlan_batches]
        self.assertIn((1000, 1002), spans)
        self.assertIn((10, 10), spans)

    def test_vlan_blocks(self):
        v = {x.vlan_id.value: (x.description.value if x.description else None)
             for x in self.cfg.vlans}
        self.assertEqual(v[10], "MGMT-VLAN")

    def test_vrf_rd_rt(self):
        vrf = self.cfg.vrfs[0]
        self.assertEqual(vrf.name.value, "OFFICE")
        self.assertEqual(vrf.route_distinguisher.value, "65000:100")
        self.assertEqual([t.value for t in vrf.export_targets], ["65000:100"])
        self.assertEqual([t.value for t in vrf.import_targets], ["65000:100"])

    def test_acl_rules(self):
        acl = self.cfg.acls[0]
        self.assertEqual(acl.identifier.value, "3000")
        self.assertEqual([r.action.value for r in acl.rules], ["deny", "permit"])

    def test_static_routes(self):
        routes = self.cfg.static_routes
        self.assertEqual(routes[0].destination.value, "0.0.0.0")
        self.assertEqual(routes[1].preference.value, 60)
        self.assertEqual(routes[2].vpn_instance.value, "OFFICE")

    def test_interface_basics(self):
        by = {i.name.value: i for i in self.cfg.interfaces}
        self.assertEqual(by["Eth-Trunk1"].link_type.value, "trunk")
        self.assertIn((1000, 1002), [(r.start, r.end) for r in by["Eth-Trunk1"].trunk_vlans])
        self.assertEqual(by["GigabitEthernet0/0/1"].eth_trunk.value, 1)
        self.assertEqual(by["Eth-Trunk1.100"].dot1q_vlan.value, 100)
        self.assertTrue(by["GigabitEthernet0/0/3"].shutdown.value)

    def test_secondary_and_mask_normalisation(self):
        ge2 = next(i for i in self.cfg.interfaces if i.name.value == "GigabitEthernet0/0/2")
        self.assertEqual(ge2.vpn_instance.value, "OFFICE")
        self.assertEqual(ge2.default_vlan.value, 20)
        self.assertEqual(ge2.ipv4[0].prefix_length.value, 24)       # dotted mask -> 24
        self.assertTrue(ge2.ipv4[1].is_secondary)                   # `sub`
        vlanif = next(i for i in self.cfg.interfaces if i.name.value == "Vlanif10")
        self.assertEqual(vlanif.ipv4[0].prefix_length.value, 24)    # prefix form
        lo = next(i for i in self.cfg.interfaces if i.name.value == "LoopBack0")
        self.assertEqual(lo.ipv4[0].prefix_length.value, 32)

    def test_sourceref_invariant(self):
        # Every traced value must point to a line that actually contains it.
        ge2 = next(i for i in self.cfg.interfaces if i.name.value == "GigabitEthernet0/0/2")
        ref = ge2.ipv4[0].address.source
        with open(SAMPLE, encoding="utf-8") as f:
            lines = f.readlines()
        self.assertIn("192.168.20.254", lines[ref.line - 1])

    def test_to_dict_omits_none_keeps_sources(self):
        d = self.cfg.to_dict()
        self.assertIn("source", d["interfaces"][0])
        self.assertIn("software_version", d)

    def test_invalid_mask_ignored(self):
        cfg = parse_text("interface GE0/0/9\n ip address 10.0.0.1 999.0.0.0\n#\n")
        self.assertEqual(cfg.interfaces[0].ipv4, [])

    def test_vpn_target_directions_and_multi(self):
        # `both` and a bare vpn-target (VRP default == both) must populate BOTH
        # import and export; a single line may carry several route-targets.
        cfg = parse_text(
            "ip vpn-instance V\n"
            " ipv4-family\n"
            "  vpn-target 1:1 both\n"
            "  vpn-target 2:2\n"
            "  vpn-target 3:3 4:4 export-extcommunity\n"
            "  vpn-target 5:5 import-extcommunity\n")
        vrf = cfg.vrfs[0]
        self.assertEqual([t.value for t in vrf.export_targets],
                         ["1:1", "2:2", "3:3", "4:4"])
        self.assertEqual([t.value for t in vrf.import_targets],
                         ["1:1", "2:2", "5:5"])
        rt44 = next(t for t in vrf.export_targets if t.value == "4:4")
        self.assertIn("4:4", rt44.source.raw)  # provenance survives multi-RT

    def test_blank_line_does_not_truncate_block(self):
        # A blank line inside a block must not silently drop the rest of it.
        cfg = parse_text(
            "interface GE0/0/5\n"
            " description X\n"
            "\n"
            " ip address 1.2.3.4 24\n"
            "#\n")
        itf = cfg.interfaces[0]
        self.assertEqual(itf.description.value, "X")
        self.assertEqual(itf.ipv4[0].address.value, "1.2.3.4")
        self.assertEqual(itf.ipv4[0].prefix_length.value, 24)

    def test_sample_vrf_shared_multi_rt_both(self):
        # The de-friendlied sample now guards the vpn-target fixes directly.
        shared = next(v for v in self.cfg.vrfs if v.name.value == "SHARED")
        self.assertEqual([t.value for t in shared.export_targets],
                         ["65000:200", "65000:201", "65000:300"])
        self.assertEqual([t.value for t in shared.import_targets],
                         ["65000:200", "65000:201", "65000:300", "65000:999"])


if __name__ == "__main__":
    unittest.main()
