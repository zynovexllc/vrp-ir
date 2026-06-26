# vrp-ir Evolution Plan (2026-06)

This document turns the current repo state, backlog, and adjacent ecosystem
facts into a practical evolution plan for `vrp-ir`.

It distinguishes between:

- **Facts**: verifiable statements about the current repo, releases, issues, and
  adjacent tooling ecosystem.
- **Recommendations**: decisions inferred from those facts.

It is intentionally written as a maintainer planning document, not as external
marketing copy.

## 1. Executive summary

### Fact

`vrp-ir` is already a real project, not a prototype sketch:

- Current package version is **`0.9.0`**.
- The repo currently ships **16 registered acceptance checks** plus the parser
  coverage sentinel `PARSER-UNCHECKED-LINES` in the CLI catalogue.
- The current gate is **240 unit tests + `ruff`**.
- Releases **`v0.7.0`**, **`v0.8.0`**, and **`v0.9.0`** were all published on
  **2026-06-25**.

### Recommendation

The right next step is **not** a speculative parser rewrite. The right next step
is to consolidate `vrp-ir` around its strongest proven wedge:

1. **Source-traceable offline Huawei VRP/USG acceptance evidence**
2. **CI-consumable audit output**
3. **Corpus-driven coverage expansion**
4. **A disciplined open-core boundary with AegisTwin**

In practice, that means:

- Do **not** force `#74` right now.
- Treat **real de-identified corpus growth** as the highest-leverage input.
- Push toward **1.0 as a stability contract**, not as a feature-count race.

## 2. Current factual baseline

### Repo and release state

Facts observed from the current checkout and repo metadata on 2026-06-26:

- Package version: `0.9.0`
- Acceptance registry size: `16`
- CLI catalogue size: `17` entries
  - The 17th entry is `PARSER-UNCHECKED-LINES`, which is a parser coverage
    sentinel rather than a normal security policy check.
- Test gate: `240` unit tests passing
- Lint gate: `ruff check .` passing
- Latest releases present: `v0.4.0` through `v0.9.0`

Current open issues:

- `#65` Epic: Trust foundation (evidence correctness)
- `#66` Epic: Advisory standards anchoring
- `#67` Epic: Evidence interop & parser maturity
- `#74` Parser hardening: view state machine + table-driven dispatch
- `#75` 1.0 stability contract

### Capability baseline

As of `0.9.0`, the repo already includes:

- Offline VRP/USG config parsing with field-level `SourceRef`
- Advisory acceptance auditing with line-cited findings
- Evidence policy (`no source, no claim`)
- Coverage transparency (`CHECKED / NA / UNCHECKED`)
- Golden de-identified corpus + zero-false-negative regression gate
- Advisory standards anchoring
- SARIF output
- JUnit output
- Check registry
- `vrp-ir checks`
- `vrp-ir explain <CHECK_ID>`
- SNMPv3 parsing and audit

### Backlog state mismatch

There is an issue hygiene mismatch:

- `#65` and `#66` are still open, but their core deliverables are already in the
  shipped `0.8.0` / `0.9.0` line.
- `#67` is still a valid umbrella, but part of its original scope is already
  done.
- `#74` remains open, but its own acceptance criteria require a corpus-driven,
  byte-for-byte-safe refactor. The current repo does not yet show a new corpus
  batch justifying that refactor.
- `#75` is conceptually correct, but belongs to a later stabilization phase.

## 3. Adjacent ecosystem facts

This section matters because roadmap quality depends on what should be built
inside `vrp-ir` versus what should remain outside it.

### 3.1 Batfish is not the substitute for this niche

Facts:

- Batfish publishes a supported-device list, and the current published page does
  **not mention Huawei**.
- There is also a public Batfish issue requesting Huawei support.

Recommendation:

`vrp-ir` should continue to assume that **offline Huawei VRP/USG acceptance with
field-level provenance is not being commoditized by Batfish today**.

Implication:

- `vrp-ir` should not try to become Batfish.
- It should stay focused on the narrower problem it already solves well:
  **source-traceable config facts and acceptance evidence for Huawei VRP/USG**.

### 3.2 NTC Templates is adjacent, not a replacement

Facts:

- `ntc-templates` is a TextFSM template repository for parsing network-device
  CLI output.
- A repo code search on 2026-06-26 did not return an obvious
  `display current-configuration` template in `networktocode/ntc-templates`.

Recommendation:

Treat `ntc-templates` as complementary for **show-command parsing**, not as a
reason to de-prioritize `vrp-ir`'s saved-config parsing model.

