"""Huawei VRP config text -> :class:`VrpConfig` (routing/switching + USG firewall).

Robust to VRP's `#`-delimited sections: a section opener keyword (interface /
vlan / ip vpn-instance / acl / firewall zone / security-policy) sets the current
context regardless of leading whitespace; `#`/`return`/`quit` close it (blank
lines do not); one-line globals (sysname, ip route-static, vlan batch, nat
server, hrp, !Software Version) are dispatched by keyword.
"""
from __future__ import annotations

from typing import List, Optional

from .models import (Acl, AclRule, FirewallZone, Hrp, Interface, Ipv4Address,
                     NatServer, SecurityRule, StaticRoute, Vlan, VlanRange,
                     Vrf, VrpConfig)
from .sourceref import SourceRef, Traced


def _mask_to_prefix(token: str) -> Optional[int]:
    token = token.strip()
    if token.isdigit():
        n = int(token)
        return n if 0 <= n <= 32 else None
    parts = token.split(".")
    if len(parts) != 4:
        return None
    try:
        octets = [int(p) for p in parts]
    except ValueError:
        return None
    if any(o < 0 or o > 255 for o in octets):
        return None
    bits = "".join(f"{o:08b}" for o in octets)
    if "01" in bits:
        return None
    return bits.count("1")


def _col(raw: str, token: str) -> Optional[int]:
    i = raw.find(token)
    return i if i >= 0 else None


def _parse_vlan_ranges(tokens: List[str], src: SourceRef) -> List[VlanRange]:
    """Parse `10 20 1000 to 1002 all` into VlanRange list."""
    out: List[VlanRange] = []
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t == "all":
            out.append(VlanRange(1, 4094, src))
            i += 1
        elif t.isdigit():
            if i + 2 < len(tokens) and tokens[i + 1] == "to" and tokens[i + 2].isdigit():
                out.append(VlanRange(int(t), int(tokens[i + 2]), src))
                i += 3
            else:
                out.append(VlanRange(int(t), int(t), src))
                i += 1
        else:
            i += 1
    return out


def parse_text(text: str, filename: str = "<config>") -> VrpConfig:
    cfg = VrpConfig(source_file=filename)
    ctx_kind: Optional[str] = None   # interface | vlan | vrf | acl | fwzone | secpolicy
    ctx_obj = None

    for lineno, raw in enumerate(text.splitlines(), start=1):
        s = raw.strip()
        if not s:
            continue  # blank lines must NOT close a block (hand-edited/saved .cfg may contain them)
        if s == "#" or s == "return" or s == "quit":
            ctx_kind, ctx_obj = None, None
            continue
        if s.startswith("!"):
            if s.startswith("!Software Version"):
                v = s[len("!Software Version"):].strip()
                cfg.software_version = Traced(v, SourceRef(filename, lineno, _col(raw, v), raw))
            continue

        # --- section openers (match regardless of leading whitespace) ---
        if s.startswith("interface "):
            name = s[len("interface "):].strip()
            src = SourceRef(filename, lineno, _col(raw, name), raw)
            ctx_obj = Interface(name=Traced(name, src), source=src)
            cfg.interfaces.append(ctx_obj)
            ctx_kind = "interface"
            continue
        if s.startswith("vlan batch "):
            toks = s[len("vlan batch "):].split()
            cfg.vlan_batches.extend(_parse_vlan_ranges(toks, SourceRef(filename, lineno, None, raw)))
            ctx_kind, ctx_obj = None, None
            continue
        if s.startswith("vlan ") and s[len("vlan "):].strip().split()[0].isdigit():
            vid = s[len("vlan "):].strip().split()[0]
            src = SourceRef(filename, lineno, _col(raw, vid), raw)
            ctx_obj = Vlan(vlan_id=Traced(int(vid), src), source=src)
            cfg.vlans.append(ctx_obj)
            ctx_kind = "vlan"
            continue
        if s.startswith("ip vpn-instance "):
            name = s[len("ip vpn-instance "):].strip()
            src = SourceRef(filename, lineno, _col(raw, name), raw)
            ctx_obj = Vrf(name=Traced(name, src), source=src)
            cfg.vrfs.append(ctx_obj)
            ctx_kind = "vrf"
            continue
        if s.startswith("acl "):
            ctx_obj = _open_acl(cfg, s, raw, filename, lineno)
            ctx_kind = "acl"
            continue
        if s.startswith("firewall zone "):
            ctx_obj = _open_zone(cfg, s, raw, filename, lineno)
            ctx_kind = "fwzone"
            continue
        if s == "security-policy":
            ctx_kind, ctx_obj = "secpolicy", None
            continue

        # --- one-line globals ---
        if s.startswith("sysname "):
            v = s[len("sysname "):].strip()
            cfg.hostname = Traced(v, SourceRef(filename, lineno, _col(raw, v), raw))
            continue
        if s.startswith("ip route-static "):
            _parse_static_route(cfg, s, raw, filename, lineno)
            continue
        if s.startswith("nat server "):
            _parse_nat_server(cfg, s, raw, filename, lineno)
            continue
        if s.startswith("hrp "):
            _parse_hrp(cfg, s, raw, filename, lineno)
            continue

        # --- body lines: dispatch to current context ---
        if ctx_kind == "interface":
            _iface_line(ctx_obj, s, raw, filename, lineno)
        elif ctx_kind == "vlan":
            _vlan_line(ctx_obj, s, raw, filename, lineno)
        elif ctx_kind == "vrf":
            _vrf_line(ctx_obj, s, raw, filename, lineno)
        elif ctx_kind == "acl":
            _acl_line(ctx_obj, s, raw, filename, lineno)
        elif ctx_kind == "fwzone":
            _zone_line(ctx_obj, s, raw, filename, lineno)
        elif ctx_kind == "secpolicy":
            ctx_obj = _secpolicy_dispatch(cfg, ctx_obj, s, raw, filename, lineno)

    return cfg


