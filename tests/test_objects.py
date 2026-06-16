"""Tests for v0.4.x named object parsing (ip address-set / ip service-set).

Kept in a dedicated file so the suite grows without touching existing tests.
"""
import os
import unittest

from vrp_ir import parse_file, parse_text

SAMPLE_USG = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples", "sample-usg.cfg")


class TestObjectSets(unittest.TestCase):
    def setUp(self):
        self.cfg = parse_file(SAMPLE_USG)

    def test_address_set_object_from_sample(self):
        sets = {a.name.value: a for a in self.cfg.address_sets}
        self.assertIn("web-servers", sets)
        ws = sets["web-servers"]
        self.assertEqual(ws.set_type.value, "object")
        self.assertEqual(len(ws.members), 1)
        m = ws.members[0]
        self.assertEqual(m.address.value, "10.10.10.10")
        self.assertEqual(m.prefix_length.value, 32)

    def test_address_set_group_appended(self):
        sets = {a.name.value: a for a in self.cfg.address_sets}
        self.assertIn("mgmt-hosts", sets)
        g = sets["mgmt-hosts"]
        self.assertEqual(g.set_type.value, "group")
        self.assertEqual([m.address.value for m in g.members], ["10.0.0.0", "192.168.1.1"])
        self.assertEqual([m.prefix_length.value for m in g.members], [24, 32])

    def test_service_set_from_sample(self):
        sets = {s.name.value: s for s in self.cfg.service_sets}
        self.assertIn("web-svc", sets)
        svc = sets["web-svc"]
        self.assertEqual(svc.set_type.value, "object")
        self.assertEqual([i.seq.value for i in svc.items], ["0", "1"])
        self.assertIn("destination-port 443", svc.items[0].expression.value)

    def test_address_set_sourceref_invariant(self):
        a = next(x for x in self.cfg.address_sets if x.name.value == "web-servers")
        m = a.members[0]
        with open(SAMPLE_USG, encoding="utf-8") as f:
            lines = f.readlines()
        self.assertIn("10.10.10.10", lines[m.address.source.line - 1])
        self.assertIn("web-servers", lines[a.name.source.line - 1])

    def test_address_set_range_expression_preserved(self):
        # A range member (no `mask`) keeps the full expression; no garbage mask.
        cfg = parse_text(
            "ip address-set pool type group\n"
            " address 0 10.0.0.1 10.0.0.9\n"
            "#\n")
        m = cfg.address_sets[0].members[0]
        self.assertEqual(m.address.value, "10.0.0.1")
        self.assertIsNone(m.prefix_length)
        self.assertEqual(m.expression.value, "10.0.0.1 10.0.0.9")

    def test_to_dict_includes_object_sets(self):
        d = self.cfg.to_dict()
        self.assertIn("address_sets", d)
        self.assertIn("service_sets", d)
        self.assertEqual(d["address_sets"][0]["name"]["value"], "web-servers")
        self.assertIn("source", d["address_sets"][0])


if __name__ == "__main__":
    unittest.main()
