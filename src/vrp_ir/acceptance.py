"""Security acceptance checks over a parsed :class:`~vrp_ir.models.VrpConfig`.

This is the layer that turns the source-traceable IR into a security
*acceptance report*. Each check is a small "test case" with a stable id and an
intent, and every :class:`Finding` cites the exact source lines it is based on
(the *evidenceRef*). Because the IR carries field-level provenance, a reviewer
can jump straight from a finding to the offending configuration line.

Zero runtime dependencies; Markdown / JSON rendering.
"""
from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional

from .models import AddressSet, VrpConfig
from .sourceref import SourceRef

# Severity ranked most -> least serious.
SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
_STATUS_ORDER = {"fail": 0, "warn": 1, "unchecked": 2, "pass": 3, "na": 4}

# Stable check catalogue: id -> intent ("what is verified").
CHECKS_META: Dict[str, str] = {
    "PARSER-UNCHECKED-LINES": "Parser recognized every non-empty configuration line",
    "FW-DEFAULT-DENY": "Security-policy default action denies unmatched traffic",
    "FW-PERMIT-SCOPE": "Permit rules are narrowed (by zone or address) on both sides",
    "FW-RULE-LOGGING": "Permit rules enable session logging",
    "FW-ZONE-IFACE-UNIQUE": "Each interface is bound to exactly one zone",
    "FW-ADDRESS-SET-ANY": "Address-set objects do not silently equal any (0.0.0.0/0)",
    "HRP-ENABLED": "HRP is enabled when configured",
    "FW-HRP-INCOMPLETE": "HRP enabled with heartbeat interface and remote peer configured",
    "FW-MGMT-TELNET": "Telnet management access is disabled (cleartext protocol)",
    "FW-MGMT-HTTP": "HTTP web management is disabled (cleartext protocol; use HTTPS)",
    "FW-MGMT-VTY-TELNET": "VTY management lines do not accept Telnet (cleartext protocol)",
    "FW-MGMT-VTY-NO-ACL": "VTY management lines restrict inbound source with an ACL",
    "FW-SSH-WEAK-CIPHER": "SSH server does not use weak (CBC-mode / DES) ciphers",
    "FW-AAA-LOCAL-USER-TELNET": "Local AAA users are not granted the Telnet service type (cleartext)",
    "FW-AAA-PASSWORD-EXPIRE-DISABLED": "Local AAA password-policy view does not explicitly disable password expiry",
    "FW-AAA-PASSWORD-ALERT-DISABLED": "Local AAA password-policy view does not explicitly disable password expiry alerts",
    "FW-AAA-PASSWORD-INITIAL-CHANGE-DISABLED": "Local AAA password-policy view does not explicitly disable initial-password change prompts",
    "FW-AAA-PASSWORD-HISTORY-DISABLED": "Local AAA password-policy view does not explicitly disable password history reuse protection",
    "FW-SNMP-WEAK-COMMUNITY": "SNMP community is not a default/guessable string",
    "FW-SNMP-V3": "SNMP uses v3 with authentication and privacy (no v1/v2c)",
    "FW-NTP-MISSING": "At least one NTP server is configured",
}


@dataclass(frozen=True)
class StandardRef:
    """An **advisory** reference linking a check to a publicly citable control.

    This is never a certification or compliance claim. ``control`` is a
    control-domain description (e.g. "encrypted remote management"), **not** a
    fabricated clause number. For frameworks like 等保 (MLPS), ``level`` records
    the grading (e.g. "三级" / "四级"). A mapping is only treated as definitive
    once a human verifies it against the standard text (``manual_verified``).
    """
    framework: str                     # e.g. "等保", "CIS-style", "Huawei-hardening"
    control: str                       # control-domain description (NOT a clause id)
    level: Optional[str] = None        # e.g. "三级" / "四级" for 等保
    advisory_only: bool = True
    manual_verified: bool = False
    note: Optional[str] = None


