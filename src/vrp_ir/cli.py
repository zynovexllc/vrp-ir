"""Command-line interface: ``vrp-ir parse <config>`` / ``vrp-ir audit <config>``.

``parse`` outputs the parsed IR as JSON (every value carries its SourceRef);
``audit`` runs security acceptance checks and prints a report (Markdown, JSON,
SARIF, or JUnit) in which every finding cites the exact source line it is based
on.
"""
from __future__ import annotations

import argparse
import json
import sys

from .acceptance import (explain_check, list_checks, render_junit,
                         render_markdown, render_sarif, run_checks)
from .parser import parse_file


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="vrp-ir",
        description="Parse a Huawei VRP configuration into a source-traceable IR.")
    sub = p.add_subparsers(dest="command", required=True)

    pp = sub.add_parser("parse", help="Parse a VRP config file to JSON IR.")
    pp.add_argument("config", help="Path to a VRP configuration file.")
    pp.add_argument("--indent", type=int, default=2,
                    help="JSON indent (default: 2).")

    pa = sub.add_parser("audit", help="Run security acceptance checks on a config.")
    pa.add_argument("config", help="Path to a VRP/USG configuration file.")
    pa.add_argument("--format", choices=["md", "json", "sarif", "junit"],
                    default="md", help="Report format (default: md).")
    pa.add_argument("--strict", action="store_true",
                    help="Exit non-zero if any check fails (CI gate).")

    sub.add_parser("checks", help="List all audit checks.")

    pe = sub.add_parser("explain", help="Explain one audit check by id.")
    pe.add_argument("check_id", help="A check id, e.g. FW-DEFAULT-DENY.")

    args = p.parse_args(argv)

    if args.command == "parse":
        cfg = parse_file(args.config)
        json.dump(cfg.to_dict(), sys.stdout, ensure_ascii=False, indent=args.indent)
        sys.stdout.write("\n")
        return 0
    if args.command == "audit":
        report = run_checks(parse_file(args.config))
        if args.format == "json":
            json.dump(report.to_dict(), sys.stdout, ensure_ascii=False, indent=2)
            sys.stdout.write("\n")
        elif args.format == "sarif":
            sys.stdout.write(render_sarif(report))
        elif args.format == "junit":
            sys.stdout.write(render_junit(report))
        else:
            sys.stdout.write(render_markdown(report))
        return 1 if (args.strict and report.result == "fail") else 0
    if args.command == "checks":
        for c in list_checks():
            sys.stdout.write(f"{c['check_id']}  —  {c['intent']}\n")
        return 0
    if args.command == "explain":
        info = explain_check(args.check_id)
        if info is None:
            sys.stderr.write(f"unknown check id: {args.check_id}\n")
            return 2
        sys.stdout.write(f"{info['check_id']}\n{info['intent']}\n")
        if info["references"]:
            sys.stdout.write("\nAdvisory references (not a certification claim):\n")
            for r in info["references"]:
                lvl = f" {r['level']}" if r["level"] else ""
                verified = "" if r["manual_verified"] else " [unverified]"
                sys.stdout.write(f"  - {r['framework']}{lvl}: {r['control']}{verified}\n")
        return 0
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
