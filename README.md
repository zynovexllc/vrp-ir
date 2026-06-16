# vrp-ir

**Source-traceable structured IR for Huawei VRP configurations.**

`vrp-ir` parses an offline Huawei VRP configuration file (`display
current-configuration` output / saved `.cfg`) into a structured, typed model
where **every parsed value carries a `SourceRef` back to the exact file + line**
it came from.

```text
Huawei VRP .cfg  ──►  structured IR  ──►  every field knows its source line
```

> Status: **v0.5 / alpha.** Routing/switching (VLAN, VRF RD/RT, interfaces,
> ACL, static routes) **and USG firewall** (`firewall zone`, `security-policy`,
> `nat-policy`, `nat server`, `ip address-set` / `ip service-set` objects, `hrp`,
> telnet/http management switches) parsed with full source provenance, plus a
> **security acceptance audit** (`vrp-ir audit`, 9 checks) whose findings cite the
> exact config line. Roadmap below.

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
pip install vrp-ir            # once published to PyPI
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

## Security acceptance audit (v0.5)

Turn the source-traceable IR into a **security acceptance report**: each check
is a small test case (intent), and every finding cites the exact config line it
is based on — so a reviewer jumps straight to the offending line.

```bash
vrp-ir audit examples/sample-usg-risky.cfg            # Markdown acceptance report
vrp-ir audit examples/sample-usg.cfg --format json    # machine-readable JSON
vrp-ir audit examples/sample-usg-risky.cfg --strict   # exit 1 if any check fails (CI gate)
```

```text
### ❌ `FW-DEFAULT-DENY` [CRITICAL] — Security-policy default action denies unmatched traffic
Default action is 'permit': all traffic matching no rule is allowed (permit-any).
**Evidence**:
- `examples/sample-usg-risky.cfg:14` — `default action permit`
```

Checks (9): policy default-deny (permit-any); permit-scope (rules not narrowed by
zone/address, **dereferencing `address-set` references** so an object that resolves
to `0.0.0.0/0` is still flagged); permit rules without session logging;
one-interface-per-zone; `address-set` equal to any; HRP enabled; HRP enabled but
heartbeat interface/peer incomplete; Telnet management (cleartext); HTTP management
(cleartext). See a full rendered report at
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
- **v0.5 (now):** `nat-policy` blocks, `ip address-set` / `ip service-set`
  objects, telnet/http management switches; audit grows to **9 checks** —
  `address-set` dereference in permit-scope, `address-set`-equals-any, HRP
  consistency, and cleartext management (Telnet / HTTP). ✅
- **v0.5.x (next):** more management-plane baselines (SNMP community, AAA / local
  users, NTP / Syslog presence), NAT correctness, `vsys`.
- Later: Huawei security-device coverage (USG / WAF / AntiDDoS / 4A).

## Commercial / support

`vrp-ir` is free and open source (Apache-2.0). It is the open foundation of
**AegisTwin** — a carrier/data-center security-integration **acceptance**
workbench (HLD/LLD → traceable topology → acceptance advisor → evidence chain →
sign-off report). If you need:

- Huawei **security-device** acceptance (USG/WAF/AntiDDoS/4A),
- HLD/LLD → traceable acceptance test cases,
- customer-grade, auditable acceptance reports (incl. MLPS / carrier formats),

→ open an issue tagged `commercial`, or reach out about a **paid workflow
review / design-partner pilot**.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Real (de-identified) VRP config snippets
that we parse incorrectly make the **best** issues.

## License

[Apache-2.0](LICENSE).
