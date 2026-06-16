"""Security acceptance checks over a parsed :class:`~vrp_ir.models.VrpConfig`.

This is the layer that turns the source-traceable IR into a security
*acceptance report*. Each check is a small "test case" with a stable id and an
intent, and every :class:`Finding` cites the exact source lines it is based on
(the *evidenceRef*). Because the IR carries field-level provenance, a reviewer
can jump straight from a finding to the offending configuration line.

Zero runtime dependencies; Markdown / JSON rendering.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, List

from .models import VrpConfig
from .sourceref import SourceRef

# Severity ranked most -> least serious.
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
_STATUS_ORDER = {"fail": 0, "warn": 1, "pass": 2}

# Stable check catalogue: id -> intent ("what is verified").
CHECKS_META: Dict[str, str] = {
    "FW-DEFAULT-DENY": "Security-policy default action denies unmatched traffic",
    "FW-PERMIT-SCOPE": "Permit rules are narrowed (by zone or address) on both sides",
    "FW-RULE-LOGGING": "Permit rules enable session logging",
    "FW-ZONE-IFACE-UNIQUE": "Each interface is bound to exactly one zone",
    "FW-ADDRESS-SET-ANY": "Address-set objects do not silently equal any (0.0.0.0/0)",
    "HRP-ENABLED": "HRP is enabled when configured",
    "FW-HRP-INCOMPLETE": "HRP enabled with heartbeat interface and remote peer configured",
    "FW-MGMT-TELNET": "Telnet management access is disabled (cleartext protocol)",
    "FW-MGMT-HTTP": "HTTP web management is disabled (cleartext protocol; use HTTPS)",
}


@dataclass
class Finding:
    """One acceptance test-case result, citing its source evidence."""
    check_id: str
    severity: str            # critical | high | medium | low | info
    status: str              # pass | fail | warn
    detail: str
    evidence: List[SourceRef] = field(default_factory=list)

    @property
    def title(self) -> str:
        return CHECKS_META.get(self.check_id, self.check_id)


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
                "title": f.title,
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
            "Default action is 'permit': all traffic matching no rule is allowed "
            "(permit-any).",
            [da.source])
    else:
        yield Finding(
            "FW-DEFAULT-DENY", "critical", "pass",
            "Traffic matching no rule is denied by default.",
            [da.source] if da is not None else [])


def _addr_set_resolves_to_any(name: str, addr_sets_by_name: Dict[str, "AddressSet"]) -> bool:
    """Return True when the named address-set contains a 0.0.0.0/0 member (prefix_length 0)."""
    aset = addr_sets_by_name.get(name)
    if aset is None:
        return False
    return any(m.prefix_length is not None and m.prefix_length.value == 0
               for m in aset.members)


def _narrowed(zones, addresses, addr_sets_by_name: Dict[str, "AddressSet"] = None) -> bool:
    """A side is narrowed if it has a non-``any`` zone OR a non-``any`` address.

    Using zone-presence alone is wrong both ways: an explicit ``source-zone any``
    would look "scoped" (missing a permit-any), and an address-only rule would
    look "unscoped" (false positive). Either an effective zone or an effective
    address constrains the side.

    When *addr_sets_by_name* is provided, an ``address-set NAME`` reference is
    dereferenced: if the named set has a member with prefix_length 0 (0.0.0.0/0)
    it is treated as ``any`` and does NOT count as narrowing.
    """
    zoned = any(z.value.lower() != "any" for z in zones)

    def _is_narrowing_addr(a) -> bool:
        val = a.value.lower()
        parts = val.split()
        if parts[0] == "any":
            return False
        if parts[0] == "address-set" and addr_sets_by_name is not None and len(parts) >= 2:
            set_name = a.value.split(None, 1)[1]  # preserve original case for lookup
            return not _addr_set_resolves_to_any(set_name, addr_sets_by_name)
        return True

    addressed = any(_is_narrowing_addr(a) for a in addresses)
    return zoned or addressed


def _check_permit_scope(cfg: VrpConfig) -> Iterable[Finding]:
    addr_sets_by_name = {aset.name.value: aset for aset in cfg.address_sets}
    for r in cfg.security_rules:
        if not (r.action and r.action.value == "permit"):
            continue
        src_ok = _narrowed(r.source_zones, r.source_addresses, addr_sets_by_name)
        dst_ok = _narrowed(r.destination_zones, r.destination_addresses, addr_sets_by_name)
        if src_ok and dst_ok:
            continue
        if not src_ok and not dst_ok:
            yield Finding(
                "FW-PERMIT-SCOPE", "high", "fail",
                f"Rule '{r.name.value}' permits traffic with neither source nor "
                f"destination narrowed by zone or address (permit-any).",
                [r.source])
        else:
            side = "source" if not src_ok else "destination"
            yield Finding(
                "FW-PERMIT-SCOPE", "medium", "warn",
                f"Rule '{r.name.value}' permits traffic but the {side} side is not "
                f"narrowed by zone or address.",
                [r.source])


def _check_rule_logging(cfg: VrpConfig) -> Iterable[Finding]:
    for r in cfg.security_rules:
        if r.action and r.action.value == "permit" and r.session_logging is None:
            yield Finding(
                "FW-RULE-LOGGING", "medium", "warn",
                f"Rule '{r.name.value}' permits traffic without 'session logging' "
                f"(auditability gap).",
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
                f"Interface {name} is bound to {len(zone_refs)} zones: {zones}.",
                list(zone_refs.values()))


def _check_hrp(cfg: VrpConfig) -> Iterable[Finding]:
    if cfg.hrp is None:
        return
    if cfg.hrp.enabled.value:
        yield Finding(
            "HRP-ENABLED", "info", "pass",
            "HRP dual-node hot-standby is enabled.",
            [cfg.hrp.enabled.source])
    else:
        yield Finding(
            "HRP-ENABLED", "medium", "warn",
            "HRP is configured but not enabled (no 'hrp enable').",
            [cfg.hrp.source])


def _check_hrp_incomplete(cfg: VrpConfig) -> Iterable[Finding]:
    if cfg.hrp is None:
        return
    if not cfg.hrp.enabled.value:
        return
    if cfg.hrp.heartbeat_interface is None or cfg.hrp.peer is None:
        yield Finding(
            "FW-HRP-INCOMPLETE", "medium", "warn",
            "HRP is enabled but heartbeat interface or remote peer is not "
            "configured; the HA pair will not sync.",
            [cfg.hrp.source])


def _check_mgmt_telnet(cfg: VrpConfig) -> Iterable[Finding]:
    t = cfg.telnet_server_enabled
    if t is None or not t.value:
        return
    yield Finding(
        "FW-MGMT-TELNET", "high", "fail",
        "Telnet server is enabled; management traffic is transmitted in cleartext "
        "(credentials and commands visible on the wire). Disable with "
        "'undo telnet server enable' and use SSH instead.",
        [t.source])


def _check_address_set_any(cfg: VrpConfig) -> Iterable[Finding]:
    """Flag an address-set member equal to 0.0.0.0/0 (mask 0).

    A named object that resolves to *any* is dangerous precisely because it
    hides a permit-any behind a friendly name: a permit rule referencing such a
    set looks scoped but is effectively unrestricted. Only the unambiguous
    ``mask 0`` form is flagged (no garbage facts); range members are left alone.
    """
    for aset in cfg.address_sets:
        for m in aset.members:
            if m.prefix_length is not None and m.prefix_length.value == 0:
                yield Finding(
                    "FW-ADDRESS-SET-ANY", "high", "fail",
                    f"Address-set '{aset.name.value}' member {m.seq.value} is "
                    f"0.0.0.0/0 (any); any rule referencing this set is "
                    f"effectively unrestricted.",
                    [m.source])


def _check_mgmt_http(cfg: VrpConfig) -> Iterable[Finding]:
    h = cfg.http_server_enabled
    if h is None or not h.value:
        return
    yield Finding(
        "FW-MGMT-HTTP", "high", "fail",
        "HTTP server is enabled; web management traffic is transmitted in cleartext "
        "(credentials and commands visible on the wire). Disable with "
        "'undo http server enable' and use HTTPS instead.",
        [h.source])


CHECKS = [_check_default_deny, _check_permit_scope, _check_rule_logging,
          _check_zone_iface_unique, _check_address_set_any, _check_hrp,
          _check_hrp_incomplete, _check_mgmt_telnet, _check_mgmt_http]


def run_checks(cfg: VrpConfig) -> AcceptanceReport:
    """Run all acceptance checks; findings are ordered fail/warn/pass then severity."""
    report = AcceptanceReport(source_file=cfg.source_file)
    for check in CHECKS:
        report.findings.extend(check(cfg))
    report.findings.sort(key=lambda f: (_STATUS_ORDER.get(f.status, 9),
                                        SEVERITY_ORDER.get(f.severity, 9)))
    return report


_STATUS_ICON = {"pass": "✅", "warn": "⚠️", "fail": "❌"}
_NA = "No applicable security checks (no security-policy / zones / HRP)."


def render_markdown(report: AcceptanceReport) -> str:
    """Render an acceptance report as Markdown."""
    c = report.counts()
    out: List[str] = [
        "# Security Acceptance Report",
        "",
        f"- **Config**: `{report.source_file}`",
    ]
    if not report.findings:
        out += ["", f"_{_NA}_", ""]
        return "\n".join(out) + "\n"
    out += [
        f"- **Result**: {_STATUS_ICON[report.result]} {report.result.upper()}",
        f"- **Summary**: {c['fail']} FAIL · {c['warn']} WARN · {c['pass']} PASS",
        "",
        "## Checks",
    ]
    for f in report.findings:
        out += [
            "",
            f"### {_STATUS_ICON[f.status]} `{f.check_id}` [{f.severity.upper()}] "
            f"— {f.title}",
            "",
            f.detail,
        ]
        if f.evidence:
            out += ["", "**Evidence**:"]
            for e in f.evidence:
                snippet = f" — `{e.raw.strip()}`" if e.raw else ""
                out.append(f"- `{e.file}:{e.line}`{snippet}")
    return "\n".join(out) + "\n"
