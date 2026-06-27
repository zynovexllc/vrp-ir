# Evidence Batch Brief: AAA Password Policy

This document defines the first concrete manual-analysis batch for Phase 2.

It does **not** authorize implementation work yet. Its purpose is to determine
whether `aaa` password policy is strong enough to justify the first real
Phase 2 parser/audit batch.

Mandatory artifact:

- [`docs/aaa-password-policy-support-matrix.md`](aaa-password-policy-support-matrix.md)

Current evidence rule:

- this batch must first determine whether `aaa` password policy is one stable
  command model or multiple product/view-specific subfamilies
- no follow-up implementation issue may mix different command models just
  because they are all "about passwords"

## 1. Why this target is first

`aaa` password policy is a strong first candidate because it is already listed
in [`docs/coverage-ledger.md`](coverage-ledger.md) as a not-yet-shipped area,
but it is narrower and easier to reason about than a broad parser-hardening
refactor.

This target is also suitable for the current evidence-source policy because it
can be approached through:

- public command references,
- grammar-only command skeletons,
- reduced management-plane blocks,
- and zero-export field confirmation.

It does **not** require starting with a topology-rich full config.

## 2. Evidence objective

The batch succeeds if we can answer all of these:

1. Which Huawei VRP/USG command families express local password policy in a way
   relevant to offline acceptance?
2. Are these commands top-level, inside `aaa`, or inside a dedicated password
   policy view?
3. Which parts are parse-worthy facts versus merely display/operational output?
4. Is there enough real-world evidence to justify:
   - a parser addition,
   - an audit addition,
   - or no repo change yet?

## 3. Public-primary-source tasks

Use public primary sources first.

Candidate command families already identified from Huawei public references:

- `local-aaa-user password policy administrator`
- `local-aaa-user password policy access-user`
- `password expire`
- `password alert before-expire`
- `password alert original`
- `password history record number`
- `user-password complexity-check`
- `local-user password expire`
- `local-user policy password expire`
- `local-user policy password complexity-enhance`
- `display local-aaa-user password policy`

For each command family, capture:

1. command name
2. command function in one sentence
3. configuration view / scope
4. whether it is config syntax or display-only syntax
5. any obvious parameters that affect acceptance posture
6. whether the command appears device-family-specific or broadly VRP-like
7. whether it appears in saved config, not merely in display output
8. whether it belongs to the same command model as the other candidates, or a
   separate product/view family that should be deferred

## 4. Zero-export field-validation tasks

Ask operator or integrator contacts only questions that do **not** require text
export.

Preferred questions:

1. Do you see a dedicated local password policy view in real deployments, or is
   password policy usually expressed through scattered one-line commands?
2. Is password complexity control typically enabled by default and left alone,
   or actively configured?
3. Are password expiry and pre-expiry alerts commonly configured for local
   administrators?
4. Is the relevant syntax more common on VRP switching/routing gear, on USG, or
   on both?
5. Is there any command family here that is common in production but absent from
   public examples?

Preferred artifact types:

- grammar-only command skeletons
- yes/no validation of command-family prevalence
- reduced management-plane blocks with placeholders

Not acceptable as the first ask:

- full config backup
- architecture-bearing AAA section
- real usernames, IPs, ACLs, or policy values

## 5. Decision gate

Open a real implementation batch only if the support matrix supports one of
these:

### Case A: parser-worthy structure exists

There is enough evidence that a stable **single command family/model** exists
and should be
captured in the IR with `SourceRef`.

### Case B: audit-worthy policy exists

There is enough evidence that the parseable facts support a meaningful offline
acceptance check, and that the check can be driven by **explicit configured
weakening** rather than by guessing from product defaults, such as:

- explicit expiry disabled indefinitely,
- explicit complexity checking disabled,
- explicit password-history reuse protection disabled,
- explicit initial-password-change prompting disabled.

### Case C: not enough evidence yet

If the command families are too product-specific, too sparse, or too dependent
on operational display output rather than saved config syntax, do **not** force
implementation. Record the result and move to the next candidate family.

## 6. Acceptance criteria for this evidence batch

This batch is complete only when:

1. the support matrix is filled for the target command families,
2. each command family is classified as config syntax vs display syntax,
3. any default-behavior or product-family ambiguity is explicitly recorded,
4. at least one zero-export field-validation pass is attempted when useful,
5. the maintainer can classify the outcome as:
   - `open parser batch`,
   - `open audit batch`,
   - or `defer and move to next candidate`.
6. any opened follow-up issue is narrowed to one validated command model, not a
   mixed "AAA password policy" umbrella.

## 7. Deliverables

At the end of this batch, the repo should have:

1. this brief,
2. the support matrix,
3. a short decision note added to `#92`,
4. if justified, a new concrete follow-up issue for the Phase 2 batch.
