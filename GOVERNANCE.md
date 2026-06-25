# Governance

This document describes how `vrp-ir` is governed: what it is, who decides, and
the standards a contribution must meet. It exists so contributors know what to
expect and so the project stays trustworthy.

## Project scope and non-goals

**Scope.** `vrp-ir` parses **offline** Huawei VRP/USG configuration into a
source-traceable IR (`SourceRef` per field) and runs an **advisory** security
acceptance audit whose findings cite the exact source line.

**Non-goals (intentionally out of scope):**

- Live device collection or command execution (offline input only).
- Multi-vendor abstraction and analysis (belongs to AegisTwin).
- Compliance **certification** claims of any kind.
- Proprietary or customer-specific baseline content.
- Reinventing capabilities that exist in `ntc-templates`, `hier_config`,
  `napalm`, or `Batfish` — integrate in a later layer instead.

See [`ROADMAP.md`](ROADMAP.md) for direction and the open-core boundary.

## Open-core and commercial transparency

`vrp-ir` is the open core of **AegisTwin**, a commercial acceptance product by
Zynovex. The project is sponsored and led by Zynovex; final decisions on
architecture and roadmap rest with the maintainers. We state this openly: a
library with a commercial backer is **less** likely to be abandoned, and a clear
boundary protects contributors from investing in something that will be pulled
behind a paywall. What is OSS stays OSS under Apache-2.0.

## Decision model

- **Maintainers** (currently Zynovex) own merge and release decisions.
- Changes are classified by blast radius:
  - *parser construct / audit check* — normal review.
  - *IR schema / check-id / report contract* — breaking-change review; requires
    a maintainer decision and a deprecation plan.
- Disagreements are resolved by the maintainers in the open (issue/PR threads).
  We optimize for project trustworthiness over feature velocity.

## What a good contribution looks like

The highest-value contribution is a **real, de-identified** config snippet we
parse incorrectly. Before sharing any config, follow
[`docs/de-identifying-configs.md`](docs/de-identifying-configs.md).

Every PR that adds or changes behavior must satisfy:

1. **Provenance.** New parsed values carry a `SourceRef`, asserted by a test.
   A value without a verified source is a bug.
2. **No garbage facts.** If a value cannot be parsed cleanly, skip it rather than
   surface something partial.
3. **Honest findings.** A check reports a status it can defend: `PASS` / `WARN` /
   `FAIL` / `NA` / `UNCHECKED`. **No source, no claim** — never imply `PASS` when
   nothing was actually checked.
4. **Advisory standards only.** Any standard reference is advisory, level-aware,
   and clause numbers are manually verified — never fabricated, never presented
   as certification.
5. **No weakened tests.** Do not delete or weaken existing tests to make a change
   pass, unless the behavior change is intentional and called out.
6. **Dependency-free core.** No third-party runtime dependencies.
7. **Green gates.** `PYTHONPATH=src python3 -m unittest discover -s tests` and
   `ruff check .` pass.

## Stability and compatibility

- Releases follow **SemVer**.
- Before 1.0, the IR schema and check ids may change; such changes are noted in
  the changelog.
- **1.0 is a stability contract**, not a feature milestone: it freezes the IR
  schema and check-id catalogue and commits to a deprecation policy.

## Releases

Merging to `main` does not publish to PyPI. Releases are maintainer-approved and
follow [`docs/release-process.md`](docs/release-process.md).

## Maintainer commitments

- Best-effort triage and first response on issues and PRs.
- Security reports are handled privately per [`SECURITY.md`](SECURITY.md).
- First-time contributors are acknowledged in release notes when their PR merges.

## AI-assisted contributions

AI-assisted code and review are allowed. The same bar applies: provenance,
honest findings, no weakened tests, dependency-free core, green gates. The
contributor is responsible for the result.

## Red lines (always in force)

- **Provenance-first**: no surfaced value without a verified source.
- **Advisory, not certification**: never claim compliance certification.
- **Reuse, don't reinvent**: integrate existing tooling in later layers.
- **Dependency-free core**.
- **Privacy**: never commit real IPs, hostnames, secrets, SNMP communities, keys,
  or customer-identifying topology.
