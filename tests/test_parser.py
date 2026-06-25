"""Tests for the v0.2 VRP parser, including SourceRef provenance assertions."""
import os
import tempfile
import unittest

from vrp_ir import parse_file, parse_text

SAMPLE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples", "sample-vrp.cfg")
SAMPLE_USG = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples", "sample-usg.cfg")


class TestParser(unittest.TestCase):
    def setUp(self):
        self.cfg = parse_file(SAMPLE)

    def test_header_and_hostname(self):
        self.assertEqual(self.cfg.software_version.value, "V800R012C10SPC300")
        self.assertEqual(self.cfg.hostname.value, "CORE-SW-01")  # tolerates leading space

    def test_parse_file_accepts_utf8_bom(self):
        path = self._write_temp_config("\ufeffsysname BOM-FW\n", encoding="utf-8")

        cfg = parse_file(path)

        self.assertEqual(cfg.hostname.value, "BOM-FW")

    def test_parse_file_accepts_gb18030_chinese_config(self):
        path = self._write_temp_config(
            "sysname 防火墙\n"
            "interface GigabitEthernet0/0/1\n"
            " description 上联核心\n"
            "#\n",
            encoding="gb18030",
        )

        cfg = parse_file(path)

        self.assertEqual(cfg.hostname.value, "防火墙")
        self.assertEqual(cfg.interfaces[0].description.value, "上联核心")
        self.assertIn("上联核心", cfg.interfaces[0].description.source.raw)

    def test_parse_text_tracks_unparsed_top_level_and_body_lines(self):
        cfg = parse_text(
            "sysname FW\n"
            "unknown-security-feature enable\n"
            "interface GigabitEthernet0/0/1\n"
            " unknown-interface-command value\n"
            "#\n",
            filename="unknown.cfg",
        )

        self.assertEqual(cfg.analyzed_line_count, 4)
        self.assertEqual([x.line for x in cfg.unparsed_lines], [2, 4])
        self.assertIn("unknown-security-feature", cfg.unparsed_lines[0].raw)
        self.assertIn("unknown-interface-command", cfg.unparsed_lines[1].raw)

    def test_to_dict_includes_parser_coverage_inputs(self):
        cfg = parse_text("sysname FW\nunknown-command enable\n")
        data = cfg.to_dict()

        self.assertEqual(data["analyzed_line_count"], 2)
        self.assertEqual(data["unparsed_lines"][0]["line"], 2)

    def _write_temp_config(self, text: str, encoding: str) -> str:
        fd, path = tempfile.mkstemp(suffix=".cfg")
        os.close(fd)
        self.addCleanup(lambda: os.path.exists(path) and os.remove(path))
        with open(path, "wb") as f:
            f.write(text.encode(encoding))
        return path

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

    def test_vpn_target_evpn_trailing_qualifier(self):
        # Direction keyword may be followed by an address-family qualifier
        # (EVPN); it must still set direction, and neither the keyword nor the
        # `evpn` qualifier may leak in as a fake route-target ("no garbage facts").
        cfg = parse_text(
            "ip vpn-instance E\n"
            " ipv4-family\n"
            "  vpn-target 1:1 export-extcommunity evpn\n"
            "  vpn-target 2:2 import-extcommunity evpn\n"
            "  vpn-target 3:3 both evpn\n")
        vrf = cfg.vrfs[0]
        self.assertEqual([t.value for t in vrf.export_targets], ["1:1", "3:3"])
        self.assertEqual([t.value for t in vrf.import_targets], ["2:2", "3:3"])
        leaked = {t.value for t in vrf.export_targets + vrf.import_targets}
        self.assertFalse(leaked & {"evpn", "export-extcommunity", "import-extcommunity", "both"})

    def test_sample_vrf_evpn_targets(self):
        evpn = next(v for v in self.cfg.vrfs if v.name.value == "EVPN1")
        self.assertEqual([t.value for t in evpn.export_targets], ["65000:400"])
        self.assertEqual([t.value for t in evpn.import_targets], ["65000:401"])


