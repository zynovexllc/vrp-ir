# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.8.0](https://github.com/zynovexllc/vrp-ir/compare/v0.7.0...v0.8.0) (2026-06-25)


### Features

* **audit:** advisory standards anchoring (level-aware refs) ([#81](https://github.com/zynovexllc/vrp-ir/issues/81)) ([60dbc75](https://github.com/zynovexllc/vrp-ir/commit/60dbc759abf5a68e469070f02db4a4a1922d5d08)), closes [#70](https://github.com/zynovexllc/vrp-ir/issues/70)
* **audit:** coverage & limitations transparency ([#79](https://github.com/zynovexllc/vrp-ir/issues/79)) ([ad9ccf0](https://github.com/zynovexllc/vrp-ir/commit/ad9ccf00f6570509fe201ec8fa0de33842091047)), closes [#71](https://github.com/zynovexllc/vrp-ir/issues/71)
* **audit:** evidence policy (no source, no claim) ([#78](https://github.com/zynovexllc/vrp-ir/issues/78)) ([701a4df](https://github.com/zynovexllc/vrp-ir/commit/701a4df63d1be02366e80b5e4be35ccd878f6db5)), closes [#68](https://github.com/zynovexllc/vrp-ir/issues/68)


### Documentation

* add ROADMAP and GOVERNANCE ([#63](https://github.com/zynovexllc/vrp-ir/issues/63)) ([e414ba6](https://github.com/zynovexllc/vrp-ir/commit/e414ba61f26398a82bd1575ed411e4cfc12a69dd))

## [0.7.0](https://github.com/zynovexllc/vrp-ir/compare/v0.6.0...v0.7.0) (2026-06-25)


### Features

* **audit:** add NA and unchecked statuses ([#57](https://github.com/zynovexllc/vrp-ir/issues/57)) ([c103cb0](https://github.com/zynovexllc/vrp-ir/commit/c103cb02a5e2a1eb4ac95abde3d5365ae2ad64e0))
* **audit:** flag missing NTP servers ([#58](https://github.com/zynovexllc/vrp-ir/issues/58)) ([414740b](https://github.com/zynovexllc/vrp-ir/commit/414740b0e21ca957a293c1f9f59dddf7e5b7bc24))
* **audit:** flag weak SNMP communities ([#56](https://github.com/zynovexllc/vrp-ir/issues/56)) ([ef7bad8](https://github.com/zynovexllc/vrp-ir/commit/ef7bad8dc3a9a3acb51453af5b3693384ba01802))
* **parser:** parse info-center loghost ([#55](https://github.com/zynovexllc/vrp-ir/issues/55)) ([59a1cdf](https://github.com/zynovexllc/vrp-ir/commit/59a1cdfd28a32ad8323a49ca3bf15847a8adb454))
* **parser:** surface unparsed config lines ([#54](https://github.com/zynovexllc/vrp-ir/issues/54)) ([ff0df69](https://github.com/zynovexllc/vrp-ir/commit/ff0df69a3ef58c77c18ba4d3cb41982677ff7f60))


### Bug Fixes

* **parser:** accept GB18030 Huawei config files ([#49](https://github.com/zynovexllc/vrp-ir/issues/49)) ([a02f48d](https://github.com/zynovexllc/vrp-ir/commit/a02f48da4c8c4fd155a351489c37288dda13dd39))


### Documentation

* add config de-identification workflow ([#59](https://github.com/zynovexllc/vrp-ir/issues/59)) ([48cb72a](https://github.com/zynovexllc/vrp-ir/commit/48cb72a7bddf8f6711d5d05f5748616f3478f1f5))
* add social-preview (OG) card + reproducible generator ([#42](https://github.com/zynovexllc/vrp-ir/issues/42)) ([1e784aa](https://github.com/zynovexllc/vrp-ir/commit/1e784aae6211f4e267c52248881a411b40705e70))
* add terminal demo GIF to README (parse provenance + line-cited audit) ([#36](https://github.com/zynovexllc/vrp-ir/issues/36)) ([356185d](https://github.com/zynovexllc/vrp-ir/commit/356185dbd3cb9e95c793d4ad545445479ce68263))
* document release and PyPI process ([#60](https://github.com/zynovexllc/vrp-ir/issues/60)) ([9adb311](https://github.com/zynovexllc/vrp-ir/commit/9adb311345d9a9059db202364464629af3d41048))
* open-source hygiene (CHANGELOG, SECURITY, CoC, issue/PR templates, README badges) ([#31](https://github.com/zynovexllc/vrp-ir/issues/31)) ([2460e55](https://github.com/zynovexllc/vrp-ir/commit/2460e5514b7b92a60c95f90a1877bf7fb8727108))
* refine commercial positioning (trivy-style open-core CTA + comparison page) ([#35](https://github.com/zynovexllc/vrp-ir/issues/35)) ([54e843e](https://github.com/zynovexllc/vrp-ir/commit/54e843ed02b15bfff7a291cc8505f07e92fd9b0f))
* vrp-ir is live on PyPI (pip install vrp-ir + PyPI badges) ([#34](https://github.com/zynovexllc/vrp-ir/issues/34)) ([4174aee](https://github.com/zynovexllc/vrp-ir/commit/4174aee52106d4104f3bf68c0abe12125bc6fba5))

## [Unreleased]
### Added
- Audit: a **check registry** (`CheckSpec` + `registry()`) that pairs each check
  function with its id, intent, and advisory references in one place. Run order
  and output are unchanged; this is structured metadata, not a declarative DSL.
- Parsing: SNMPv3 `snmp-agent sys-info version` and `snmp-agent usm-user v3`
  (auth/privacy modes, multi-line merge) with `SourceRef`.
- Audit: `FW-SNMP-V3` warns when SNMP v1/v2c is enabled or a v3 user is missing
  authentication or privacy, with advisory standard references.
- CLI: `vrp-ir checks` lists every audit check (id + intent), and
  `vrp-ir explain <CHECK_ID>` prints a check's intent and its advisory
  references — making the catalogue self-describing.
- CLI: `vrp-ir audit --format sarif` and `--format junit` for CI integration —
  SARIF 2.1.0 (GitHub/GitLab code scanning, with the cited source line as the
  result location) and JUnit XML (red/green gating aligned with `--strict`).
- Audit: **advisory standards anchoring** (`StandardRef`). Findings can carry
  level-aware advisory references (等保 三级/四级 alongside CIS-style / Huawei
  hardening) describing the **control domain only** — no fabricated clause
  numbers, `manual_verified: false` pending expert review, and rendered with an
  explicit "not a certification claim" disclaimer. See
  [`docs/standards-mapping.md`](docs/standards-mapping.md).
- Tests: a **golden corpus** of de-identified fixtures with hand-authored
  `*.expected.json` ground truth and a **zero-false-negative** regression gate
  (`tests/test_golden_corpus.py`) — required high-severity findings must keep
  being surfaced and parser coverage must not regress.
- Audit: a **Coverage & limitations** section in the report (Markdown + JSON
  `check_coverage`) that states what the audit asserted vs. left unasserted —
  listing `NA` (not applicable) and `UNCHECKED` (not evaluable) checks so the
  report is explicit about what it did **not** claim.
- Audit: an explicit **evidence policy** ("no source, no claim"). Findings now
  carry `confidence`, `rationale`, and an (advisory) `references` slot; an
  asserting `pass`/`warn`/`fail` finding without a cited source line must document
  its basis (absence/implicit-default findings are marked low-confidence with a
  rationale instead of an unbacked claim).
- Documentation: published a **Now / Next / Later** [`ROADMAP.md`](ROADMAP.md)
  and a [`GOVERNANCE.md`](GOVERNANCE.md) describing project scope, the PR
  acceptance bar, and the open-core boundary with AegisTwin.
- Distribution: published to **PyPI** — `pip install vrp-ir` (via OIDC Trusted Publishing).
- Documentation: de-identification workflow and golden fixture convention for
  safely sharing real-world VRP/USG parser regressions.
- Documentation: maintainer release process, including release-please,
  `RELEASE_PLEASE_TOKEN`, tags and PyPI Trusted Publishing.
- Parser coverage: parsed IR and `vrp-ir audit` reports now surface unparsed
  configuration lines and coverage counts, so unsupported commands are visible
  instead of being silently hidden from acceptance reports.
- Parsing: `info-center loghost` syslog targets, including optional
  `vpn-instance`, now carry `SourceRef` provenance.
- Audit: `FW-SNMP-WEAK-COMMUNITY` warns on plaintext `public` / `private`
  SNMP community strings with line-cited evidence.
- Audit: findings now distinguish `PASS`, `WARN`, `FAIL`, `NA`, and
  `UNCHECKED`; parser coverage gaps now produce an explicit unchecked finding.
- Audit: `FW-NTP-MISSING` fails applicable device configs with no configured
  NTP server and passes with line-cited NTP evidence when one is present.

### Fixed
- Parser: `parse_file(...)` now accepts UTF-8 files with a BOM and GB18030/GBK
  Chinese configuration files instead of failing before parsing starts.

## [0.6.0] - 2026-06-16
### Added
- Management-plane parsing (driven by a real-world config corpus):
  `user-interface` con/vty (`protocol inbound`, inbound ACL, `authentication-mode`,
  privilege level), `ssh server cipher`, and `aaa` local-users — all with `SourceRef`.
- Audit checks (9 → 13): `FW-MGMT-VTY-TELNET`, `FW-MGMT-VTY-NO-ACL`,
  `FW-SSH-WEAK-CIPHER`, `FW-AAA-LOCAL-USER-TELNET`.

## [0.5.0] - 2026-06-16
### Added
- Parsing: `nat-policy` rules, `ip address-set` / `ip service-set` objects,
  `telnet`/`http` management switches — all with `SourceRef`.
- Audit checks (5 → 9): `address-set` dereference in permit-scope,
  `FW-ADDRESS-SET-ANY`, `FW-HRP-INCOMPLETE`, `FW-MGMT-TELNET`, `FW-MGMT-HTTP`.

## [0.4.0] - 2026-06-16
### Added
- `vrp-ir audit`: a security acceptance report (Markdown/JSON) where every finding
  cites the exact source line; seed firewall checks (default-deny, permit-scope,
  rule-logging, zone-iface-unique, HRP).

## [0.3.0] - 2026-06-15
### Added
- Huawei USG firewall objects: `firewall zone`, `security-policy`
  (`rule name` with zones / addresses / services / profiles / action / logging),
  `nat server`, `hrp` — the global open-source gap (Batfish marks VRP unsupported).

## [0.2.0] - 2026-06-15
### Added
- VLANs (incl. batch ranges), VRF (RD/RT), interface enhancements (link-type,
  trunk allow-pass ranges, Eth-Trunk, dot1q subinterfaces, secondary IPv4,
  VRF binding, admin state), ACLs, static routes.

## [0.1.0] - 2026-06-15
### Added
- Initial parser: hostname + interface basics, with the core differentiator —
  every parsed value carries a `SourceRef` (`file:line[:col]`) back to its origin.

[Unreleased]: https://github.com/zynovexllc/vrp-ir/compare/v0.6.0...HEAD
[0.6.0]: https://github.com/zynovexllc/vrp-ir/releases/tag/v0.6.0
[0.5.0]: https://github.com/zynovexllc/vrp-ir/releases/tag/v0.5.0
[0.4.0]: https://github.com/zynovexllc/vrp-ir/releases/tag/v0.4.0
