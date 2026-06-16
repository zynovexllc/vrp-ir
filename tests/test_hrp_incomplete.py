"""Tests for FW-HRP-INCOMPLETE acceptance check (issue #15)."""
import unittest

from vrp_ir import parse_text, run_checks


def _findings(text):
    return [f for f in run_checks(parse_text(text)).findings
            if f.check_id == "FW-HRP-INCOMPLETE"]


class TestHrpIncomplete(unittest.TestCase):

    def test_hrp_enabled_no_interface_yields_one_warn(self):
        """HRP enabled but no heartbeat interface → exactly one FW-HRP-INCOMPLETE warn."""
        cfg_text = "hrp enable\n#\n"
        fs = _findings(cfg_text)
        self.assertEqual(len(fs), 1)
        self.assertEqual(fs[0].status, "warn")
        self.assertEqual(fs[0].severity, "medium")

    def test_hrp_enabled_no_peer_yields_one_warn(self):
        """HRP enabled but no remote peer → exactly one FW-HRP-INCOMPLETE warn."""
        cfg_text = "hrp enable\nhrp interface GigabitEthernet0/0/0\n#\n"
        fs = _findings(cfg_text)
        self.assertEqual(len(fs), 1)
        self.assertEqual(fs[0].status, "warn")

    def test_hrp_enabled_no_interface_no_peer_yields_one_warn(self):
        """HRP enabled but neither interface nor peer → exactly one finding."""
        cfg_text = "hrp enable\n#\n"
        fs = _findings(cfg_text)
        self.assertEqual(len(fs), 1)

    def test_hrp_enabled_and_complete_yields_no_finding(self):
        """Complete HRP (interface + peer on same line) → no FW-HRP-INCOMPLETE finding."""
        cfg_text = (
            "hrp enable\n"
            "hrp interface GigabitEthernet0/0/2 remote 10.0.0.2\n"
            "#\n"
        )
        fs = _findings(cfg_text)
        self.assertEqual(fs, [])

    def test_hrp_absent_yields_no_finding(self):
        """No HRP configuration → no FW-HRP-INCOMPLETE finding."""
        fs = _findings("")
        self.assertEqual(fs, [])

    def test_hrp_disabled_yields_no_finding(self):
        """HRP configured but not enabled → no FW-HRP-INCOMPLETE finding."""
        cfg_text = "hrp interface GigabitEthernet0/0/2\n#\n"
        fs = _findings(cfg_text)
        self.assertEqual(fs, [])

    def test_incomplete_hrp_finding_cites_hrp_source(self):
        """Evidence must cite the hrp source line."""
        cfg_text = "hrp enable\n#\n"
        fs = _findings(cfg_text)
        self.assertEqual(len(fs), 1)
        self.assertTrue(len(fs[0].evidence) >= 1)


if __name__ == "__main__":
    unittest.main()
