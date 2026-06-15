# Contributing to vrp-ir

Thanks for helping make Huawei VRP configs source-traceable.

## The best contribution: real (de-identified) configs we get wrong

If `vrp-ir` mis-parses a real VRP snippet, that's the highest-value issue.
Please **de-identify** (scrub IPs, hostnames, secrets) before sharing.

## Dev setup

```bash
pip install -e .
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

No runtime dependencies; tests use the stdlib `unittest`.

## Adding a parsed construct

Every new construct must come with:

1. A minimal snippet added to `examples/` (or an existing sample extended).
2. A positive test asserting the parsed value.
3. A **SourceRef assertion** — the value must trace back to the correct line.
   (Provenance is the whole point; a value without a verified source is a bug.)

See `docs/spec-v0.1.md` for the data model and parsing rules.

## Principles

- **Reuse, don't reinvent.** If a capability already exists in `ntc-templates`,
  `hier_config`, `napalm`, or `Batfish`, integrate it in a later layer rather
  than reimplement it here.
- **No garbage facts.** If a value can't be parsed cleanly, skip it rather than
  surface something partial/wrong.
- **Keep the core dependency-free.**

## License

By contributing you agree your contributions are licensed under Apache-2.0.