@dataclass
class Finding:
    """One acceptance test-case result, citing its source evidence.

    Evidence policy ("no source, no claim"): a finding with an asserting status
    (``pass`` / ``warn`` / ``fail``) must be backed by **either** a cited source
    line (``evidence``) **or** a documented ``rationale`` (for absence/implicit
    findings that legitimately have no single line to cite). ``na`` / ``unchecked``
    make no claim and may have neither.

    - ``confidence`` reflects how certain the conclusion is: ``high`` for findings
      backed by a parsed source line, ``low`` for absence/implicit-default
      findings, ``medium`` in between.
    - ``references`` carries advisory standard references (populated later); it is
      never a certification claim.
    """
    check_id: str
    severity: str            # critical | high | medium | low | info
    status: str              # pass | warn | fail | na | unchecked
    detail: str
    evidence: List[SourceRef] = field(default_factory=list)
    confidence: str = "high"          # high | medium | low
    rationale: Optional[str] = None   # basis when there is no single line to cite
    references: List["StandardRef"] = field(default_factory=list)  # advisory (see #70)

    def __post_init__(self) -> None:
        # "No source, no claim": an asserting status with no cited evidence must
        # document its basis, so we never surface a bare, unbacked claim.
        if self.status in ("pass", "warn", "fail") and not self.evidence \
                and not self.rationale:
            raise ValueError(
                f"{self.check_id}: a '{self.status}' finding without evidence "
                "must provide a rationale (no source, no claim)")

    @property
    def title(self) -> str:
        return CHECKS_META.get(self.check_id, self.check_id)


@dataclass
class AcceptanceReport:
    source_file: str
    findings: List[Finding] = field(default_factory=list)
    analyzed_line_count: int = 0
    unparsed_lines: List[SourceRef] = field(default_factory=list)

    @property
    def result(self) -> str:
        if any(f.status == "fail" for f in self.findings):
            return "fail"
        if any(f.status == "warn" for f in self.findings):
            return "warn"
        if any(f.status == "unchecked" for f in self.findings):
            return "unchecked"
        if any(f.status == "pass" for f in self.findings):
            return "pass"
        if any(f.status == "na" for f in self.findings):
            return "na"
        return "pass"

    def counts(self) -> Dict[str, int]:
        c = {"pass": 0, "warn": 0, "fail": 0, "na": 0, "unchecked": 0}
        for f in self.findings:
            c[f.status] = c.get(f.status, 0) + 1
        return c

    def check_coverage(self) -> Dict[str, object]:
        """Summarize what the audit asserted vs. left unasserted.

        ``pass``/``warn``/``fail`` findings made a claim; ``na``/``unchecked``
        explicitly made no claim. Surfacing the latter is the point: the report
        states *what it did not assert and why*.
        """
        asserted = [f for f in self.findings if f.status in ("pass", "warn", "fail")]
        na = [f for f in self.findings if f.status == "na"]
        unchecked = [f for f in self.findings if f.status == "unchecked"]
        return {
            "asserted": len(asserted),
            "na": len(na),
            "unchecked": len(unchecked),
            "na_checks": [f.check_id for f in na],
            "unchecked_checks": [f.check_id for f in unchecked],
        }

    def parser_coverage(self) -> Dict[str, object]:
        unparsed = len(self.unparsed_lines)
        recognized = max(0, self.analyzed_line_count - unparsed)
        percent = None
        if self.analyzed_line_count:
            percent = round((recognized / self.analyzed_line_count) * 100, 1)
        return {
            "analyzed_lines": self.analyzed_line_count,
            "recognized_lines": recognized,
            "unparsed_lines": unparsed,
            "coverage_percent": percent,
        }

    def to_dict(self) -> dict:
        return {
            "source_file": self.source_file,
            "result": self.result,
            "counts": self.counts(),
            "check_coverage": self.check_coverage(),
            "parser_coverage": {
                **self.parser_coverage(),
                "unparsed": [{"file": e.file, "line": e.line, "col": e.col,
                              "raw": e.raw.strip() if e.raw else None}
                             for e in self.unparsed_lines],
            },
            "findings": [{
                "check_id": f.check_id,
                "severity": f.severity,
                "status": f.status,
                "title": f.title,
                "detail": f.detail,
                "confidence": f.confidence,
                "rationale": f.rationale,
                "references": [{"framework": r.framework, "control": r.control,
                                "level": r.level, "advisory_only": r.advisory_only,
                                "manual_verified": r.manual_verified, "note": r.note}
                               for r in f.references],
                "evidence": [{"file": e.file, "line": e.line, "col": e.col,
                              "raw": e.raw.strip() if e.raw else None}
                             for e in f.evidence],
            } for f in self.findings],
        }


