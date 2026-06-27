# vrp-ir (open source) vs. AegisTwin (commercial)

`vrp-ir` is proudly the **open core** of [AegisTwin](https://github.com/zynovexllc).
If you liked `vrp-ir`, AegisTwin builds on top of it to deliver full
security-integration **acceptance** at scale — for carriers, data centers, and
the integrators who hand over to them.

This page is a high-level comparison between **vrp-ir (OSS)** and the **AegisTwin**
commercial product. The open-source core is fully usable on its own; AegisTwin
adds the workflow, coverage, and reporting that paid acceptance delivery needs.

> Want a workflow review or a design-partner pilot?
> **[support@zynovexllc.com](mailto:support@zynovexllc.com)**

## Parsing & coverage

| Capability | vrp-ir (OSS) | AegisTwin (commercial) |
| --- | --- | --- |
| Huawei VRP/USG config parsing | ✅ routing/switching + USG firewall, with field-level `SourceRef` | ✅ Same engine, plus extended device families |
| Security-device coverage | USG firewall objects | In addition: WAF / AntiDDoS / 4A |
| Multi-vendor | — | On the roadmap for commercial engagements |
| Input | Offline config file (CLI) | Config + HLD/LLD design documents |

## Acceptance & audit

| Capability | vrp-ir (OSS) | AegisTwin (commercial) |
| --- | --- | --- |
| Security checks | ✅ 21 built-in checks, each citing the exact config line | ✅ Plus customer/standard baselines |
| HLD/LLD → test cases | — | Traceable acceptance test cases derived from the design |
| Evidence chain | Per-finding `file:line` evidence | End-to-end: design → topology → finding → sign-off |
| Standard mapping | — | MLPS / carrier acceptance formats, compliance matrix |

## Reporting & delivery

| Capability | vrp-ir (OSS) | AegisTwin (commercial) |
| --- | --- | --- |
| Output | Markdown / JSON / SARIF / JUnit | Customer-grade, auditable sign-off reports |
| Interface | CLI | CLI + acceptance workbench |
| CI gating | ✅ `--strict` exits non-zero on failure | ✅ Plus managed acceptance pipelines |

## Support

| | vrp-ir (OSS) | AegisTwin (commercial) |
| --- | --- | --- |
| Support | Community, best-effort (GitHub issues) | Expert review, onboarding, and SLA-backed support |
| Engagement | Self-serve | Paid workflow review / design-partner pilot |

---

The open-source project will always remain free under Apache-2.0. AegisTwin is for
teams that want acceptance delivered as a product and a service rather than
assembled by hand.

→ **[support@zynovexllc.com](mailto:support@zynovexllc.com)**
