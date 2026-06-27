# Evidence Batch Brief: Password Complexity Command-Model Split

This document defines the next manual-analysis batch after the shipped
`local-aaa-user password policy` parser/audit cycle.

It does **not** authorize implementation work yet. Its purpose is to determine
whether Huawei password-complexity controls are one stable implementation model
or multiple product/view-specific models that must stay split.

Mandatory artifact:

- [`docs/password-complexity-command-model-matrix.md`](password-complexity-command-model-matrix.md)

Current evidence rule:

- no follow-up implementation issue may mix `user-password complexity-check`
  and `local-user policy password complexity-enhance` unless the support matrix
  proves they are the same model for repo purposes
- conflicting defaults are a stop sign, not something to average together

## 1. Why this target is next

The repo has now completed one full manual-grounded cycle for the
`local-aaa-user password policy` family.

The next adjacent candidate is password complexity, because it remained
explicitly deferred in the previous matrix due to product/view/default drift.

This makes it a good next batch:

- it is close enough to the shipped AAA work to reason about efficiently,
- it still has unresolved command-model ambiguity,
- and forcing it directly into code would violate the current strategy.

## 2. Evidence objective

The batch succeeds if we can answer all of these:

1. Is `user-password complexity-check` the same command model as
   `local-user policy password complexity-enhance`, or not?
2. Which views and product families do these commands belong to?
3. Do their defaults agree strongly enough to support an honest offline audit
   check?
4. Is there a small narrowed follow-up batch worth opening, or should this
   family remain deferred?

## 3. Public-primary-source tasks

Use public primary sources first.

Initial candidate rows:

- `user-password complexity-check` on WLAN/AP-style command references
- `user-password complexity-check` on Huawei docs where the local-user default
  is described differently
- `local-user policy password complexity-enhance` on CX-style docs

For each row, capture:

1. command family
2. product/doc source
3. view / scope
4. default behavior
5. whether it is saved-config syntax
6. what fact the parser could safely surface
7. what offline semantic, if any, is safe to audit
8. whether it belongs to a shared or separate command model

## 4. Decision gate

Open a real implementation batch only if the support matrix supports one of
these:

### Case A: one narrowed command family is stable

The maintainer can point to one specific product/view family with stable enough
syntax and default semantics to justify a parser or audit batch.

### Case B: explicit audit semantics are safe without default guessing

The maintainer can point to an explicit weakening form whose meaning is stable
enough to audit without inferring anything from command absence.

### Case C: remain deferred

If the family still collapses multiple product/view/default models together, do
not force implementation. Record the split and move to a different candidate.

## 5. Acceptance criteria for this evidence batch

This batch is complete only when:

1. the matrix is filled for the candidate rows,
2. product/view/default drift is explicit,
3. the maintainer can classify the outcome as:
   - `open narrowed parser batch`,
   - `open narrowed audit batch`,
   - or `defer`,
4. no implementation issue is opened until the command-model split is resolved.
