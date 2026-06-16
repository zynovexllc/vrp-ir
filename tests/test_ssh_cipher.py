"""Tests for 'ssh server cipher' parsing and FW-SSH-WEAK-CIPHER acceptance check."""
import unittest

from vrp_ir.parser import parse_text
from vrp_ir.acceptance import run_checks


class TestSshServerCipherParsing(unittest.TestCase):
    """Parser: 'ssh server cipher' line -> ssh_server_ciphers."""

    def test_three_ciphers_parsed(self):
        cfg = parse_text("ssh server cipher aes256_ctr 3des_cbc aes128_cbc\n")
        self.assertEqual(len(cfg.ssh_server_ciphers), 3)
        self.assertEqual([t.value for t in cfg.ssh_server_ciphers],
                         ["aes256_ctr", "3des_cbc", "aes128_cbc"])

    def test_source_refs_line_number(self):
        cfg = parse_text("sysname FW\nssh server cipher aes256_ctr 3des_cbc aes128_cbc\n")
        for t in cfg.ssh_server_ciphers:
            self.assertEqual(t.source.line, 2)

    def test_source_refs_columns_advancing(self):
        line = "ssh server cipher aes256_ctr 3des_cbc aes128_cbc"
        cfg = parse_text(line)
        cols = [t.source.col for t in cfg.ssh_server_ciphers]
        # Each token must start after the previous one
        self.assertEqual(cols[0], line.index("aes256_ctr"))
        self.assertEqual(cols[1], line.index("3des_cbc"))
        self.assertEqual(cols[2], line.index("aes128_cbc"))
        # Columns are strictly increasing
        self.assertLess(cols[0], cols[1])
        self.assertLess(cols[1], cols[2])

    def test_strong_ciphers_only(self):
        cfg = parse_text("ssh server cipher aes256_ctr aes256_gcm\n")
        self.assertEqual(len(cfg.ssh_server_ciphers), 2)
        self.assertEqual([t.value for t in cfg.ssh_server_ciphers],
                         ["aes256_ctr", "aes256_gcm"])

    def test_no_ssh_cipher_line(self):
        cfg = parse_text("sysname FW\ntelnet server enable\n")
        self.assertEqual(cfg.ssh_server_ciphers, [])

    def test_other_ssh_lines_not_consumed(self):
        # 'ssh server authentication-type ...' must NOT be captured as ciphers
        cfg = parse_text("ssh server authentication-type password\n")
        self.assertEqual(cfg.ssh_server_ciphers, [])

    def test_source_ref_raw_stored(self):
        line = "ssh server cipher aes256_ctr 3des_cbc"
        cfg = parse_text(line)
        for t in cfg.ssh_server_ciphers:
            self.assertEqual(t.source.raw, line)


class TestFwSshWeakCipherCheck(unittest.TestCase):
    """Acceptance check FW-SSH-WEAK-CIPHER."""

    def _findings(self, text):
        cfg = parse_text(text)
        report = run_checks(cfg)
        return [f for f in report.findings if f.check_id == "FW-SSH-WEAK-CIPHER"]

    def test_weak_ciphers_yield_one_warn(self):
        findings = self._findings(
            "ssh server cipher aes256_ctr 3des_cbc aes128_cbc\n")
        self.assertEqual(len(findings), 1)
        f = findings[0]
        self.assertEqual(f.status, "warn")
        self.assertEqual(f.severity, "medium")
        self.assertIn("3des_cbc", f.detail)
        self.assertIn("aes128_cbc", f.detail)
        self.assertNotIn("aes256_ctr", f.detail)

    def test_weak_ciphers_evidence_refs_point_to_weak_tokens(self):
        line = "ssh server cipher aes256_ctr 3des_cbc aes128_cbc"
        findings = self._findings(line)
        self.assertEqual(len(findings), 1)
        evidence_cols = [e.col for e in findings[0].evidence]
        self.assertIn(line.index("3des_cbc"), evidence_cols)
        self.assertIn(line.index("aes128_cbc"), evidence_cols)
        # strong cipher must NOT appear in evidence
        self.assertNotIn(line.index("aes256_ctr"), evidence_cols)

    def test_all_strong_ciphers_no_finding(self):
        findings = self._findings(
            "ssh server cipher aes256_ctr aes256_gcm\n")
        self.assertEqual(findings, [])

    def test_no_ssh_cipher_line_no_finding(self):
        findings = self._findings("sysname FW\n")
        self.assertEqual(findings, [])

    def test_cbc_substring_detected(self):
        findings = self._findings("ssh server cipher aes128_cbc\n")
        self.assertEqual(len(findings), 1)
        self.assertIn("aes128_cbc", findings[0].detail)

    def test_3des_prefix_detected(self):
        findings = self._findings("ssh server cipher 3des_cbc\n")
        self.assertEqual(len(findings), 1)
        self.assertIn("3des_cbc", findings[0].detail)

    def test_des_exact_detected(self):
        findings = self._findings("ssh server cipher des\n")
        self.assertEqual(len(findings), 1)
        self.assertIn("des", findings[0].detail)

    def test_check_id_registered(self):
        from vrp_ir.acceptance import CHECKS_META
        self.assertIn("FW-SSH-WEAK-CIPHER", CHECKS_META)


if __name__ == "__main__":
    unittest.main()