def _iface_line(itf: Interface, s: str, raw: str, fn: str, ln: int) -> None:
    if s.startswith("description "):
        v = s[len("description "):].strip()
        itf.description = Traced(v, SourceRef(fn, ln, _col(raw, v), raw))
    elif s == "shutdown":
        itf.shutdown = Traced(True, SourceRef(fn, ln, None, raw))
    elif s.startswith("ip address "):
        rest = s[len("ip address "):].split()
        if len(rest) >= 2:
            prefix = _mask_to_prefix(rest[1])
            if prefix is not None:
                src = SourceRef(fn, ln, _col(raw, rest[0]), raw)
                itf.ipv4.append(Ipv4Address(Traced(rest[0], src), Traced(prefix, src),
                                            is_secondary=(len(rest) >= 3 and rest[2] == "sub")))
    elif s.startswith("ip binding vpn-instance "):
        v = s[len("ip binding vpn-instance "):].strip()
        itf.vpn_instance = Traced(v, SourceRef(fn, ln, _col(raw, v), raw))
    elif s.startswith("port link-type "):
        v = s[len("port link-type "):].strip()
        itf.link_type = Traced(v, SourceRef(fn, ln, _col(raw, v), raw))
    elif s.startswith("port default vlan "):
        v = s[len("port default vlan "):].strip()
        if v.isdigit():
            itf.default_vlan = Traced(int(v), SourceRef(fn, ln, _col(raw, v), raw))
    elif s.startswith("port trunk allow-pass vlan "):
        toks = s[len("port trunk allow-pass vlan "):].split()
        itf.trunk_vlans.extend(_parse_vlan_ranges(toks, SourceRef(fn, ln, None, raw)))
    elif s.startswith("eth-trunk "):
        v = s[len("eth-trunk "):].strip()
        if v.isdigit():
            itf.eth_trunk = Traced(int(v), SourceRef(fn, ln, _col(raw, v), raw))
    elif s.startswith("vlan-type dot1q "):
        v = s[len("vlan-type dot1q "):].strip()
        if v.isdigit():
            itf.dot1q_vlan = Traced(int(v), SourceRef(fn, ln, _col(raw, v), raw))


def _vlan_line(vlan: Vlan, s: str, raw: str, fn: str, ln: int) -> None:
    if s.startswith("description "):
        v = s[len("description "):].strip()
        vlan.description = Traced(v, SourceRef(fn, ln, _col(raw, v), raw))


