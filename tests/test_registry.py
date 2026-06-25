"""Tests for the check registry."""
import os
import unittest

from vrp_ir import CheckSpec, parse_file, registry, run_checks
from vrp_ir.acceptance import CHECKS, CHECKS_META, CHECK_REFERENCES

RISKY = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                     "examples", "sample-usg-risky.cfg")


class TestRegistry(unittest.TestCase):

    def test_registry_entries_are_checkspecs(self):
        for spec in registry():
            self.assertIsInstance(spec, CheckSpec)

    def test_registry_functions_match_checks(self):
        self.assertEqual([s.fn for s in registry()], CHECKS)

    def test_each_spec_metadata_matches_catalogue(self):
        for spec in registry():
            self.assertEqual(spec.intent, CHECKS_META[spec.check_id])
            self.assertEqual(spec.references, list(CHECK_REFERENCES.get(spec.check_id, [])))

    def test_run_order_preserved(self):
        ids = [s.check_id for s in registry()]
        self.assertEqual(ids[0], "FW-DEFAULT-DENY")
        self.assertEqual(ids[-1], "FW-NTP-MISSING")
        self.assertIn("FW-SNMP-V3", ids)

    def test_behaviour_unchanged(self):
        # The registry-driven run must still produce the established result.
        report = run_checks(parse_file(RISKY))
        self.assertEqual(report.result, "fail")


if __name__ == "__main__":
    unittest.main()
