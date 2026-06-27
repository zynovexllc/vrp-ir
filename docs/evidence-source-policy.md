# Evidence Source Policy

This document defines which evidence sources `vrp-ir` should rely on when
trying to unlock the next parser/audit batch.

It exists because, in operator and regulated enterprise environments, asking
people to export even "de-identified" configs is often unrealistic and can
still create security/accountability risk.

## 1. Working assumption

For operator / carrier /政企 environments, maintainers should assume:

- direct config export is usually **not** the default path,
- even redacted configs may still expose architecture,
- friendly contacts still may not be able to justify any export,
- therefore the repo must support **real-world evidence without raw config
  handoff**.

This is a policy assumption, not a temporary inconvenience.

## 2. Allowed evidence sources, in priority order

## Tier 1: Public primary sources

Use first whenever possible.

Examples:

- vendor command references
- vendor configuration guides
- public sample snippets in official documentation
- release/change notes describing syntax variants

Why this tier matters:

- zero customer disclosure risk
- reproducible
- easy to cite and preserve

Limits:

- may not reflect messy real deployments
- may omit edge combinations that appear in the field

## Tier 2: Self-built lab corpus

Use when public primary sources define the grammar but no safe field sample is
available.

Examples:

- synthetic configs built from official syntax docs
- lab scenarios combining known command families
- intentionally risky/hardened variants built to exercise acceptance logic

Why this tier matters:

- no customer data exposure
- allows deterministic regression fixtures
- useful for parser/audit behavior when field export is impossible

Limits:

- realism must be justified, not assumed
- synthetic configs should not be mislabeled as customer evidence

## Tier 3: Zero-export field validation

Use when a real environment can confirm behavior but cannot export config.

Examples:

- a contact confirms whether a command family exists in production
- a contact provides grammar-only command skeletons
- a contact provides yes/no validation of parse or audit behavior
- a contact provides "unparsed line family" descriptions without exporting text

Why this tier matters:

- preserves real-world grounding
- avoids raw config transfer

Limits:

- weaker than a fixture
- often sufficient to prioritize a lab-backed reproduction batch, but not always
  sufficient alone to ship a regression fixture

## Tier 4: Customer-side extraction / normalization

Use when more structure is needed but raw export is still unacceptable.

Examples:

- local extractor outputs only one command family
- local normalizer replaces identifiers with placeholders before export
- local parser run emits only unparsed-line skeletons or structured summaries

Why this tier matters:

- strong signal with much lower disclosure risk
- best realistic option for security-sensitive environments

Limits:

- requires some tooling or guided extraction
- must still be reviewed before promotion into fixtures

## Tier 5: Private config handoff

Use only exceptionally.

Why it is lowest priority:

- highest trust burden
- highest disclosure risk
- least likely to pass security review in operator environments

If this tier is used, the sample must be minimized and re-scrubbed before any
public or repo promotion.

## 3. Default disallowed strategy

The repo should **not** treat the following as its default acquisition plan:

- asking operator/政企 contacts to send full or near-full configs,
- assuming friendship or trust overrides internal security policy,
- assuming "脱敏后就没问题",
- assuming contacts can cleanly explain why they exported even a reduced sample.

Those assumptions are strategically weak and should not drive planning.

## 4. What counts as "real enough" to unlock work

A next-batch trigger does **not** require a full config export.

It is enough if the maintainer can point to a real-world evidence artifact that
is specific enough to justify one small follow-up batch, for example:

- an official syntax source plus a confirmed field-use report,
- a grammar-only skeleton that exposes a real parser blind spot,
- a customer-side extracted command-family sample,
- a reduced minimal block validated as production-derived.

What matters is not "rawness" of the sample. What matters is whether the
artifact is:

1. specific,
2. reproducible,
3. honest about its limits,
4. strong enough to justify or reject a concrete implementation batch.

## 5. Operational rule for `#87`

`#87` should be interpreted as:

> collect the next **real-world evidence batch** sufficient to unlock Phase 2

not narrowly as:

> obtain a directly exported customer config

That distinction is critical in high-security environments.