def _has_security_policy(cfg: VrpConfig) -> bool:
    return bool(cfg.security_rules) or cfg.security_default_action is not None


def _check_default_deny(cfg: VrpConfig) -> Iterable[Finding]:
    if not _has_security_policy(cfg):
        yield Finding(
            "FW-DEFAULT-DENY", "info", "na",
            "No security-policy was parsed; default-deny is not applicable.",
            [])
        return
    da = cfg.security_default_action
    if da is not None and da.value == "permit":
        yield Finding(
            "FW-DEFAULT-DENY", "critical", "fail",
            "Default action is 'permit': all traffic matching no rule is allowed "
            "(permit-any).",
            [da.source])
    elif da is not None:
        yield Finding(
            "FW-DEFAULT-DENY", "critical", "pass",
            "Traffic matching no rule is denied by default.",
            [da.source])
    else:
        yield Finding(
            "FW-DEFAULT-DENY", "critical", "pass",
            "Traffic matching no rule is denied by default.",
            [], confidence="low",
            rationale="No explicit 'default action' was parsed; relies on the "
                      "VRP security-policy implicit deny-by-default.")


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


def _check_vty_telnet(cfg: VrpConfig) -> Iterable[Finding]:
    for ui in cfg.user_interfaces:
        if ui.kind.value != "vty":
            continue
        for proto in ui.protocol_inbound:
            if proto.value.lower() in ("telnet", "all"):
                yield Finding(
                    "FW-MGMT-VTY-TELNET", "high", "fail",
                    f"VTY {ui.first.value}–{ui.last.value if ui.last else ui.first.value} "
                    f"accepts Telnet (protocol inbound {proto.value}); management traffic "
                    f"is transmitted in cleartext. Restrict to SSH only.",
                    [proto.source])
                break


def _check_vty_no_acl(cfg: VrpConfig) -> Iterable[Finding]:
    for ui in cfg.user_interfaces:
        if ui.kind.value != "vty":
            continue
        if ui.protocol_inbound and ui.acl_inbound is None:
            yield Finding(
                "FW-MGMT-VTY-NO-ACL", "medium", "warn",
                f"VTY {ui.first.value}–{ui.last.value if ui.last else ui.first.value} "
                f"has no inbound ACL; the management line is reachable from any source. "
                f"Apply 'acl <id> inbound' to restrict access.",
                [ui.source])


def _is_weak_cipher(name: str) -> bool:
    lo = name.lower()
    return "cbc" in lo or lo.startswith("3des") or lo == "des"


def _check_ssh_weak_cipher(cfg: VrpConfig) -> Iterable[Finding]:
    if not cfg.ssh_server_ciphers:
        return
    weak = [t for t in cfg.ssh_server_ciphers if _is_weak_cipher(t.value)]
    if not weak:
        return
    names = ", ".join(t.value for t in weak)
    yield Finding(
        "FW-SSH-WEAK-CIPHER", "medium", "warn",
        f"SSH server is configured with weak cipher(s): {names}. "
        f"CBC-mode and DES ciphers are cryptographically weak; "
        f"use CTR or GCM mode ciphers instead.",
        [t.source for t in weak])


def _check_aaa_local_user_telnet(cfg: VrpConfig) -> Iterable[Finding]:
    for user in cfg.local_users:
        for svc in user.service_types:
            if svc.value.lower() == "telnet":
                yield Finding(
                    "FW-AAA-LOCAL-USER-TELNET", "medium", "warn",
                    f"Local user '{user.name.value}' is granted the Telnet service type; "
                    f"Telnet transmits credentials in cleartext. "
                    f"Remove 'telnet' from the service-type list.",
                    [svc.source])
                break


