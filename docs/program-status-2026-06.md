# Program Status (2026-06)

This document records the current phase-gate assessment against
[`docs/program-plan-2026-2027.md`](program-plan-2026-2027.md).

It is the status companion to the program plan: the plan defines the allowed
sequence; this file records where the repo currently stands in that sequence.

## 1. Phase 0: Truth Surfaces

### Exit gate

Phase 0 is complete only when:

1. public capability docs match the released repo,
2. stale epics are closed or narrowed,
3. the remaining open issues describe genuinely remaining work.

### Assessment

`PASS`

Evidence:

- public docs drift corrected in:
  - `README.md`
  - `CHANGELOG.md`
  - `docs/commercial.md`
- stale epics closed:
  - `#65`
  - `#66`
- remaining open issues narrowed to genuine remaining work:
  - `#67`
  - `#74`
  - `#75`

### Decision

Phase 0 is complete.

## 2. Phase 1: Corpus Readiness

### Exit gate

Phase 1 is complete only when:

1. a maintainer can add a new de-identified fixture without guesswork,
2. current coverage and corpus gaps are versioned in-repo,
3. the next corpus-backed batch can be selected by policy rather than intuition.

### Assessment

`PASS`

Evidence:

- fixture intake workflow and taxonomy documented in `tests/fixtures/README.md`
- de-identification workflow documented in `docs/de-identifying-configs.md`
- coverage and current gaps versioned in `docs/coverage-ledger.md`
- execution and sequencing policy versioned in:
  - `docs/evolution-plan-2026-06.md`
  - `docs/implementation-plan-2026-06.md`
  - `docs/program-plan-2026-2027.md`
- issue intake templates updated to support smaller, safer, more reproducible
  corpus reports

### Decision

Phase 1 is complete.

## 3. Phase 2: Corpus-Backed Expansion

### Entry gate

Phase 2 begins only when a new real de-identified corpus artifact justifies a
specific parser/audit expansion batch.

### Assessment

`NOT STARTED`

Reason:

- no new de-identified corpus batch has been recorded in-repo since the current
  Phase 0 / Phase 1 completion work
- therefore parser-hardening or coverage-expansion work would still be
  speculative

### Decision

Phase 2 is not the active mainline yet.

## 4. Phase 3: Stability Contract

### Assessment

`NOT STARTED`

Reason:

- the repo has not yet gone through another corpus-backed expansion cycle after
  the current 0.9.0 surface
- output stability has not yet been re-demonstrated under new real corpus

## 5. Phase 4: Integration Layer

### Assessment

`NOT STARTED`

Reason:

- integration work is explicitly downstream of a more mature and re-validated
  core

## 6. Active next-step rule

The only valid next-step trigger for new feature work is:

> a new real de-identified fixture or corpus-backed acceptance gap

Current backlog representation of that trigger:

- `#87` — collect the next de-identified corpus batch to unlock Phase 2

Until that trigger exists, the repo may still do:

- maintenance,
- factual corrections,
- release hygiene,
- and plan/status updates,

but it should not pretend to be in active parser-expansion mode.
