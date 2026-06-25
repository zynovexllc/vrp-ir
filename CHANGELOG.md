# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added
- Distribution: published to **PyPI** — `pip install vrp-ir` (via OIDC Trusted Publishing).
- Parser coverage: parsed IR and `vrp-ir audit` reports now surface unparsed
  configuration lines and coverage counts, so unsupported commands are visible
  instead of being silently hidden from acceptance reports.
- Parsing: `info-center loghost` syslog targets, including optional
  `vpn-instance`, now carry `SourceRef` provenance.
- Audit: `FW-SNMP-WEAK-COMMUNITY` warns on plaintext `public` / `private`
  SNMP community strings with line-cited evidence.

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