Implication:

- `vrp-ir`'s wedge is still valid.
- Reuse opportunities should be integration-layer opportunities, not a mandate
  to replace `vrp-ir`'s internal parser model.

### 3.3 ciscoconfparse2 and hier_config solve different layers

Facts:

- `ciscoconfparse2` describes itself as an advanced grep/diff tool for network
  configuration files.
- `hier_config` focuses on comparing running vs intended configuration and
  generating remediation commands.

Recommendation:

Do **not** drift `vrp-ir` toward becoming either:

- a generic grep/query library, or
- a remediation engine.

Implication:

- `vrp-ir` should remain the **evidence-grade parse + audit layer**.
- Diff/remediation may become downstream integrations later, but should not be
  allowed to dominate the core roadmap now.

### 3.4 NAPALM and pyATS/Genie support integration stories, not core scope

Facts:

- NAPALM documents supported drivers and the Huawei VRP community driver exists.
- pyATS positions itself as a network **test automation** platform.

Recommendation:

Treat live collection and test-harness orchestration as **integration concerns**,
not as the core of `vrp-ir`.

Implication:

- Live device collection remains out of scope for the open-source core.
- `vrp-ir` should consume offline config text and export machine-readable
  evidence to CI/tooling, not become a device-operations framework.

### 3.5 SARIF and JUnit are the right interoperability outputs

Facts:

- GitHub code scanning supports SARIF and documents required fields such as
  `ruleId`, location data, and `partialFingerprints`.
- GitLab test reporting accepts **JUnit XML** and documents parser constraints,
  including duplicate-name handling.

Recommendation:

The current choice to support **SARIF + JUnit** is strategically correct. This
is a durable interop path, not feature fluff.

Implication:

- Keep investing in CI-grade outputs.
- Do not spend near-term time on lower-value export formats unless they unlock a
  real downstream user workflow.

## 4. Strategic conclusion

### Fact-based identity

The strongest defensible identity for `vrp-ir` is:

> **An evidence-grade, source-traceable offline acceptance core for Huawei
> VRP/USG configurations.**

This identity is stronger than any of the following alternatives:

- generic network parser
- generic network compliance framework
- remediation engine
- multi-vendor abstraction layer
- live automation framework

### Recommendation

The roadmap should optimize for the following order:

1. **Trustworthiness of evidence**
2. **Coverage breadth driven by real corpus**
3. **Stable contracts for downstream consumers**
4. **Only then optional ecosystem integrations**

That order is already implied by the current repo doctrine. The gap is not the
direction; the gap is backlog hygiene and phase discipline.

## 5. Recommended evolution plan

## Phase A: Truth, hygiene, and roadmap cleanup

### Goal

Make the repo's public and internal planning surfaces accurately reflect the
project that now exists.

### Recommended work

1. Close or explicitly retitle stale epics:
   - `#65` should be closed with a shipped-summary note.
   - `#66` should be closed or reduced to a follow-up issue if only manual
     verification backlog remains.
2. Keep `#67` as the umbrella for remaining "interop + maturity" work, but edit
   it to distinguish **done**, **blocked**, and **later** items.
3. Mark `#74` as **blocked by new real de-identified corpus**, not "ready to
   code now".
4. Keep `#75` as later-stage work.
5. Eliminate public docs drift:
   - README capability summary
   - commercial comparison page
   - any check-count references that still say 13

### Why this phase is necessary

Because a trust-oriented project cannot afford internal roadmap fiction.

## Phase B: Corpus acquisition as the primary growth engine

### Goal

Expand confidence and coverage using real de-identified configs rather than
speculative parser architecture work.

### Recommended work

1. Treat corpus intake as a first-class product input:
   - more de-identified VRP/USG fixtures
   - explicit fixture provenance rules
   - acceptance expectations checked into git
2. Add a fixture taxonomy:
   - enterprise routing/switching
   - USG security edge
   - management-heavy configs
   - localization/encoding variants
   - HA/HRP variants
3. Add a simple coverage ledger documenting:
   - config families seen
   - commands intentionally unsupported
   - checks blocked by missing corpus

### Why this phase is necessary

Because `#74` and most meaningful parser-expansion work are only rational if a
corpus exposes real breakpoints.

## Phase C: Coverage expansion in small evidence-backed batches

### Goal

Keep widening useful acceptance coverage without destabilizing the trust model.

### Recommended selection rule

A new parser/check batch should be accepted only if at least one of these is
true:

