"""Security acceptance checks over a parsed :class:`~vrp_ir.models.VrpConfig`.

This is the layer that turns the source-traceable IR into a security
*acceptance report*. Each check is a small "test case" with a stable id and an
intent, and every :class:`Finding` cites the exact source lines it is based on
(the *evidenceRef*). Because the IR carries field-level provenance, a reviewer
can jump straight from a finding to the offending configuration line.

Zero runtime dependencies; bilingual (zh / en) rendering.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List

from .models import VrpConfig
from .sourceref import SourceRef

# Severity ranked most -> least serious.
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
_STATUS_ORDER = {"fail": 0, "warn": 1, "pass": 2}

# Stable check catalogue: id -> bilingual intent ("what is verified").
CHECKS_META: Dict[str, Dict[str, str]] = {
    "FW-DEFAULT-DENY": {
        "zh": "安全策略默认动作应为 deny(拒绝未匹配流量)",
        "en": "Security-policy default action denies unmatched traffic"},
    "FW-PERMIT-SCOPE": {
        "zh": "permit 规则的源与目的应被区域或地址收敛",
        "en": "Permit rules are narrowed (by zone or address) on both sides"},
    "FW-RULE-LOGGING": {
        "zh": "permit 规则应开启会话日志(session logging)",
        "en": "Permit rules enable session logging"},
    "FW-ZONE-IFACE-UNIQUE": {
        "zh": "每个接口应仅绑定到一个安全区域",
        "en": "Each interface is bound to exactly one zone"},
    "HRP-ENABLED": {
        "zh": "若配置了 HRP 双机热备则应启用",
        "en": "HRP is enabled when configured"},
}


@dataclass
class Finding:
    """One acceptance test-case result, citing its source evidence."""
    check_id: str
    severity: str            # critical | high | medium | low | info
    status: str              # pass | fail | warn
    detail: Dict[str, str]   # {"zh": ..., "en": ...}
    evidence: List[SourceRef] = field(default_factory=list)

    def title(self, lang: str = "zh") -> str:
        return CHECKS_META.get(self.check_id, {}).get(lang, self.check_id)


@dataclass
class AcceptanceReport:
    source_file: str
    findings: List[Finding] = field(default_factory=list)

    @property
    def result(self) -> str:
        if any(f.status == "fail" for f in self.findings):
            return "fail"
        if any(f.status == "warn" for f in self.findings):
            return "warn"
        return "pass"

    def counts(self) -> Dict[str, int]:
        c = {"pass": 0, "warn": 0, "fail": 0}
        for f in self.findings:
            c[f.status] = c.get(f.status, 0) + 1
        return c

    def to_dict(self) -> dict:
        return {
            "source_file": self.source_file,
            "result": self.result,
            "counts": self.counts(),
            "findings": [{
                "check_id": f.check_id,
                "severity": f.severity,
                "status": f.status,
                "title": {lang: f.title(lang) for lang in ("zh", "en")},
                "detail": f.detail,
                "evidence": [{"file": e.file, "line": e.line, "col": e.col,
                              "raw": e.raw.strip() if e.raw else None}
                             for e in f.evidence],
            } for f in self.findings],
        }


def _has_security_policy(cfg: VrpConfig) -> bool:
    return bool(cfg.security_rules) or cfg.security_default_action is not None


def _check_default_deny(cfg: VrpConfig) -> Iterable[Finding]:
    if not _has_security_policy(cfg):
        return
    da = cfg.security_default_action
    if da is not None and da.value == "permit":
        yield Finding(
            "FW-DEFAULT-DENY", "critical", "fail",
            {"zh": "默认动作为 permit:所有未匹配安全策略的流量被放行(permit-any)。",
             "en": "Default action is 'permit': all traffic matching no rule is "
                   "allowed (permit-any)."},
            [da.source])
    else:
        yield Finding(
            "FW-DEFAULT-DENY", "critical", "pass",
            {"zh": "未匹配安全策略的流量默认被拒绝。",
             "en": "Traffic matching no rule is denied by default."},
            [da.source] if da is not None else [])


def _narrowed(zones, addresses) -> bool:
    """A side is narrowed if it has a non-``any`` zone OR a non-``any`` address.

    Using zone-presence alone is wrong both ways: an explicit ``source-zone any``
    would look "scoped" (missing a permit-any), and an address-only rule would
    look "unscoped" (false positive). Either an effective zone or an effective
    address constrains the side.
    """
    zoned = any(z.value.lower() != "any" for z in zones)
    addressed = any(a.value.lower().split()[0] != "any" for a in addresses)
    return zoned or addressed


def _check_permit_scope(cfg: VrpConfig) -> Iterable[Finding]:
    for r in cfg.security_rules:
        if not (r.action and r.action.value == "permit"):
            continue
        src_ok = _narrowed(r.source_zones, r.source_addresses)
        dst_ok = _narrowed(r.destination_zones, r.destination_addresses)
        if src_ok and dst_ok:
            continue
        if not src_ok and not dst_ok:
            yield Finding(
                "FW-PERMIT-SCOPE", "high", "fail",
                {"zh": f"规则 '{r.name.value}' 放行流量,但源与目的均未被区域或地址收敛(permit-any)。",
                 "en": f"Rule '{r.name.value}' permits traffic with neither source "
                       f"nor destination narrowed by zone or address (permit-any)."},
                [r.source])
        else:
            zh_side, en_side = ("源", "source") if not src_ok else ("目的", "destination")
            yield Finding(
                "FW-PERMIT-SCOPE", "medium", "warn",
                {"zh": f"规则 '{r.name.value}' 放行流量,但{zh_side}侧未被区域或地址收敛(匹配所有{zh_side})。",
                 "en": f"Rule '{r.name.value}' permits traffic but the {en_side} side "
                       f"is not narrowed by zone or address."},
                [r.source])


def _check_rule_logging(cfg: VrpConfig) -> Iterable[Finding]:
    for r in cfg.security_rules:
        if r.action and r.action.value == "permit" and r.session_logging is None:
            yield Finding(
                "FW-RULE-LOGGING", "medium", "warn",
                {"zh": f"规则 '{r.name.value}' 放行流量但未开启 session logging,可审计性不足。",
                 "en": f"Rule '{r.name.value}' permits traffic without 'session "
                       f"logging' (auditability gap)."},
                [r.source])


def _check_zone_iface_unique(cfg: VrpConfig) -> Iterable[Finding]:
    # interface -> {zone_name: interface-binding SourceRef} (dedupe repeats in
    # the same zone, so only genuinely conflicting zones are flagged)
    seen: Dict[str, Dict[str, SourceRef]] = {}
    for z in cfg.firewall_zones:
        for itf in z.interfaces:
            seen.setdefault(itf.value, {}).setdefault(z.name.value, itf.source)
    for name, zone_refs in seen.items():
        if len(zone_refs) > 1:
            zones = ", ".join(zone_refs)
            yield Finding(
                "FW-ZONE-IFACE-UNIQUE", "high", "fail",
                {"zh": f"接口 {name} 被绑定到 {len(zone_refs)} 个区域:{zones}。",
                 "en": f"Interface {name} is bound to {len(zone_refs)} zones: {zones}."},
                list(zone_refs.values()))


def _check_hrp(cfg: VrpConfig) -> Iterable[Finding]:
    if cfg.hrp is None:
        return
    if cfg.hrp.enabled.value:
        yield Finding(
            "HRP-ENABLED", "info", "pass",
            {"zh": "HRP 双机热备已启用。",
             "en": "HRP dual-node hot-standby is enabled."},
            [cfg.hrp.enabled.source])
    else:
        yield Finding(
            "HRP-ENABLED", "medium", "warn",
            {"zh": "已配置 HRP 但未启用(缺少 hrp enable)。",
             "en": "HRP is configured but not enabled (no 'hrp enable')."},
            [cfg.hrp.source])


CHECKS = [_check_default_deny, _check_permit_scope, _check_rule_logging,
          _check_zone_iface_unique, _check_hrp]


def run_checks(cfg: VrpConfig) -> AcceptanceReport:
    """Run all acceptance checks; findings are ordered fail/warn/pass then severity."""
    report = AcceptanceReport(source_file=cfg.source_file)
    for check in CHECKS:
        report.findings.extend(check(cfg))
    report.findings.sort(key=lambda f: (_STATUS_ORDER.get(f.status, 9),
                                        SEVERITY_ORDER.get(f.severity, 9)))
    return report


_STATUS_ICON = {"pass": "✅", "warn": "⚠️", "fail": "❌"}
_L = {
    "zh": {"title": "安全验收报告", "config": "配置文件", "result": "结论",
           "summary": "汇总", "findings": "检查项", "evidence": "证据",
           "pass": "通过", "warn": "告警", "fail": "未通过",
           "na": "无适用的安全检查项(该配置未包含安全策略 / 区域 / HRP)。"},
    "en": {"title": "Security Acceptance Report", "config": "Config",
           "result": "Result", "summary": "Summary", "findings": "Checks",
           "evidence": "Evidence", "pass": "PASS", "warn": "WARN", "fail": "FAIL",
           "na": "No applicable security checks (no security-policy / zones / HRP)."},
}


def render_markdown(report: AcceptanceReport, lang: str = "zh") -> str:
    """Render an acceptance report as Markdown (lang: ``zh`` or ``en``)."""
    L = _L.get(lang, _L["zh"])
    c = report.counts()
    out: List[str] = [
        f"# {L['title']}",
        "",
        f"- **{L['config']}**: `{report.source_file}`",
    ]
    if not report.findings:
        out += ["", f"_{L['na']}_", ""]
        return "\n".join(out) + "\n"
    out += [
        f"- **{L['result']}**: {_STATUS_ICON[report.result]} {L[report.result]}",
        f"- **{L['summary']}**: {c['fail']} {L['fail']} · {c['warn']} {L['warn']} "
        f"· {c['pass']} {L['pass']}",
        "",
        f"## {L['findings']}",
    ]
    for f in report.findings:
        out += [
            "",
            f"### {_STATUS_ICON[f.status]} `{f.check_id}` [{f.severity.upper()}] "
            f"— {f.title(lang)}",
            "",
            f.detail.get(lang, f.detail.get("en", "")),
        ]
        if f.evidence:
            out += ["", f"**{L['evidence']}**:"]
            for e in f.evidence:
                snippet = f" — `{e.raw.strip()}`" if e.raw else ""
                out.append(f"- `{e.file}:{e.line}`{snippet}")
    return "\n".join(out) + "\n"
