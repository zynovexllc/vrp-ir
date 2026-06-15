# vrp-ir v0.1 Specification

> Status: implemented (alpha). This document defines the v0.1 scope, data model,
> parsing rules, and design constraints. It is the contract reviewers/contributors
> should check against. Breadth grows in later milestones (see Roadmap in README).

## 1. Goal & non-goals

**Goal.** Parse an offline Huawei VRP configuration file into a structured,
typed Intermediate Representation (IR) where **every surfaced value carries a
`SourceRef` (file + line [+ col + raw])** back to its origin.

**Non-goals (v0.1).**
- Not a live-device collector (use `napalm` / `napalm-huawei-vrp`).
- Not a multi-vendor analyzer (use `Batfish`).
- Not a config diff/remediation tool (use `hier_config`).
- Not a show-command parser (use `ntc-templates`).
- No topology, no analysis, no security-device coverage yet.

**Design constraint.** Zero runtime dependencies in the core package; reuse the
ecosystem (above) in *later* layers rather than rebuild it.

## 2. The differentiator: SourceRef

`SourceRef(file, line, col=None, raw=None)` — attached to every parsed value via
`Traced[T](value, source)`. No existing OSS network parser exposes field-level
provenance; this is the reason `vrp-ir` exists.

Invariant (tested): for any `Traced` value `t`, the text at
`t.source.file:t.source.line` actually contains the token that produced
`t.value`.

## 3. v0.1 IR scope

| Construct | Fields (each `Traced`) | VRP source |
|---|---|---|
| `VrpConfig.hostname` | name | `sysname <name>` |
| `Interface` | name, source | `interface <name>` |
| `Interface.description` | text | `description <text>` |
| `Interface.ipv4[]` | address, prefix_length | `ip address <addr> <mask\|prefixlen>` |
| `Interface.shutdown` | bool(True) | `shutdown` |
| `Interface.access_vlan` | int | `port default vlan <id>` |
| `Interface.vpn_instance` | name | `ip binding vpn-instance <name>` |

## 4. Parsing rules

1. Line-based, 1-based line numbers; raw line text retained on each `SourceRef`.
2. A line is **top-level** if it has no leading whitespace; **sub-command** if
   indented.
3. `#` separator lines and blank lines **close** the current interface stanza.
4. Any top-level command closes the current interface stanza.
5. `interface <name>` opens a stanza; subsequent indented sub-commands attach to
   it until rule 3/4 closes it.
6. `ip address <addr> <mask>`: `<mask>` may be a dotted mask (`255.255.255.0`)
   or a prefix int (`24`). Dotted masks must be contiguous (run of 1s then 0s);
   invalid masks are **ignored** (no partial/garbage facts surfaced).
7. Unknown sub-commands are ignored in v0.1 (no error), but must not crash.

## 5. Output

`VrpConfig.to_dict()` returns a JSON-serialisable structure where every value is
`{"value": ..., "source": {"file", "line", "col"}}`. The CLI `vrp-ir parse
<file>` prints it.

## 6. Quality gates

- `python -m unittest discover -s tests` is green (CI enforces it).
- Provenance invariant (§2) covered by a test.
- New parsed constructs require: a sample snippet in `examples/`, a positive
  test, and a SourceRef assertion.

## 7. Roadmap hooks (not in v0.1)

- v0.2: LLDP-neighbor ingestion (via `ntc-templates`) → L2/L3 topology; VRF/VLAN
  objects.
- v0.3: acceptance test-case schema (`testCase ↔ intentRef ↔ evidenceRef`) +
  report generator.
- Later: Huawei security devices (USG/WAF/AntiDDoS/4A).
