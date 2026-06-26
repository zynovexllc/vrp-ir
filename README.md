# vrp-ir

[![Tests](https://github.com/zynovexllc/vrp-ir/actions/workflows/tests.yml/badge.svg)](https://github.com/zynovexllc/vrp-ir/actions/workflows/tests.yml)
[![PyPI](https://img.shields.io/pypi/v/vrp-ir.svg)](https://pypi.org/project/vrp-ir/)
[![Python](https://img.shields.io/pypi/pyversions/vrp-ir.svg)](https://pypi.org/project/vrp-ir/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

**Source-traceable structured IR for Huawei VRP configurations.**

<p align="center">
  <img src="https://raw.githubusercontent.com/zynovexllc/vrp-ir/main/docs/demo/demo.gif"
       alt="vrp-ir: parse a Huawei config with field-level provenance, then run a line-cited security audit"
       width="760">
</p>


`vrp-ir` parses an offline Huawei VRP configuration file (`display
current-configuration` output / saved `.cfg`) into a structured, typed model
where **every parsed value carries a `SourceRef` back to the exact file + line**
it came from.

```text
Huawei VRP .cfg  ──►  structured IR  ──►  every field knows its source line
```

> Status: **v0.9 / alpha.** Routing/switching (VLAN, VRF RD/RT, interfaces,
> ACL, static routes) **and USG firewall** (`firewall zone`, `security-policy`,
> `nat-policy`, `nat server`, `ip address-set` / `ip service-set` objects, `hrp`,
> and the **management plane** — `user-interface` con/vty, `ssh server cipher`,
> `aaa` local-users, telnet/http switches, `info-center loghost`, and SNMPv3
> users) parsed with full source provenance, plus a **security acceptance audit**
> (`vrp-ir audit`, 16 checks) whose findings cite the exact config line. Recent
> releases added evidence policy, coverage transparency, advisory standards
> anchoring, SARIF/JUnit output, a check registry, and `vrp-ir checks` /
> `vrp-ir explain`. Roadmap below.

> 💼 **Commercial** — `vrp-ir` is the open core of **AegisTwin**, a Huawei
> security-integration **acceptance** workbench. Need customer-grade acceptance
> reports, a readiness review, or multi-vendor coverage? See
> [Commercial / support](#commercial--support).

## Why this exists (the gap)

The network-automation ecosystem is rich, but a specific combination is missing:

- **Batfish** is excellent, but its source explicitly marks Huawei **VRP as
  `UNSUPPORTED`**.
- **ntc-templates** has ~35 Huawei `display` *show-command* templates, but **no**
  `display current-configuration` (config-file) parser.
- **ciscoconfparse2** is Cisco-centric and only exposes an integer `.linenum`
  per line — not field-level provenance.
- No open-source tool exposes **field → `file:line` provenance** for parsed
  config facts.

`vrp-ir` fills exactly that gap: **Huawei VRP config file → semantic model with
per-field source traceability.** This is what acceptance/audit work needs — when
a value looks wrong, jump straight to the line, don't grep the raw config.

## Install

```bash
pip install vrp-ir
# or, from source:
pip install -e .
```

## Quick start (CLI)

```bash
vrp-ir parse examples/sample-vrp.cfg     # routing / switching
vrp-ir parse examples/sample-usg.cfg     # USG firewall (zones / policy / nat-policy / objects / hrp)
```

```jsonc
{
  "hostname": { "value": "CORE-FW-01", "source": { "file": "...", "line": 2, "col": 8 } },
  "interfaces": [
    {
      "name": { "value": "GigabitEthernet0/0/1", "source": { "line": 9 } },
      "ipv4": [
        { "address": { "value": "10.10.10.1", "source": { "line": 11 } },
          "prefix_length": { "value": 24, "source": { "line": 11 } } }
      ]
    }
  ]
}
```

## Quick start (Python)

```python
from vrp_ir import parse_file

cfg = parse_file("examples/sample-vrp.cfg")
print(cfg.hostname.value)                       # CORE-FW-01
ip = cfg.interfaces[0].ipv4[0]
print(ip.address.value, ip.prefix_length.value) # 10.10.10.1 24
print(ip.address.source)                        # examples/sample-vrp.cfg:11  ← provenance
```

## Security acceptance audit (v0.9)

Turn the source-traceable IR into a **security acceptance report**: each check
is a small test case (intent), and every finding cites the exact config line it
is based on — so a reviewer jumps straight to the offending line.

```bash
vrp-ir audit examples/sample-usg-risky.cfg            # Markdown acceptance report
vrp-ir audit examples/sample-usg.cfg --format json    # machine-readable JSON
vrp-ir audit examples/sample-usg-risky.cfg --format sarif  # SARIF 2.1.0 (code scanning)
vrp-ir audit examples/sample-usg-risky.cfg --format junit  # JUnit XML (CI gating)
vrp-ir audit examples/sample-usg-risky.cfg --strict   # exit 1 if any check fails (CI gate)
```

```text
### ❌ `FW-DEFAULT-DENY` [CRITICAL] — Security-policy default action denies unmatched traffic
Default action is 'permit': all traffic matching no rule is allowed (permit-any).
**Evidence**:
- `examples/sample-usg-risky.cfg:14` — `default action permit`
```

Checks (16): policy default-deny (permit-any); permit-scope (rules not narrowed by
zone/address, **dereferencing `address-set` references** so an object that resolves
to `0.0.0.0/0` is still flagged); permit rules without session logging;
one-interface-per-zone; `address-set` equal to any; HRP enabled; HRP enabled but
heartbeat interface/peer incomplete; **management plane** — Telnet/HTTP enabled
(cleartext), VTY accepting Telnet, VTY without an inbound source ACL, weak SSH
ciphers (CBC/3DES/DES), local AAA users granted the Telnet service, weak SNMP
communities, SNMP not locked to v3 auth+priv, and missing NTP. See a full
rendered report at
[`docs/acceptance-report-example.md`](docs/acceptance-report-example.md).

## Design principles

- **Zero runtime dependencies** in the core — easy to embed.
- **Reuse, don't reinvent.** `vrp-ir` is a thin VRP-config + provenance layer.
  It complements (does not replace) `ntc-templates` (show-command parsing),
  `hier_config` (VRP diff/remediation), `napalm` (live-device collection) and
  `Batfish` (multi-vendor analysis). Topology/analysis layers will integrate
  these rather than rebuild them.
- **Provenance first.** If we can't say where a value came from, we don't
  surface it.

## Roadmap

- **v0.1:** hostname + interface basics with SourceRef. ✅
- **v0.2:** VLANs (batch ranges), VRF (RD/RT), interface enhancements
  (link-type, trunk allow-pass ranges, Eth-Trunk, dot1q subinterfaces, secondary
  IPv4, VRF binding), ACLs, static routes. ✅
- **v0.3:** Huawei **USG firewall** objects — `firewall zone`,
  `security-policy` (`rule name` with zones / addresses / services / profiles /
  action / logging), `nat server`, `hrp` (the global OSS gap; Batfish drops VRP
  entirely). ✅
- **v0.4:** security **acceptance audit** — test-case schema
  (`testCase ↔ intent ↔ evidenceRef`) + a Markdown/JSON report generator;
  `vrp-ir audit` with seed firewall checks, each citing its source line. ✅
- **v0.5:** `nat-policy` blocks, `ip address-set` / `ip service-set` objects,
  telnet/http management switches; audit at 9 checks — `address-set` dereference
  in permit-scope, `address-set`-equals-any, HRP consistency, cleartext
  management (Telnet / HTTP). ✅
- **v0.6:** **management-plane access baseline** (driven by real-world
  config corpus) — `user-interface` con/vty (protocol inbound / inbound ACL /
  auth mode), `ssh server cipher`, `aaa` local-users; audit grows to **13
  checks** (VTY-accepts-Telnet, VTY-no-ACL, weak-SSH-cipher, AAA-user-Telnet). ✅
- **v0.7:** GB18030/GBK config support; parser **coverage transparency**
  (unparsed lines surfaced in the audit); `info-center loghost`; audit status
  semantics `PASS / WARN / FAIL / NA / UNCHECKED`; checks for weak SNMP community
  and missing NTP. ✅
- **v0.8:** **Trust foundation** — evidence policy ("no source, no claim"),
  richer report + coverage transparency, de-identified golden corpus with a
  zero-false-negative gate, and advisory standards anchoring (incl. 等保 Level
  3 / Level 4 advisory references). ✅
- **v0.9:** **Evidence interop** — SARIF / JUnit output, `vrp-ir checks`,
  `vrp-ir explain <CHECK_ID>`, a structured check registry, and SNMPv3
  parsing + audit. ✅

### What's next

The forward-looking roadmap is maintained as **Now / Next / Later** (no fixed
dates) in **[ROADMAP.md](ROADMAP.md)**. In short: the recent `v0.8` / `v0.9`
releases delivered the trust-foundation and evidence-interop batches; the next
active work is corpus-driven parser hardening / coverage breadth, followed by a
1.0 stability contract that freezes the IR schema and check-id catalogue.

See **[GOVERNANCE.md](GOVERNANCE.md)** for how the project is run and the
open-core boundary with AegisTwin.

## Commercial / support

`vrp-ir` is free and open source (Apache-2.0), and it stays that way.

It is the **open core of AegisTwin** — an acceptance workbench for carrier and
data-center security integration (HLD/LLD → traceable topology → acceptance
advisor → evidence chain → sign-off report). If you liked `vrp-ir`, AegisTwin
**builds on top of it** for teams that deliver acceptance at scale: Huawei
security-device coverage (USG / WAF / AntiDDoS / 4A), HLD/LLD → traceable
acceptance test cases, and customer-grade, auditable reports (incl. MLPS /
carrier formats).

See the **[open-source vs. commercial comparison](docs/commercial.md)**.

**Talk to us** about a paid workflow review or a design-partner pilot →
**support@zynovexllc.com**.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Real (de-identified) VRP config snippets
that we parse incorrectly make the **best** issues; follow the
[de-identification guide](docs/de-identifying-configs.md) before sharing any
snippet publicly.

## License

[Apache-2.0](LICENSE).