def _vrf_line(vrf: Vrf, s: str, raw: str, fn: str, ln: int) -> None:
    if s.startswith("route-distinguisher "):
        v = s[len("route-distinguisher "):].strip()
        vrf.route_distinguisher = Traced(v, SourceRef(fn, ln, _col(raw, v), raw))
    elif s.startswith("vpn-target "):
        # Syntax: vpn-target <rt> [<rt> ...] [both | export-extcommunity |
        # import-extcommunity] [evpn]. The direction keyword (VRP default
        # `both`) may be followed by an address-family qualifier (e.g. EVPN's
        # `vpn-target 1:1 export-extcommunity evpn`), so it is NOT necessarily
        # the last token -> locate it by membership, not by position. Route-
        # targets are the colon-bearing tokens (ASN:nn / IP:nn); any keyword or
        # qualifier is skipped rather than surfaced as a garbage RT.
        toks = s[len("vpn-target "):].split()
        direction = "both"
        for kw in ("export-extcommunity", "import-extcommunity", "both"):
            if kw in toks:
                direction = kw
                break
        for rt in toks:
            if ":" not in rt:
                continue
            tr = Traced(rt, SourceRef(fn, ln, _col(raw, rt), raw))
            if direction in ("both", "export-extcommunity"):
                vrf.export_targets.append(tr)
            if direction in ("both", "import-extcommunity"):
                vrf.import_targets.append(tr)


def _open_acl(cfg: VrpConfig, s: str, raw: str, fn: str, ln: int) -> Acl:
    rest = s[len("acl "):].split()
    src = SourceRef(fn, ln, None, raw)
    kind = None
    if rest and rest[0] == "number" and len(rest) >= 2:
        ident = Traced(rest[1], SourceRef(fn, ln, _col(raw, rest[1]), raw))
    elif rest and rest[0] == "name" and len(rest) >= 2:
        ident = Traced(rest[1], SourceRef(fn, ln, _col(raw, rest[1]), raw))
        if len(rest) >= 3:
            kind = Traced(rest[2], SourceRef(fn, ln, _col(raw, rest[2]), raw))
    else:
        ident = Traced(rest[0] if rest else "", src)
    acl = Acl(identifier=ident, source=src, kind=kind)
    cfg.acls.append(acl)
    return acl


def _acl_line(acl: Acl, s: str, raw: str, fn: str, ln: int) -> None:
    if not s.startswith("rule "):
        return
    rest = s[len("rule "):].split()
    if len(rest) >= 2 and rest[0].isdigit() and rest[1] in ("permit", "deny"):
        seq, action = rest[0], rest[1]
        body = " ".join(rest[2:]) or None
        src = SourceRef(fn, ln, _col(raw, seq), raw)
        acl.rules.append(AclRule(
            seq=Traced(int(seq), src), action=Traced(action, src), source=src,
            body=Traced(body, src) if body else None))


def _parse_static_route(cfg: VrpConfig, s: str, raw: str, fn: str, ln: int) -> None:
    rest = s[len("ip route-static "):].split()
    src = SourceRef(fn, ln, None, raw)
    vpn = None
    if rest[:1] == ["vpn-instance"] and len(rest) >= 2:
        vpn = Traced(rest[1], SourceRef(fn, ln, _col(raw, rest[1]), raw))
        rest = rest[2:]
    if len(rest) < 3:
        return
    dest, mask, nh = rest[0], rest[1], rest[2]
    pref = None
    if "preference" in rest:
        pi = rest.index("preference")
        if pi + 1 < len(rest) and rest[pi + 1].isdigit():
            pref = Traced(int(rest[pi + 1]), src)
    cfg.static_routes.append(StaticRoute(
        destination=Traced(dest, SourceRef(fn, ln, _col(raw, dest), raw)),
        mask=Traced(mask, src), next_hop=Traced(nh, src), source=src,
        vpn_instance=vpn, preference=pref))


def _open_zone(cfg: VrpConfig, s: str, raw: str, fn: str, ln: int) -> FirewallZone:
    rest = s[len("firewall zone "):].split()
    zone_id = None
    if rest[:1] == ["name"] and len(rest) >= 2:
        name = rest[1]
        if "id" in rest:
            i = rest.index("id")
            if i + 1 < len(rest) and rest[i + 1].isdigit():
                zone_id = Traced(int(rest[i + 1]), SourceRef(fn, ln, _col(raw, rest[i + 1]), raw))
    else:
        name = rest[0] if rest else ""
    src = SourceRef(fn, ln, _col(raw, name), raw)
    zone = FirewallZone(name=Traced(name, src), source=src, zone_id=zone_id)
    cfg.firewall_zones.append(zone)
    return zone