def _check_aaa_password_expire_disabled(cfg: VrpConfig) -> Iterable[Finding]:
    for policy in cfg.local_aaa_password_policies:
        if policy.password_expire_days is None or policy.password_expire_days.value != 0:
            continue
        yield Finding(
            "FW-AAA-PASSWORD-EXPIRE-DISABLED", "medium", "warn",
            f"Local AAA password policy ({policy.scope.value}) sets "
            f"'password expire 0'; passwords never expire under this policy.",
            [policy.password_expire_days.source])


def _check_aaa_password_alert_disabled(cfg: VrpConfig) -> Iterable[Finding]:
    for policy in cfg.local_aaa_password_policies:
        if (
            policy.password_alert_before_expire_days is None
            or policy.password_alert_before_expire_days.value != 0
        ):
            continue
        yield Finding(
            "FW-AAA-PASSWORD-ALERT-DISABLED", "low", "warn",
            f"Local AAA password policy ({policy.scope.value}) sets "
            f"'password alert before-expire 0'; users receive no expiry warning.",
            [policy.password_alert_before_expire_days.source])


def _check_aaa_password_initial_change_disabled(cfg: VrpConfig) -> Iterable[Finding]:
    for policy in cfg.local_aaa_password_policies:
        if policy.password_alert_original is None or policy.password_alert_original.value:
            continue
        yield Finding(
            "FW-AAA-PASSWORD-INITIAL-CHANGE-DISABLED", "medium", "warn",
            f"Local AAA password policy ({policy.scope.value}) explicitly disables "
            f"initial-password change prompting with 'undo password alert original'.",
            [policy.password_alert_original.source])


def _check_aaa_password_history_disabled(cfg: VrpConfig) -> Iterable[Finding]:
    for policy in cfg.local_aaa_password_policies:
        if (
            policy.password_history_record_number is None
            or policy.password_history_record_number.value != 0
        ):
            continue
        yield Finding(
            "FW-AAA-PASSWORD-HISTORY-DISABLED", "medium", "warn",
            f"Local AAA password policy ({policy.scope.value}) sets "
            f"'password history record number 0'; password reuse protection is disabled.",
            [policy.password_history_record_number.source])


def _check_snmp_weak_community(cfg: VrpConfig) -> Iterable[Finding]:
    for community in cfg.snmp_communities:
        if community.community is None:
            continue
        value = community.community.value
        if value.lower() not in ("public", "private"):
            continue
        yield Finding(
            "FW-SNMP-WEAK-COMMUNITY", "medium", "warn",
            f"Community '{value}' ({community.access_mode.value}) is a well-known default.",
            [community.community.source])


def _check_snmp_v3(cfg: VrpConfig) -> Iterable[Finding]:
    for version in cfg.snmp_versions:
        if version.value.lower() in ("v1", "v2c"):
            yield Finding(
                "FW-SNMP-V3", "medium", "warn",
                f"SNMP {version.value} is enabled; use SNMPv3 with authentication "
                f"and privacy instead of v1/v2c.",
                [version.source])
    for user in cfg.snmp_usm_users:
        if user.auth_mode is None or user.privacy_mode is None:
            missing = []
            if user.auth_mode is None:
                missing.append("authentication")
            if user.privacy_mode is None:
                missing.append("privacy")
            yield Finding(
                "FW-SNMP-V3", "medium", "warn",
                f"SNMPv3 user '{user.name.value}' is missing {' and '.join(missing)}; "
                f"v3 users should configure both auth and privacy.",
                [user.source])


def _has_device_acceptance_scope(cfg: VrpConfig) -> bool:
    """Return True when the parsed config has enough device facts for absence checks."""
    return bool(
        cfg.interfaces or cfg.acls or cfg.static_routes or cfg.firewall_zones or
        cfg.security_rules or cfg.address_sets or cfg.service_sets or
        cfg.nat_policy_rules or cfg.nat_servers or cfg.hrp or cfg.user_interfaces or
        cfg.local_users or cfg.local_aaa_password_policies or
        cfg.telnet_server_enabled is not None or
        cfg.http_server_enabled is not None or cfg.ssh_server_ciphers or cfg.log_hosts
    )


