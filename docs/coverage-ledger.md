# Coverage Ledger

This ledger is a maintainer-facing map of what the current repo covers and what
still needs more evidence before it should be treated as shipped scope.

It is not a marketing checklist. It is meant to support roadmap decisions and
future fixture intake.

## 1. What is represented in the shipped repo

### Parsing surface represented in tests/examples

- Routing/switching baseline:
  - hostname
  - interfaces
  - VLANs
  - VRFs / RD / RT
  - ACLs
  - static routes
- USG security objects and policy:
  - `firewall zone`
  - `security-policy`
  - `nat-policy`
  - `nat server`
  - `ip address-set`
  - `ip service-set`
  - `hrp`
- Management plane:
  - `user-interface` con/vty
  - inbound protocol and ACL restrictions
  - `ssh server cipher`
  - `aaa local-user service-type`
  - `local-aaa-user password policy` views
  - telnet/http switches
- Additional operational/security inputs:
  - `info-center loghost`
  - NTP server lines
  - SNMP communities
  - SNMPv3 `usm-user`
- Parser coverage accounting:
  - unparsed-line surfacing
  - parser coverage percentage

### Audit surface represented in the registry

Current registered checks:

- `FW-DEFAULT-DENY`
- `FW-PERMIT-SCOPE`
- `FW-RULE-LOGGING`
- `FW-ZONE-IFACE-UNIQUE`
- `FW-ADDRESS-SET-ANY`
- `HRP-ENABLED`
- `FW-HRP-INCOMPLETE`
- `FW-MGMT-TELNET`
- `FW-MGMT-HTTP`
- `FW-MGMT-VTY-TELNET`
- `FW-MGMT-VTY-NO-ACL`
- `FW-SSH-WEAK-CIPHER`
- `FW-AAA-LOCAL-USER-TELNET`
- `FW-AAA-PASSWORD-EXPIRE-DISABLED`
- `FW-AAA-PASSWORD-ALERT-DISABLED`
- `FW-AAA-PASSWORD-INITIAL-CHANGE-DISABLED`
- `FW-AAA-PASSWORD-HISTORY-DISABLED`
- `FW-SNMP-WEAK-COMMUNITY`
- `FW-SNMP-V3`
- `FW-NTP-MISSING`

Parser coverage also surfaces `PARSER-UNCHECKED-LINES` through the CLI/reporting
path.

## 2. Current golden fixture families

- `deidentified-golden-vrp` — routing/switching
- `hardened-usg` — hardened firewall
- `mgmt-plane-cn` — management plane / localized text
- `objects-nat-usg` — object-heavy firewall + NAT
- `risky-edge-usg` — risky edge/firewall posture

## 3. What is not yet a shipped commitment

These items appear in repo planning (`ROADMAP.md`, open issues, or both), but
are not yet something maintainers should describe as delivered:

- `vsys`
- deferred Huawei password-policy families outside the shipped
  `local-aaa-user password policy` view family
- interface/routing authentication
- field-level config diff with `SourceRef`
- 1.0 schema/check-id stability contract
- parser-hardening refactor

## 4. Evidence-blocked areas

The following should be treated as evidence-blocked rather than
architecture-led:

- parser hardening across recurring view/dispatch patterns
- broader management-plane hardening beyond the current checks
- additional vendor-specific or deployment-specific control interpretations
- any stability-contract decision that depends on more observed command models
  or real configs

Evidence for these areas may come from:

- public primary sources,
- self-built lab corpus grounded in vendor syntax,
- zero-export field validation,
- or de-identified corpus fixtures

What still remains invalid is architecture-led expansion without one of those
inputs.

## 5. Intake rule

When choosing the next implementation batch, prefer a batch that satisfies at
least one of these:

1. a documented command family exposes a stable syntax boundary and explicit
   offline semantic,
2. a new de-identified fixture exposes a parser blind spot,
3. a current finding is evidence-poor or misleading,
4. a downstream CI workflow needs a small extension of already-shipped output.

If none of those is true, the batch is probably speculative and should wait.
