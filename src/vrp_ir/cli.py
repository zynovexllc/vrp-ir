"""Command-line interface: ``vrp-ir parse <config>`` / ``vrp-ir audit <config>``.

``parse`` outputs the parsed IR as JSON (every value carries its SourceRef);
``audit`` runs security acceptance checks and prints a report (Markdown or JSON)
in which every finding cites the exact source line it is based on.
"""
from __future__ import annotations

import argparse
import json
import sys

from .acceptance import render_markdown, run_checks
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
    pa.add_argument("--format", choices=["md", "json"], default="md",
                    help="Report format (default: md).")
    pa.add_argument("--strict", action="store_true",
                    help="Exit non-zero if any check fails (CI gate).")

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
        else:
            sys.stdout.write(render_markdown(report))
        return 1 if (args.strict and report.result == "fail") else 0
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