def _check_ntp_missing(cfg: VrpConfig) -> Iterable[Finding]:
    if cfg.ntp_servers:
        yield Finding(
            "FW-NTP-MISSING", "medium", "pass",
            "At least one NTP server is configured.",
            [server.source for server in cfg.ntp_servers])
        return
    if not _has_device_acceptance_scope(cfg):
        return
    yield Finding(
        "FW-NTP-MISSING", "medium", "fail",
        "No NTP server is configured; device time is unsynchronised, weakening "
        "log correlation and audit evidence.",
        [], confidence="low",
        rationale="Absence finding: no 'ntp-service unicast-server' line was "
                  "parsed in a config that otherwise has device-level facts.")


def _dengbao(control: str) -> List[StandardRef]:
    # 等保 (MLPS) is graded by level; Level 3 is the common acceptance bar, Level 4
    # is critical infrastructure. These are advisory control-domain descriptions —
    # NOT clause numbers — and remain manual_verified=False pending expert review.
    return [StandardRef("等保", control, level="三级"),
            StandardRef("等保", control, level="四级")]


# Advisory mapping: check id -> publicly citable control domains. Advisory only,
# never a certification claim; clause numbers are intentionally absent until a
# human verifies them against the standard text.
CHECK_REFERENCES: Dict[str, List[StandardRef]] = {
    "FW-DEFAULT-DENY": _dengbao("访问控制：默认拒绝未匹配流量") + [
        StandardRef("CIS-style", "Default-deny on unmatched traffic")],
    "FW-PERMIT-SCOPE": _dengbao("访问控制：按最小权限收敛放通范围") + [
        StandardRef("CIS-style", "Least-privilege permit rules")],
    "FW-MGMT-TELNET": _dengbao("远程管理：禁用明文管理协议") + [
        StandardRef("Huawei-hardening", "Disable Telnet; use STelnet/SSH")],
    "FW-MGMT-HTTP": _dengbao("远程管理：禁用明文管理协议") + [
        StandardRef("Huawei-hardening", "Disable HTTP; use HTTPS")],
    "FW-MGMT-VTY-TELNET": _dengbao("远程管理：管理线路仅用加密协议") + [
        StandardRef("Huawei-hardening", "VTY protocol inbound ssh only")],
    "FW-MGMT-VTY-NO-ACL": _dengbao("远程管理：限制管理访问源地址") + [
        StandardRef("CIS-style", "Restrict management-plane source addresses")],
    "FW-SSH-WEAK-CIPHER": _dengbao("密码算法：禁用弱加密算法") + [
        StandardRef("CIS-style", "Disable CBC-mode/DES ciphers; use CTR/GCM")],
    "FW-SNMP-WEAK-COMMUNITY": _dengbao("凭据安全：禁用默认/弱 SNMP 团体字") + [
        StandardRef("CIS-style", "No default SNMP community strings")],
    "FW-SNMP-V3": _dengbao("SNMP 安全：使用 v3 鉴别与加密，禁用 v1/v2c") + [
        StandardRef("CIS-style", "Use SNMPv3 with auth+privacy; disable v1/v2c")],
    "FW-AAA-LOCAL-USER-TELNET": _dengbao("身份鉴别：账户不授予明文服务") + [
        StandardRef("Huawei-hardening", "Do not grant Telnet service-type")],
    "FW-AAA-PASSWORD-EXPIRE-DISABLED": _dengbao("身份鉴别：口令应定期更换") + [
        StandardRef("Huawei-hardening", "Avoid 'password expire 0' in local AAA password policy")],
    "FW-AAA-PASSWORD-ALERT-DISABLED": _dengbao("身份鉴别：口令到期前应提醒更换") + [
        StandardRef("Huawei-hardening", "Avoid 'password alert before-expire 0' in local AAA password policy")],
    "FW-AAA-PASSWORD-INITIAL-CHANGE-DISABLED": _dengbao("身份鉴别：初始口令登录后应提示修改") + [
        StandardRef("Huawei-hardening", "Do not disable initial-password change prompting")],
    "FW-AAA-PASSWORD-HISTORY-DISABLED": _dengbao("身份鉴别：应防止历史口令重复使用") + [
        StandardRef("Huawei-hardening", "Do not set 'password history record number 0'")],
    "FW-NTP-MISSING": _dengbao("时间同步：配置可信 NTP 以保证日志可追溯") + [
        StandardRef("CIS-style", "Configure trusted NTP for log correlation")],
}


