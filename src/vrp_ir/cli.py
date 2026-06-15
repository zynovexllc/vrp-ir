"""Command-line interface: ``vrp-ir parse <config> [--json]``.

Outputs the parsed IR as JSON (every value carries its SourceRef), so it can
feed downstream tooling (topology builders, acceptance checks, report
generators) in later milestones.
"""
from __future__ import annotations

import argparse
import json
import sys

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

    args = p.parse_args(argv)

    if args.command == "parse":
        cfg = parse_file(args.config)
        json.dump(cfg.to_dict(), sys.stdout, ensure_ascii=False, indent=args.indent)
        sys.stdout.write("\n")
        return 0
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