1. a real de-identified config exposes a parsing blind spot,
2. a current check is producing misleading evidence quality,
3. the addition closes a concrete acceptance workflow gap.

### Recommended near-term candidate areas

These are promising, but **only when corpus-backed**:

- `vsys`
- `aaa` password policy
- interface/routing authentication
- more management-plane hardening
- config diff with `SourceRef`

### Non-recommendation

Do **not** start with a big parser rewrite.

Reason:

- The current parser already supports a meaningful shipped surface.
- A speculative rewrite creates regression risk before it creates user value.

## Phase D: 1.0 stability contract

### Goal

Make `1.0` mean "safe to build against", not "feature complete forever".

### Recommended prerequisites

1. Versioned JSON Schema for parse output and audit output
2. Published check catalogue
3. Deprecation policy
4. Evidence that the current check IDs and report fields have stabilized across
   multiple releases
5. Removal of externally stale `alpha` language only when the contract is real

### Why this phase should wait

Because freezing a contract too early creates drag, while freezing it too late
harms downstream adoption. The right trigger is not time; it is **output
stability**.

## Phase E: Integration layer, not core expansion

### Goal

Make `vrp-ir` easier to adopt without bloating the core.

### Recommended work later

- Better SARIF/GitHub code scanning guidance
- Better GitLab/JUnit CI examples
- Integration examples with collection/remediation layers
- Reference workflows that pair `vrp-ir` with adjacent tooling

### Non-recommendation

Do not make live collection, remediation, multi-vendor abstraction, or deep
certification matrices part of the OSS core roadmap.

## 6. Explicit backlog decisions

### `#65` Trust foundation

Recommendation: **close** after adding a short shipped-summary comment.

Reason:

Its core scope is already reflected in `0.8.0`.

### `#66` Standards anchoring

Recommendation: **close or narrow**.

Reason:

The structure is shipped. Remaining work appears to be about cautious expansion
and manual verification depth, not the original epic's enabling work.

### `#67` Evidence interop & parser maturity

Recommendation: **keep open**, but update the body.

Reason:

It still correctly owns:

- parser hardening policy
- coverage breadth
- 1.0 contract work

But it should explicitly say which original items are already delivered.

### `#74` Parser hardening

Recommendation: **do not execute now**. Reclassify as blocked by corpus.

Reason:

- The issue itself says corpus-driven.
- The project doctrine says no speculative rewrites.
- Current repo facts do not show a new corpus batch justifying it.

### `#75` 1.0 stability contract

Recommendation: **keep open as a later-stage target**.

Reason:

It is strategically correct, but it is a contract phase, not the next coding
batch.

## 7. Suggested operating rules for the next 3-5 PRs

1. Every PR should answer: **what user-trust or workflow problem does this
   solve?**
2. No parser-architecture refactor without a corpus-driven trigger.
3. No new output format unless it unlocks a concrete consumer workflow.
4. No feature that weakens the open-core boundary.
5. Every behavior change must land with tests that preserve `SourceRef` and
   evidence quality.

## 8. What success looks like

The next meaningful success state is not "more features". It is:

- a cleaned-up backlog,
- a larger and better-structured de-identified corpus,
- several more coverage batches justified by real configs,
- a clearer division between OSS mechanism and commercial content,
- and a visible path to `1.0` contract hardening.

That would make the roadmap credible to:

- maintainers,
- contributors,
- CI users,
- and future commercial adopters of AegisTwin.

## 9. Evidence basis

### Repo facts

Derived from the current checkout and GitHub metadata on 2026-06-26.

### External references

1. Batfish supported devices list:
   `https://batfish.readthedocs.io/en/stable/supported_devices.html`
2. Batfish Huawei support request:
   `https://github.com/batfish/batfish/issues/8707`
3. NTC Templates repo:
   `https://github.com/networktocode/ntc-templates`
4. ciscoconfparse2 package/docs:
   `https://pypi.org/project/ciscoconfparse2/`
5. hier_config docs:
   `https://hier-config.readthedocs.io/`
6. GitHub SARIF support:
   `https://docs.github.com/en/code-security/reference/code-scanning/sarif-files/sarif-support`
7. GitLab JUnit reports:
   `https://docs.gitlab.com/ci/testing/unit_test_reports/`
8. pyATS docs:
   `https://developer.cisco.com/docs/pyats/`
9. NAPALM support docs:
   `https://napalm.readthedocs.io/en/latest/support/index.html`
10. Huawei VRP NAPALM community driver:
    `https://github.com/napalm-automation-community/napalm-huawei-vrp`