@dataclass(frozen=True)
class CheckSpec:
    """A registered acceptance check: its function plus structured metadata.

    The registry is the single place that pairs a check function with its id,
    human intent, and advisory references. Severity is intentionally not fixed
    here — it is decided per finding by the check.
    """
    check_id: str
    intent: str
    fn: "Callable[[VrpConfig], Iterable[Finding]]"
    references: List[StandardRef] = field(default_factory=list)


def _spec(check_id: str, fn: "Callable[[VrpConfig], Iterable[Finding]]") -> CheckSpec:
    return CheckSpec(check_id=check_id, intent=CHECKS_META[check_id], fn=fn,
                     references=list(CHECK_REFERENCES.get(check_id, [])))


# Check registry — registered functions + structured metadata (not a DSL).
# Order is preserved as the audit run order.
REGISTRY: List[CheckSpec] = [
    _spec("FW-DEFAULT-DENY", _check_default_deny),
    _spec("FW-PERMIT-SCOPE", _check_permit_scope),
    _spec("FW-RULE-LOGGING", _check_rule_logging),
    _spec("FW-ZONE-IFACE-UNIQUE", _check_zone_iface_unique),
    _spec("FW-ADDRESS-SET-ANY", _check_address_set_any),
    _spec("HRP-ENABLED", _check_hrp),
    _spec("FW-HRP-INCOMPLETE", _check_hrp_incomplete),
    _spec("FW-MGMT-TELNET", _check_mgmt_telnet),
    _spec("FW-MGMT-HTTP", _check_mgmt_http),
    _spec("FW-MGMT-VTY-TELNET", _check_vty_telnet),
    _spec("FW-MGMT-VTY-NO-ACL", _check_vty_no_acl),
    _spec("FW-SSH-WEAK-CIPHER", _check_ssh_weak_cipher),
    _spec("FW-AAA-LOCAL-USER-TELNET", _check_aaa_local_user_telnet),
    _spec("FW-AAA-PASSWORD-EXPIRE-DISABLED", _check_aaa_password_expire_disabled),
    _spec("FW-AAA-PASSWORD-ALERT-DISABLED", _check_aaa_password_alert_disabled),
    _spec("FW-AAA-PASSWORD-INITIAL-CHANGE-DISABLED", _check_aaa_password_initial_change_disabled),
    _spec("FW-AAA-PASSWORD-HISTORY-DISABLED", _check_aaa_password_history_disabled),
    _spec("FW-SNMP-WEAK-COMMUNITY", _check_snmp_weak_community),
    _spec("FW-SNMP-V3", _check_snmp_v3),
    _spec("FW-NTP-MISSING", _check_ntp_missing),
]

CHECKS = [spec.fn for spec in REGISTRY]


def registry() -> List[CheckSpec]:
    """Return the registered checks (function + metadata), in run order."""
    return list(REGISTRY)


def list_checks() -> List[Dict[str, str]]:
    """Return the check catalogue: ``[{"check_id", "intent"}, ...]`` sorted by id."""
    return [{"check_id": cid, "intent": intent}
            for cid, intent in sorted(CHECKS_META.items())]