class TestFirewall(unittest.TestCase):
    """v0.3 USG firewall objects (zone / security-policy / nat server / hrp)."""

    def setUp(self):
        self.cfg = parse_file(SAMPLE_USG)

    def test_zones(self):
        z = {x.name.value: x for x in self.cfg.firewall_zones}
        self.assertEqual(set(z), {"trust", "untrust", "DMZ-WEB"})
        self.assertEqual(z["trust"].priority.value, 85)
        self.assertEqual([i.value for i in z["trust"].interfaces], ["GigabitEthernet0/0/1"])
        self.assertEqual(z["DMZ-WEB"].zone_id.value, 4)        # custom zone id
        self.assertEqual(z["DMZ-WEB"].priority.value, 50)
        self.assertIsNone(z["trust"].zone_id)                  # built-in zone has no id

    def test_security_rules_order_and_fields(self):
        rules = self.cfg.security_rules
        self.assertEqual([r.name.value for r in rules],
                         ["trust-to-dmz-web", "mgmt-ssh", "default-deny"])
        web = rules[0]
        self.assertEqual([t.value for t in web.source_zones], ["trust"])
        self.assertEqual([t.value for t in web.destination_zones], ["DMZ-WEB"])
        self.assertEqual([t.value for t in web.services], ["http", "https"])
        self.assertEqual([t.value for t in web.destination_addresses],
                         ["address-set web-servers"])   # opaque set reference kept
        self.assertEqual([t.value for t in web.profiles], ["av default"])
        self.assertEqual(web.action.value, "permit")

    def test_session_logging_and_default_deny(self):
        rules = {r.name.value: r for r in self.cfg.security_rules}
        self.assertTrue(rules["mgmt-ssh"].session_logging.value)
        self.assertIsNone(rules["trust-to-dmz-web"].session_logging)  # auditor seed
        deny = rules["default-deny"]
        self.assertEqual(deny.action.value, "deny")
        self.assertEqual(deny.source_zones, [])   # deny-all has no zone scoping

    def test_nat_server(self):
        n = self.cfg.nat_servers[0]
        self.assertEqual(n.name.value, "web-pub")
        self.assertEqual(n.zone.value, "untrust")
        self.assertEqual(n.protocol.value, "tcp")
        self.assertEqual(n.global_address.value, "203.0.113.10")
        self.assertEqual(n.global_port.value, "443")
        self.assertEqual(n.inside_address.value, "10.10.10.10")
        self.assertEqual(n.inside_port.value, "443")

    def test_nat_policy_rules_order_and_fields(self):
        rules = self.cfg.nat_policy_rules
        self.assertEqual([r.name.value for r in rules],
                         ["trust-web-out", "trust-to-dmz-no-nat"])
        snat = rules[0]
        self.assertEqual([t.value for t in snat.source_zones], ["trust"])
        self.assertEqual([t.value for t in snat.destination_zones], ["untrust"])
        self.assertEqual([t.value for t in snat.source_addresses], ["192.168.10.0 mask 24"])
        self.assertEqual([t.value for t in snat.destination_addresses], ["0.0.0.0 mask 0"])
        self.assertEqual([t.value for t in snat.services], ["any"])
        self.assertEqual(snat.action.value, "source-nat easy-ip")
        self.assertEqual(self.cfg.to_dict()["nat_policy_rules"][0]["action"]["value"],
                         "source-nat easy-ip")
        self.assertEqual(rules[1].action.value, "no-nat")

    def test_hrp(self):
        h = self.cfg.hrp
        self.assertTrue(h.enabled.value)
        self.assertEqual(h.heartbeat_interface.value, "GigabitEthernet0/0/7")
        self.assertEqual(h.peer.value, "10.255.255.2")
        self.assertIn("hrp mirror session enable", [d.value for d in h.directives])

    def test_usg_reuses_routing_engine(self):
        # USG is VRP same-origin: interfaces parse with the existing engine.
        by = {i.name.value: i for i in self.cfg.interfaces}
        self.assertEqual(by["GigabitEthernet0/0/2"].ipv4[0].prefix_length.value, 29)

    def test_firewall_sourceref_invariant(self):
        zone = next(z for z in self.cfg.firewall_zones if z.name.value == "DMZ-WEB")
        ref = zone.interfaces[0].source
        with open(SAMPLE_USG, encoding="utf-8") as f:
            lines = f.readlines()
        self.assertIn("GigabitEthernet0/0/3", lines[ref.line - 1])

    def test_builtin_zone_and_multi_zone_rule(self):
        cfg = parse_text(
            "firewall zone dmz\n"
            " set priority 50\n"
            "#\n"
            "security-policy\n"
            " rule name multi\n"
            "  source-zone trust\n"
            "  source-zone dmz\n"
            "  action permit\n"
            "#\n")
        self.assertEqual(cfg.firewall_zones[0].name.value, "dmz")
        self.assertIsNone(cfg.firewall_zones[0].zone_id)
        self.assertEqual([t.value for t in cfg.security_rules[0].source_zones],
                         ["trust", "dmz"])   # multiple zones OR-combined

    def test_security_policy_default_action(self):
        # Policy-level `default action permit` (= permit-any) must be captured —
        # even before any rule — and must not pollute a rule's own action.
        cfg = parse_text(
            "security-policy\n"
            " default action permit\n"
            " rule name r1\n"
            "  action deny\n"
            "#\n")
        self.assertEqual(cfg.security_default_action.value, "permit")
        self.assertEqual(cfg.security_rules[0].action.value, "deny")
        cfg2 = parse_text(            # hyphenated form, appearing after a rule
            "security-policy\n"
            " rule name r\n"
            "  action permit\n"
            " default-action deny\n"
            "#\n")
        self.assertEqual(cfg2.security_default_action.value, "deny")

    def test_nat_server_malformed_global_without_address(self):
        # `global` with no address must not borrow `inside`'s address as a port.
        cfg = parse_text("nat server x protocol tcp global inside 10.0.0.2 80\n")
        n = cfg.nat_servers[0]
        self.assertIsNone(n.global_address)
        self.assertIsNone(n.global_port)
        self.assertEqual(n.inside_address.value, "10.0.0.2")
        self.assertEqual(n.inside_port.value, "80")

    def test_nat_duplicate_port_distinct_cols(self):
        # global/inside share port 443; each col must point at its OWN occurrence.
        n = self.cfg.nat_servers[0]
        line = open(SAMPLE_USG, encoding="utf-8").readlines()[n.inside_port.source.line - 1]
        self.assertGreater(n.inside_port.source.col, n.global_port.source.col)
        self.assertEqual(line[n.inside_port.source.col:n.inside_port.source.col + 3], "443")

    def test_nat_policy_sourceref_lines(self):
        rules = {r.name.value: r for r in self.cfg.nat_policy_rules}
        snat = rules["trust-web-out"]
        no_nat = rules["trust-to-dmz-no-nat"]
        with open(SAMPLE_USG, encoding="utf-8") as f:
            lines = f.readlines()
        self.assertEqual(snat.action.source.line, 59)
        self.assertIn("action source-nat easy-ip", lines[snat.action.source.line - 1])
        self.assertEqual(snat.action.source.col, lines[snat.action.source.line - 1].index("source-nat easy-ip"))
        self.assertEqual(no_nat.destination_addresses[0].source.line, 64)
        self.assertIn("10.10.10.0 mask 24",
                      lines[no_nat.destination_addresses[0].source.line - 1])


if __name__ == "__main__":
    unittest.main()
