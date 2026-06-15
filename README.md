# vrp-ir

**Source-traceable structured IR for Huawei VRP configurations.**

`vrp-ir` parses an offline Huawei VRP configuration file (`display
current-configuration` output / saved `.cfg`) into a structured, typed model
where **every parsed value carries a `SourceRef` back to the exact file + line**
it came from.

```text
Huawei VRP .cfg  ──►  structured IR  ──►  every field knows its source line
```

> Status: **v0.1 / alpha.** Narrow but real: hostname + interface basics
> (description, IPv4, admin state, access VLAN, VRF binding), each with full
> provenance. Roadmap below.

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
vrp-ir parse examples/sample-vrp.cfg
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

- **v0.1 (now):** hostname + interface basics with SourceRef. ✅
- **v0.2:** L2/L3 topology view (interfaces + LLDP neighbors via `ntc-templates`),
  VRF/VLAN objects.
- **v0.3:** acceptance test-case schema (`testCase ↔ intentRef ↔ evidenceRef`)
  + a report generator (structured results → CN/EN acceptance report).
- Later: Huawei security-device coverage (USG / WAF / AntiDDoS / 4A).

## Commercial / support

`vrp-ir` is free and open source (Apache-2.0). It is the open foundation of
**AegisTwin** — a carrier/data-center security-integration **acceptance**
workbench (HLD/LLD → traceable topology → acceptance advisor → evidence chain →
sign-off report). If you need:

- Huawei **security-device** acceptance (USG/WAF/AntiDDoS/4A),
- HLD/LLD → traceable acceptance test cases,
- customer-grade, auditable acceptance reports (中文 / 等保 / 运营商),

→ open an issue tagged `commercial`, or reach out about a **paid workflow
review / design-partner pilot**.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Real (de-identified) VRP config snippets
that we parse incorrectly make the **best** issues.

## License

[Apache-2.0](LICENSE).

---

<a name="zh"></a>

# vrp-ir(中文)

**面向华为 VRP 配置的「可逐字段溯源」结构化解析器。**

把离线华为 VRP 配置文件(`display current-configuration` / 保存的 `.cfg`)解析成
结构化模型,且**每个解析出的值都带 `SourceRef`,可溯源到原始 file:line**。

## 为什么做(空白)

- **Batfish** 很强,但源码明确把华为 **VRP 标为 `UNSUPPORTED`**。
- **ntc-templates** 有 ~35 个华为 `display` **show 命令**模板,但**没有**
  `display current-configuration`(配置文件)解析。
- **ciscoconfparse2** 偏 Cisco,且只有行号整数,不是字段级溯源。
- 整个生态**没有**工具提供"字段 → file:line"的溯源。

`vrp-ir` 正好补这个空白——**华为 VRP 配置文件 → 语义模型 + 逐字段溯源**。这正是
验收/审计场景需要的:值不对时直接跳到原始行,而不是人肉翻配置。

## 不重复造轮子

`vrp-ir` 只做"VRP 配置 + 溯源"这一薄层,**复用**而非重建 `ntc-templates`
(show 解析)/ `hier_config`(VRP diff)/ `napalm`(连真机)/ `Batfish`(多厂商分析)。
后续拓扑/分析层将**集成**这些工具。

## 商业 / 支持

`vrp-ir` 是 **AegisTwin**(运营商/数据中心安全集成**验收**工作台)的开源地基。
需要华为安全设备(USG/WAF/AntiDDoS/4A)验收、HLD/LLD → 可溯源用例、客户级可签收
验收报告(中文/等保/运营商)?提一个 `commercial` issue,或聊一次**付费工作流评审 /
设计伙伴试点**。
