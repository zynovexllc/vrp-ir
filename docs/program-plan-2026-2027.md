# Program Plan (2026-2027)

This is the governing execution plan for `vrp-ir`.

It exists to prevent ad-hoc sequencing. Work should advance by **phase gate**,
not by whatever looks interesting in the moment.

If any lower-level plan conflicts with this document, this document wins until a
maintainer deliberately revises it.

## 1. Planning hierarchy

The planning stack for this repo is:

1. [`GOVERNANCE.md`](../GOVERNANCE.md)
2. [`docs/evolution-plan-2026-06.md`](evolution-plan-2026-06.md)
3. **this document** (`program-plan-2026-2027.md`)
4. [`docs/implementation-plan-2026-06.md`](implementation-plan-2026-06.md)
5. individual issues / PRs / release batches

Interpretation:

- `GOVERNANCE.md` defines red lines and contribution rules.
- `evolution-plan` explains *why* the strategy is what it is.
- `program-plan` defines the long-horizon sequence and phase gates.
- `implementation-plan` defines the current executable batches inside the active
  phase.

## 2. North-star objective

Build `vrp-ir` into a stable, evidence-grade OSS core for **offline Huawei
VRP/USG acceptance** that downstream users can:

- trust,
- automate in CI,
- and safely build against.

That objective is narrower than "network automation platform" and narrower than
"generic multi-vendor compliance tool". That narrowness is intentional.

## 3. Strategic invariants

These are not optional. Every phase must preserve them.

1. **Evidence first**: no source, no claim.
2. **Corpus before architecture**: parser shape follows real de-identified
   inputs, not speculative elegance.
3. **OSS core stays narrow**: no drift into multi-vendor abstraction, live
   collection, remediation, or certification-grade content.
4. **Contracts are earned**: `1.0` happens only after output stability is
   demonstrated.
5. **Small reversible batches**: one batch, one verification gate, then the
   next batch.

## 4. Long-horizon phase map

## Phase 0: Truth Surfaces

### Purpose

Ensure the repo, docs, and backlog describe the project that actually exists.

### Allowed work

- public docs drift cleanup
- issue/epic cleanup
- release/process docs correction
- maintainer planning docs

### Explicitly not allowed as primary work

- speculative parser refactors
- new parser surface without corpus trigger
- early 1.0 contract freeze

### Exit gate

Phase 0 is complete only when:

1. public capability docs match the released repo,
2. stale epics are closed or narrowed,
3. the remaining open issues describe genuinely remaining work.

## Phase 1: Corpus Readiness

### Purpose

Make the repo operationally ready to accept and govern more real de-identified
corpus.

### Allowed work

- fixture taxonomy
- fixture intake workflow
- coverage ledger
- maintainer guidance for de-identified fixture acceptance

### Explicitly not allowed as primary work

- broad parser rewrites
- feature-count chasing disconnected from new corpus

### Exit gate

Phase 1 is complete only when:

1. a maintainer can add a new de-identified fixture without guesswork,
2. current coverage and corpus gaps are versioned in-repo,
3. the next corpus-backed batch can be selected by policy rather than intuition.

## Phase 2: Corpus-Backed Expansion

### Purpose

Expand parse/audit value only where real corpus demonstrates demand.

### Allowed work

- parser additions tied to new de-identified fixtures
- new checks tied to real acceptance gaps
- evidence-quality improvements tied to real findings
- small CI/output improvements supporting real user workflows

### Explicitly not allowed as primary work

- architecture-led parser rewrite with no new corpus trigger
- broad scope expansion beyond Huawei VRP/USG offline acceptance

### Exit gate

Phase 2 is mature enough to move on only when:

1. at least one full additional cycle of corpus-backed expansion has landed,
2. output fields and check IDs show low churn across those batches,
3. maintainers can name which outputs are stable enough to freeze.

## Phase 3: Stability Contract

### Purpose

Prepare and ship `1.0` as a real contract.

### Allowed work

- JSON Schema for parse output
- JSON Schema for audit output
- published check catalogue
- deprecation policy
- removal of stale `alpha` language once the contract is real

### Explicitly not allowed as primary work

- using `1.0` as a marketing milestone without contract artifacts

### Exit gate

Phase 3 is complete only when:

1. schema artifacts exist and validate in CI,
2. the check catalogue is published,
3. deprecation policy is documented,
4. maintainers are willing to preserve compatibility intentionally.

## Phase 4: Integration Layer

### Purpose

Make `vrp-ir` easier to adopt in external workflows without bloating the core.

### Allowed work

- better GitHub SARIF guidance
- better GitLab JUnit guidance
- examples of pairing `vrp-ir` with collection/remediation tooling
- reference CI integrations

### Explicitly not allowed as primary work

- moving integration concerns into the core parser/audit package

## 5. Sequencing rule

The active rule is:

> **Do not start work from a later phase while an earlier phase is still missing
> its exit gate, unless a maintainer explicitly records an exception.**

This means:

- no parser-hardening refactor while the project is still cleaning up truth
  surfaces and corpus governance,
- no `1.0` contract work as the mainline while corpus-backed expansion is still
  unsettled.

## 6. Batch rule inside each phase

Inside the active phase:

1. choose one batch,
2. define its exit criteria,
3. implement,
4. run gates,
5. record the result,
6. only then choose the next batch.

No phase should have multiple fuzzy "current priorities".

## 7. Change-control rule

A later-phase item may be pulled earlier only if one of these is true:

1. it fixes a public factual error,
2. it unblocks the active phase,
3. a new real de-identified corpus artifact makes the later work newly
   non-speculative,
4. a release-critical downstream consumer workflow is blocked without it.

If none of those is true, the item waits.

## 8. Current program state (2026-06)

Current assessment:

- **Phase 0**: complete
- **Phase 1**: complete
- **Phase 2**: not yet active as the mainline
- **Phase 3**: not active
- **Phase 4**: not active

Interpretation:

- Phase 0/1 preparation is complete; their status should now be maintained, not
  re-opened casually.
- It is **not** valid to treat Phase 2 or Phase 3 as the mainline yet.

## 9. Active next-step policy

Until a new corpus-backed trigger exists, the only valid "what next?" answers
are:

1. maintain truth-surface accuracy,
2. maintain corpus-readiness artifacts,
3. record status cleanly,
4. wait for a real de-identified corpus trigger.

Only after that should the project select the first real corpus-backed expansion
batch.
