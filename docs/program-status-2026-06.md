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

## 3. Phase 2: Manual-Grounded Coverage Build

### Entry gate

Phase 2 begins when:

1. Phase 0 and Phase 1 are complete, and
2. a concrete manual-grounded evidence batch is selected.

### Assessment

`ACTIVE NEXT MAINLINE`

Reason:

- Phase 0 and Phase 1 are complete
- the first concrete evidence batch has been selected:
  - `docs/evidence-batch-aaa-password-policy.md`
- this batch is based on public primary sources plus later zero-export field
  validation, which matches the current program direction

### Decision

Phase 2 is the active mainline.

## 4. Phase 3: Feedback / Field Validation

### Assessment

`NOT STARTED`

Reason:

- the repo has not yet completed the first manual-grounded coverage batch
- feedback / field validation remains a later correction and confirmation phase

## 5. Phase 4: Stability Contract

### Assessment

`NOT STARTED`

Reason:

- the repo has not yet completed manual-grounded expansion
- the repo has not yet completed a feedback/field-validation cycle

## 6. Phase 5: Integration Layer

### Assessment

`NOT STARTED`

Reason:

- integration work is explicitly downstream of a more mature and re-validated
  core

## 7. Active next-step rule

The current valid next-step trigger for mainline feature work is:

> completion of the selected manual-grounded evidence batch

Current repo representation of that batch:

- `docs/evidence-batch-aaa-password-policy.md`
- GitHub issue `#92` — `Manual analysis batch: AAA password policy`

Until that batch is completed, the repo may still do:

- maintenance,
- factual corrections,
- release hygiene,
- and plan/status updates,

but it should keep Phase 2 focused on manual-grounded coverage work, not drift
into speculative architecture refactors.

## 8. Feedback / field-validation track

The feedback / field-validation track is still relevant, but it is no longer
the mainline gate.

Current backlog representation:

- `#87` — `Field evidence / feedback track for post-manual validation`
