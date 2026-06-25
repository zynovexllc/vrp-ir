"""Golden corpus regression + zero-false-negative gate.

Each `tests/fixtures/<name>.cfg` with a sibling `<name>.expected.json` is a
curated golden case. The expected file is **hand-authored ground truth**:

- `result`: the overall audit result the corpus must keep producing.
- `min_parser_coverage`: parser coverage must not drop below this.
- `must_flag`: high-signal findings (check_id + severity) that **must** be
  surfaced. A future change that stops flagging any of these is a caught
  **false negative** — the whole point of this gate.

Add a real, de-identified config later by dropping in a `.cfg` plus a
hand-authored `.expected.json`; see `docs/de-identifying-configs.md`.
"""
import glob
import json
import os
import unittest

from vrp_ir import parse_file, run_checks

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def _cases():
    for cfg in sorted(glob.glob(os.path.join(FIXTURE_DIR, "*.cfg"))):
        expected = cfg[:-len(".cfg")] + ".expected.json"
        if os.path.exists(expected):
            yield cfg, expected


class TestGoldenCorpus(unittest.TestCase):

    def test_corpus_is_at_least_five_cases(self):
        self.assertGreaterEqual(len(list(_cases())), 5)

    def test_corpus_matches_expectations(self):
        for cfg, expected_path in _cases():
            with self.subTest(fixture=os.path.basename(cfg)):
                with open(expected_path, encoding="utf-8") as f:
                    expected = json.load(f)
                report = run_checks(parse_file(cfg))

                self.assertEqual(report.result, expected["result"])

                coverage = report.parser_coverage()["coverage_percent"]
                self.assertIsNotNone(coverage)
                self.assertGreaterEqual(coverage, expected["min_parser_coverage"])

                # Zero false negatives: every required high-signal finding present.
                actual = {(x.check_id, x.severity, x.status) for x in report.findings}
                for req in expected["must_flag"]:
                    present = any(
                        cid == req["check_id"] and sev == req["severity"]
                        and status in ("fail", "warn")
                        for (cid, sev, status) in actual)
                    self.assertTrue(
                        present,
                        f"{os.path.basename(cfg)}: missing required finding "
                        f"{req['check_id']} [{req['severity']}] (false negative)")

    def test_clean_fixtures_have_no_unbacked_failures(self):
        # Defensive: a "pass" fixture must not emit any FAIL finding.
        for cfg, expected_path in _cases():
            with open(expected_path, encoding="utf-8") as f:
                expected = json.load(f)
            if expected["result"] != "pass":
                continue
            with self.subTest(fixture=os.path.basename(cfg)):
                report = run_checks(parse_file(cfg))
                self.assertFalse(
                    any(x.status == "fail" for x in report.findings),
                    f"{os.path.basename(cfg)}: a pass fixture should have no FAIL")


if __name__ == "__main__":
    unittest.main()