def _zone_line(zone: FirewallZone, s: str, raw: str, fn: str, ln: int) -> None:
    if s.startswith("set priority "):
        v = s[len("set priority "):].strip()
        if v.isdigit():
            zone.priority = Traced(int(v), SourceRef(fn, ln, _col(raw, v), raw))
    elif s.startswith("add interface "):
        v = s[len("add interface "):].strip()
        zone.interfaces.append(Traced(v, SourceRef(fn, ln, _col(raw, v), raw)))


def _secpolicy_dispatch(cfg: VrpConfig, rule: Optional[SecurityRule], s: str,
                        raw: str, fn: str, ln: int) -> Optional[SecurityRule]:
    """Handle a line inside ``security-policy``; return the current rule.

    ``rule name <name>`` opens a new rule (implicitly closing the previous one,
    which is how VRP nests rules with no ``#`` between them); other lines are
    attributes of the current rule.
    """
    if s.startswith("rule name "):
        name = s[len("rule name "):].strip()
        src = SourceRef(fn, ln, _col(raw, name), raw)
        rule = SecurityRule(name=Traced(name, src), source=src)
        cfg.security_rules.append(rule)
    elif rule is not None:
        _secrule_line(rule, s, raw, fn, ln)
    return rule


def _secrule_line(rule: SecurityRule, s: str, raw: str, fn: str, ln: int) -> None:
    def add(prefix: str, lst: List) -> None:
        v = s[len(prefix):].strip()
        lst.append(Traced(v, SourceRef(fn, ln, _col(raw, v), raw)))

    if s.startswith("source-zone "):
        add("source-zone ", rule.source_zones)
    elif s.startswith("destination-zone "):
        add("destination-zone ", rule.destination_zones)
    elif s.startswith("source-address "):
        add("source-address ", rule.source_addresses)
    elif s.startswith("destination-address "):
        add("destination-address ", rule.destination_addresses)
    elif s.startswith("service "):
        add("service ", rule.services)
    elif s.startswith("profile "):
        add("profile ", rule.profiles)
    elif s.startswith("action "):
        v = s[len("action "):].strip()
        rule.action = Traced(v, SourceRef(fn, ln, _col(raw, v), raw))
    elif s.startswith("session logging"):
        rule.session_logging = Traced(True, SourceRef(fn, ln, None, raw))


def _parse_nat_server(cfg: VrpConfig, s: str, raw: str, fn: str, ln: int) -> None:
    toks = s[len("nat server "):].split()
    kw = {"zone", "protocol", "global", "inside"}
    src = SourceRef(fn, ln, None, raw)

    def tt(tok: str) -> Traced:
        return Traced(tok, SourceRef(fn, ln, _col(raw, tok), raw))

    def after(k: str, offset: int) -> Optional[Traced]:
        if k in toks:
            i = toks.index(k) + offset
            if i < len(toks) and toks[i] not in kw:
                return tt(toks[i])
        return None

    name = tt(toks[0]) if toks and toks[0] not in kw else Traced("", src)
    cfg.nat_servers.append(NatServer(
        name=name, source=src,
        zone=after("zone", 1), protocol=after("protocol", 1),
        global_address=after("global", 1), global_port=after("global", 2),
        inside_address=after("inside", 1), inside_port=after("inside", 2)))


def _parse_hrp(cfg: VrpConfig, s: str, raw: str, fn: str, ln: int) -> None:
    src = SourceRef(fn, ln, None, raw)
    if cfg.hrp is None:
        cfg.hrp = Hrp(source=src, enabled=Traced(False, src))
    hrp = cfg.hrp
    if s == "hrp enable":
        hrp.enabled = Traced(True, src)
    elif s.startswith("hrp interface "):
        toks = s[len("hrp interface "):].split()
        if toks:
            hrp.heartbeat_interface = Traced(toks[0], SourceRef(fn, ln, _col(raw, toks[0]), raw))
        if "remote" in toks:
            i = toks.index("remote")
            if i + 1 < len(toks):
                hrp.peer = Traced(toks[i + 1], SourceRef(fn, ln, _col(raw, toks[i + 1]), raw))
    else:
        hrp.directives.append(Traced(s, src))


def parse_file(path: str) -> VrpConfig:
    with open(path, encoding="utf-8") as f:
        return parse_text(f.read(), filename=path)