def explain_check(check_id: str) -> Optional[dict]:
    """Describe one check (intent + advisory references), or ``None`` if unknown."""
    if check_id not in CHECKS_META:
        return None
    return {
        "check_id": check_id,
        "intent": CHECKS_META[check_id],
        "references": [{"framework": r.framework, "control": r.control,
                        "level": r.level, "advisory_only": r.advisory_only,
                        "manual_verified": r.manual_verified}
                       for r in CHECK_REFERENCES.get(check_id, [])],
    }


def run_checks(cfg: VrpConfig) -> AcceptanceReport:
    """Run all acceptance checks; findings are ordered fail/warn/pass then severity."""
    report = AcceptanceReport(
        source_file=cfg.source_file,
        analyzed_line_count=cfg.analyzed_line_count,
        unparsed_lines=list(cfg.unparsed_lines),
    )
    if cfg.unparsed_lines:
        report.findings.append(Finding(
            "PARSER-UNCHECKED-LINES", "medium", "unchecked",
            f"{len(cfg.unparsed_lines)} non-empty configuration line(s) were not "
            "recognized by the parser; audit results may be incomplete.",
            list(cfg.unparsed_lines)))
    for check in CHECKS:
        report.findings.extend(check(cfg))
    for f in report.findings:
        refs = CHECK_REFERENCES.get(f.check_id)
        if refs:
            f.references = list(refs)
    report.findings.sort(key=lambda f: (_STATUS_ORDER.get(f.status, 9),
                                        SEVERITY_ORDER.get(f.severity, 9)))
    return report


_STATUS_ICON = {"pass": "✅", "warn": "⚠️", "fail": "❌", "na": "➖", "unchecked": "❔"}
_NA = "No applicable security checks (no security-policy / zones / HRP)."


