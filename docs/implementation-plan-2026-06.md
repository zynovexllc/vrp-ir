# Implementation Plan (2026-06)

This document turns [`docs/evolution-plan-2026-06.md`](evolution-plan-2026-06.md)
and [`docs/program-plan-2026-2027.md`](program-plan-2026-2027.md) into concrete
execution batches.

It is intentionally short on vision language and long on execution criteria.

## 1. Objective

Deliver the next `vrp-ir` improvements in an order that preserves trust:

1. repo/public-state accuracy,
2. backlog accuracy,
3. corpus-driven growth inputs,
4. only then broader parser/contract work.

## 2. Current execution rule

Until new real de-identified corpus arrives, **do not** start a speculative
parser-hardening refactor.

That means:

- `#74` is policy-governed by corpus availability.
- `#75` remains a later stabilization target.
- the next implementation batches should focus on **truth surfaces** and
  **corpus-readiness**.

## 3. Batch plan

## Batch A1: Public-state cleanup

### Status

Completed in the current working tree.

### Scope

- Fix all remaining public docs drift caused by the `0.7.0` / `0.8.0` / `0.9.0`
  releases.
- Ensure capability, check-count, and output-format claims match the current
  repo.

### Concrete items

- README status/capability summary
- `docs/commercial.md`
- changelog compare links
- any other doc still claiming `13` checks or pre-`0.9` output surface

### Exit criteria

- No stale public claim found by targeted grep.
- Repo docs accurately describe the current shipped surface.

## Batch A2: Backlog hygiene

### Status

Completed at the issue level:

- `#65` closed
- `#66` closed
- `#67` updated with current-state notes
- `#74` updated as corpus-blocked
- `#75` reaffirmed as later-stage work

### Scope

- Close or narrow issues that are already effectively shipped.
- Mark blocked work as blocked, not as silently "ready".

### Concrete items

- Close `#65` with a shipped-summary comment.
- Close or narrow `#66` with a shipped-summary comment.
- Update `#67` with a current-state comment separating:
  - already delivered,
  - blocked by corpus,
  - later-stage work.
- Update `#74` with an explicit blocked-by-corpus note.
- Reaffirm `#75` as later-stage contract work.

### Exit criteria

- Open issues reflect actual remaining work rather than historical release scope.

## Batch B1: Corpus-readiness

### Status

Completed in the current working tree:

- fixture taxonomy added
- coverage ledger added
- fixture intake workflow documented
- issue intake templates updated for safer/smaller corpus reports

### Scope

Prepare the repo to absorb more de-identified real configs cleanly.

### Concrete items

- Add a fixture taxonomy note under `tests/fixtures/README.md` or a sibling doc.
- Add a coverage ledger documenting:
  - config families represented,
  - commands intentionally unsupported,
  - checks blocked by missing corpus.
- Add a short maintainer workflow for accepting a new de-identified fixture:
  - where the fixture goes,
  - how expected output is generated/reviewed,
  - what redactions are mandatory.

### Exit criteria

- A new maintainer or contributor can add a corpus-backed fixture without guesswork.

## Batch B2: Corpus-backed coverage expansion

### Scope

Only start when at least one new real de-identified config exposes a concrete
blind spot.

### Candidate areas

- `vsys`
- `aaa` password policy
- interface/routing authentication
- additional management-plane controls

### Gate

No batch starts unless a real fixture demonstrates the gap.

## Batch C1: 1.0 contract preparation

### Scope

Start only after at least one more cycle of corpus-backed expansion confirms
that the current output surface is stabilizing.

### Concrete items

- draft JSON Schema for parse output and audit output,
- draft `docs/check-catalog.md`,
- draft deprecation policy,
- identify output fields still too volatile to freeze.

## 4. Decision log for what is intentionally deferred

### Deferred: parser hardening refactor

Reason:

- the current parser ships useful value already,
- the issue itself requires corpus-driven justification,
- a speculative refactor has regression risk without immediate user value.

### Deferred: live collection

Reason:

- this belongs to the integration layer, not the OSS core.

### Deferred: multi-vendor expansion

Reason:

- it weakens the current wedge and crosses the open-core boundary.

### Deferred: certification-grade standards content

Reason:

- the repo doctrine is advisory-only; certification-grade content belongs to
  AegisTwin.

## 5. Validation gate for every batch

Every batch must satisfy:

1. clear user-trust or workflow value,
2. no contradiction with `GOVERNANCE.md`,
3. no weakening of tests,
4. `PYTHONPATH=src python3 -m unittest discover -s tests` green,
5. `ruff check .` green.

## 6. Immediate next actions

The immediate next actions after this document lands are:

1. record the active program state against the phase gates,
2. keep Phase 0/1 artifacts accurate,
3. only choose the first true Batch B2 candidate when new corpus exists.

## 7. Backlog sync

The current remote backlog mapping is:

- `#67` — umbrella for remaining interop/maturity work
- `#74` — parser hardening, explicitly corpus-blocked
- `#75` — later-stage 1.0 contract work
- `#87` — the concrete next-step unlock issue for collecting the next
  de-identified corpus batch

This means the next justified mainline action is **not** to start `#74`; it is
to satisfy `#87`.
