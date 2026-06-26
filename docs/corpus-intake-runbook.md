# Corpus Intake Runbook

This runbook governs how `vrp-ir` accepts new real-world parser/audit corpus.

Its purpose is twofold:

1. protect users from leaking sensitive production configuration data;
2. make sure new corpus actually improves the repo rather than becoming random
   config accumulation.

This is a maintainer-facing workflow, but contributors should also be able to
read it and know which submission path is appropriate.

For copyable outbound request language, see
[`docs/corpus-request-template.md`](corpus-request-template.md).

## 1. Intake decision tree

Use this order every time:

### Path A: public issue

Use a normal public issue **only if** all of these are true:

- the snippet is the smallest reproducer you could make,
- it is synthetic or safely de-identified,
- no live secrets remain,
- no customer-identifying topology remains,
- the remaining content is sufficient to reproduce the parser/audit behavior.

Preferred templates:

- **Config parsing issue** for parser/audit repro snippets
- **Bug report** for crashes or other non-snippet-specific defects

### Path B: private config handoff

Use a private handoff when the sample is high-value but you are **not confident**
you can safely publish it yet.

Examples:

- a real config still contains customer-identifying topology even after initial
  scrubbing,
- the bug depends on a larger config context than is easy to reduce safely,
- you want maintainer help deciding what can be generalized into a public
  de-identified reproducer.

Current private handoff channel:

- `support@zynovexllc.com`

Expectation:

- the maintainer should reduce or scrub the sample further before any part of it
  becomes public or is committed into the repo.

### Path C: private security advisory

Use GitHub **Security Advisories** instead of public issues or support email if
the problem is also a security issue.

Examples:

- crafted input crashes or hangs the parser,
- malformed config triggers unbounded resource use,
- the report requires sharing sensitive config material that should stay private
  while a fix is prepared.

Current private security channel:

- repository **Security** tab → **Report a vulnerability**

## 2. Maintainer intake checklist

Before accepting a new real-world sample into the repo:

1. Confirm which intake path was used and whether it was appropriate.
2. Confirm the sample is actually needed:
   - does it expose a parser blind spot,
   - an evidence-quality gap,
   - or an audit false negative / false positive?
3. Reduce the sample to the smallest reproducer practical.
4. Re-scrub:
   - hostnames,
   - public/private IPs that reveal real topology,
   - communities,
   - credentials,
   - keys,
   - identifiers,
   - provider/customer names,
   - ticket/circuit references.
5. Decide whether the sample can safely move from private handling into a public
   fixture.

If the answer to step 5 is "no", do not commit it.

## 3. Promotion rule: from sample to shipped fixture

A de-identified real-world sample should be promoted into `tests/fixtures/` only
when all of these are true:

1. it is safe to publish,
2. it exposes a behavior worth preserving in regression tests,
3. the expected parser/audit boundary can be written down clearly,
4. it belongs to a fixture family that is not already over-represented by a
   near-duplicate.

Required repo artifacts when promotion happens:

- `<name>.cfg`
- `<name>.expected.json`
- direct unit tests if new parse-time facts or `SourceRef` invariants deserve
  pinning
- an update to `docs/coverage-ledger.md` if the coverage boundary changed

## 4. Acceptance rubric for opening a follow-up implementation batch

A new sample is **not** automatically permission to start coding.

Use the sample to ask:

1. Is this an isolated syntax edge, or evidence of a repeated parser pattern?
2. Does it expose a missing parsed construct, or a missing check, or an
   evidence-quality weakness?
3. Can the fix be done as a small batch without speculative architecture work?
4. Does it justify a Phase 2 batch, or should it wait for one more similar
   sample to prove the pattern?

Only after this rubric is answered should maintainers choose the next coding
batch.

## 5. Red lines

- Never commit raw production configs.
- Never use public issues for samples that are not safely de-identified.
- Never turn a private sample into a public fixture without re-scrubbing and
  reduction.
- Never let "interesting config" override the repo's narrow scope.