def render_markdown(report: AcceptanceReport) -> str:
    """Render an acceptance report as Markdown."""
    c = report.counts()
    out: List[str] = [
        "# Security Acceptance Report",
        "",
        f"- **Config**: `{report.source_file}`",
        _parser_coverage_summary(report),
    ]
    if not report.findings:
        out += _parser_coverage_details(report)
        out += ["", f"_{_NA}_", ""]
        return "\n".join(out) + "\n"
    out += [
        f"- **Result**: {_STATUS_ICON[report.result]} {report.result.upper()}",
        f"- **Summary**: {c['fail']} FAIL · {c['warn']} WARN · "
        f"{c['unchecked']} UNCHECKED · {c['pass']} PASS · {c['na']} NA",
    ]
    out += _parser_coverage_details(report)
    out += _coverage_limitations(report)
    out += [
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
        if f.status in ("pass", "warn", "fail"):
            out += ["", f"_Confidence: {f.confidence}._"]
        if f.rationale:
            out += [f"_Basis: {f.rationale}_"]
        if f.references:
            out += ["", "**Advisory references** (not a certification claim):"]
            for r in f.references:
                lvl = f" {r.level}" if r.level else ""
                verified = "" if r.manual_verified else " — unverified mapping"
                out.append(f"- {r.framework}{lvl}: {r.control}{verified}")
        if f.evidence:
            out += ["", "**Evidence**:"]
            for e in f.evidence:
                snippet = f" — `{e.raw.strip()}`" if e.raw else ""
                out.append(f"- `{e.file}:{e.line}`{snippet}")
    if any(f.references for f in report.findings):
        out += [
            "",
            "---",
            "",
            "_Advisory references map findings to publicly citable control domains. "
            "They are **not** a compliance certification; mappings marked "
            "'unverified' await manual review against the standard text._",
        ]
    return "\n".join(out) + "\n"


def _parser_coverage_summary(report: AcceptanceReport) -> str:
    c = report.parser_coverage()
    pct = c["coverage_percent"]
    pct_text = "n/a" if pct is None else f"{pct:.1f}%"
    return (
        f"- **Parser coverage**: {c['recognized_lines']}/{c['analyzed_lines']} "
        f"recognized ({pct_text}); {c['unparsed_lines']} unparsed"
    )


def _parser_coverage_details(report: AcceptanceReport) -> List[str]:
    if not report.unparsed_lines:
        return []
    out = ["", "## Parser coverage", "", "Unparsed lines are surfaced so audit users can judge parser coverage:"]
    for e in report.unparsed_lines:
        snippet = f" — `{e.raw.strip()}`" if e.raw else ""
        out.append(f"- `{e.file}:{e.line}`{snippet}")
    return out


def _coverage_limitations(report: AcceptanceReport) -> List[str]:
    cc = report.check_coverage()
    out = [
        "",
        "## Coverage & limitations",
        "",
        f"- **Checks asserted**: {cc['asserted']} · "
        f"**not applicable**: {cc['na']} · **unchecked**: {cc['unchecked']}",
    ]
    not_asserted = [f for f in report.findings if f.status in ("na", "unchecked")]
    if not_asserted:
        out += ["", "_Not asserted (no claim made):_"]
        for f in not_asserted:
            out.append(f"- `{f.check_id}` [{f.status.upper()}] — {f.detail}")
    return out


_SARIF_LEVEL = {"fail": "error", "warn": "warning", "unchecked": "note"}


def render_sarif(report: AcceptanceReport) -> str:
    """Render the report as SARIF 2.1.0 for CI code scanning.

    Only asserting problems (fail/warn) and coverage gaps (unchecked) become
    results; pass/na make no problem claim. Each result locates the exact source
    line when one is cited.
    """
    from . import __version__ as version

    rules = [{"id": cid, "name": cid, "shortDescription": {"text": intent}}
             for cid, intent in CHECKS_META.items()]
    results = []
    for f in report.findings:
        if f.status not in _SARIF_LEVEL:
            continue
        physical = {"artifactLocation": {"uri": report.source_file}}
        lines = [e.line for e in f.evidence if e.line]
        if lines:
            physical["region"] = {"startLine": lines[0]}
        results.append({
            "ruleId": f.check_id,
            "level": _SARIF_LEVEL[f.status],
            "message": {"text": f.detail},
            "locations": [{"physicalLocation": physical}],
            "properties": {"severity": f.severity, "status": f.status,
                           "confidence": f.confidence},
        })
    doc = {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [{
            "tool": {"driver": {
                "name": "vrp-ir",
                "informationUri": "https://github.com/zynovexllc/vrp-ir",
                "version": version,
                "rules": rules,
            }},
            "results": results,
        }],
    }
    return json.dumps(doc, ensure_ascii=False, indent=2) + "\n"


def render_junit(report: AcceptanceReport) -> str:
    """Render the report as JUnit XML.

    Aligns with ``--strict``: only ``fail`` becomes a JUnit ``<failure>``;
    ``warn`` passes (noted in system-out); ``na``/``unchecked`` are skipped.
    """
    findings = report.findings
    failures = sum(1 for f in findings if f.status == "fail")
    skipped = sum(1 for f in findings if f.status in ("na", "unchecked"))
    suite = ET.Element("testsuite", {
        "name": "vrp-ir audit",
        "tests": str(len(findings)),
        "failures": str(failures),
        "errors": "0",
        "skipped": str(skipped),
    })
    seen: Dict[str, int] = {}
    for f in findings:
        n = seen.get(f.check_id, 0)
        seen[f.check_id] = n + 1
        name = f.check_id if n == 0 else f"{f.check_id}#{n + 1}"
        tc = ET.SubElement(suite, "testcase",
                           {"classname": "vrp-ir.audit", "name": name})
        evidence = "; ".join(f"{e.file}:{e.line}" for e in f.evidence if e.line)
        msg = f.detail + (f" [{evidence}]" if evidence else "")
        if f.status == "fail":
            fail = ET.SubElement(tc, "failure",
                                 {"message": f.detail, "type": f.severity})
            fail.text = msg
        elif f.status in ("na", "unchecked"):
            ET.SubElement(tc, "skipped", {"message": f.status})
        elif f.status == "warn":
            so = ET.SubElement(tc, "system-out")
            so.text = f"WARN: {msg}"
    suites = ET.Element("testsuites")
    suites.append(suite)
    return ET.tostring(suites, encoding="unicode") + "\n"
