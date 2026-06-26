# De-identified Corpus Request Template

This document provides copyable templates for asking partners, users, or
internal operators for high-value de-identified VRP/USG config samples.

The goal is to make sample collection:

- specific,
- safe,
- low-friction,
- and useful for `vrp-ir` regression coverage.

## 1. What we are asking for

We are **not** asking for full production configs by default.

We are asking for the **smallest de-identified snippet** that still reproduces
one of the following:

- a parser blind spot,
- an audit false negative,
- an audit false positive,
- or a config family that is currently under-represented in the shipped corpus.

## 2. Safe request checklist

Before sending a request, be explicit about all of these:

1. the sample should be **de-identified**,
2. the sample can be a **small snippet**, not a full config,
3. secrets must be removed,
4. customer/site/provider identifiers must be removed,
5. if they are unsure, they should use a **private handoff** instead of posting
   publicly.

## 3. Short request template

Use this when the other side already understands the project context.

```text
Hi — we are improving `vrp-ir`, our offline Huawei VRP/USG parser + line-cited
acceptance auditor.

The most useful input right now is a **real but de-identified** config snippet
that reproduces a parser or audit gap. The snippet does not need to be a full
device config — the smallest reproducer is best.

Please remove or replace:
- hostnames / site names / customer names
- public or topology-revealing IPs
- SNMP communities
- passwords / keys / hashes
- provider or circuit identifiers

If the sample is not obviously safe to share publicly, please use a **private
handoff** instead.

What helps most:
- the config snippet
- what you expected us to parse or flag
- what we currently parse or report instead
- whether file encoding matters (for example GB18030 / GBK)
```

## 4. Detailed request template

Use this when asking someone outside the immediate maintainer circle.

```text
Subject: Request for de-identified Huawei VRP/USG config snippet

Hi,

We are improving `vrp-ir`, an offline Huawei VRP/USG config parser and
acceptance-audit tool. The next development batch is intentionally driven by
real-world evidence rather than speculative parser work.

If you are willing to help, the most valuable contribution is a **real but
de-identified** config snippet that reproduces one of these:

- a section we parse incorrectly,
- a line or block we currently leave unparsed,
- an audit finding we should flag but currently miss,
- an audit finding we currently flag incorrectly.

Please send the **smallest snippet** that still reproduces the behavior.
It does not need to be a full device config.

Before sharing, please scrub or replace:
- hostnames, site names, customer names
- public IPs or internal addressing that reveals real topology
- SNMP communities
- passwords, keys, hashes, certificates
- provider, circuit, VPN, or inventory identifiers

Useful context to include:
- expected parse / expected finding
- actual parse / actual finding
- whether encoding matters (UTF-8 / GB18030 / GBK)
- whether the snippet came from VRP routing/switching, USG firewall, management
  plane, HA/HRP, or another config family

If you are not sure the sample is safe to publish, do **not** post it publicly.
Use a private handoff instead.
```

## 5. Private handoff template

Use this when a sample is high-value but likely still too sensitive for a public
issue.

```text
Hi,

I have a real Huawei VRP/USG config sample that may help improve `vrp-ir`, but
I am not yet confident it is safe to post publicly.

I would like to use the private corpus handoff path first.

What I can provide:
- a reduced config snippet or larger config section
- the parser/audit behavior I expected
- the parser/audit behavior I actually observed
- any notes on encoding or device family

Please help determine:
- what else must be scrubbed,
- whether the sample can be reduced further,
- and whether it can eventually be promoted into a safe public regression
  fixture.
```

## 6. What to ask for first

When multiple sample types are possible, ask for these in this order:

1. config families not yet strongly represented in the shipped corpus,
2. snippets that expose unparsed lines,
3. snippets that demonstrate a false negative in current audit output,
4. snippets that reveal repeated parser/view patterns worth future hardening.

## 7. What not to ask for

Do not ask for:

- full production backups unless absolutely necessary,
- anything with live secrets left in place,
- samples whose only value is "maybe interesting later",
- multi-vendor configs unrelated to the current OSS scope,
- certification-grade standards matrices or customer report templates.

## 8. Promotion reminder

A received sample is not automatically a shipped fixture.

Before promotion into `tests/fixtures/`, follow
[`docs/corpus-intake-runbook.md`](corpus-intake-runbook.md).
