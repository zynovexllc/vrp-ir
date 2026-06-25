# Roadmap

This roadmap describes **direction and priorities**, organized as **Now / Next /
Later**. It deliberately does **not** promise dates or guarantee that a specific
feature ships in a specific release. Released versions follow SemVer; the
roadmap is a statement of intent, not a delivery commitment.

> `vrp-ir` is the open core of **AegisTwin**. This roadmap covers the
> open-source project only. See the [open-core boundary](#open-core-boundary)
> for what is intentionally out of scope here.

## Guiding principle: evidence correctness first

`vrp-ir`'s core asset is a **line-cited** conclusion. Its worst failure mode is a
**wrong** line-cited conclusion — a false negative or false positive that carries
a `file:line` reference and is therefore trusted. So the overriding rule is:

> **No source, no claim.** If a fact or finding cannot be traced to a parsed
> source line, it is reported as `NA` / `UNCHECKED`, never as `PASS` or `FAIL`.

Anything that scales the reach of an assertion (CI integrations, security
dashboards, standard-mapping language) lands **after** the evidence foundation
it depends on.

## Themes

1. **Evidence correctness / trust** — every parser and audit output is traceable
   and reproducible; honest coverage; explicit handling of "not checked".
2. **Standards anchoring (advisory, level-aware)** — map checks to publicly
   citable baselines (vendor hardening, CIS-style, and 等保 *Level 3 / Level 4*
   relevant clauses) as **advisory references only** — never a certification
   claim.
3. **Workflow interoperability (CLI / CI)** — make line-cited reports consumable
   by pipelines (e.g. SARIF / JUnit) so audits can gate changes.
4. **Coverage breadth, corpus-driven** — widen Huawei VRP/USG coverage where the
   ecosystem leaves a gap, driven by real (de-identified) configs rather than
   speculation.
5. **Stability contract** — a documented, versioned IR schema and stable check
   ids. This is what defines 1.0, not a feature count.

## Now

Theme: **Trust foundation.** Make "the evidence cannot lie" provable, and make
that work visible.

- Audit **evidence policy**: findings without source evidence can only be
  `NA` / `UNCHECKED`; add `confidence`, `reference`, and `rationale` to findings.
- **Golden corpus**: grow de-identified real-world fixtures with expected audit
  snapshots; CI gate = **zero false negatives** on held-out real configs.
- **Richer report + coverage transparency**: surface confidence, references,
  rationale, exact source line, and `CHECKED / NA / UNCHECKED` coverage.
- **Advisory standards anchoring (v0)**: a `framework + level` reference field
  (等保三级/四级 alongside CIS / vendor baselines), advisory-only, clause numbers
  manually verified — never fabricated, never a certification claim.
- **SARIF / JUnit output** (lands only after the evidence fields above).

## Next

Theme: **Evidence interop & breadth**, corpus-driven.

- **Check registry**: registered check functions with structured metadata
  (id, advisory refs, evidence requirements, severity rationale). Not a
  declarative DSL.
- **Parser hardening**: corpus-driven; a view/context state machine plus
  table-driven command dispatch; fix only the gaps that real configs expose.
- **Coverage expansion**: e.g. `vsys`, SNMPv3 users, `aaa` password policy,
  interface/routing authentication.
- **Config diff**: field-level `vrp-ir diff` with `SourceRef`, for
  before/after acceptance.

## Later

Theme: **Rule & parser maturity.** Direction only — explicitly not a commitment.

- **Stability contract**: freeze IR schema and check ids; documented deprecation
  policy; remove the alpha marker.
- **Declarative checks (maybe)**: only after the corpus shows which patterns
  repeat. The valuable asset is the curated rule set, not the engine.
- **Interop**: optional bridges to existing tooling (reuse, do not reinvent).
- **YAML export**: community-PR-driven; JSON already covers machine consumption.

## Open-core boundary

`vrp-ir` (OSS) stays free under Apache-2.0. The following are intentionally
**out of scope for this repository** and belong to AegisTwin (commercial):

- Multi-vendor abstraction (H3C/Comware, etc.) and extended device families
  (WAF / AntiDDoS / 4A).
- Deep, curated **等保 Level 3 / Level 4 clause matrices** and other
  certification-grade baseline content.
- HLD/LLD → traceable acceptance-test-case generation.
- Customer-grade report templates, sign-off workflow, and the acceptance
  workbench.
- Private corpora, managed pipelines, and SLA-backed support.

The OSS project ships **mechanisms and publicly verifiable checks**; it does not
ship proprietary content. See [`docs/commercial.md`](docs/commercial.md).

## A note on standards and compliance

Standard references in `vrp-ir` are **advisory**. They help a reviewer connect a
finding to a publicly citable control; they are **not** a compliance
certification and do not constitute a regulatory endorsement. Clause-level
mappings are added only after manual verification against the standard text.
