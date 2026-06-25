"""Huawei VRP config text -> :class:`VrpConfig` (routing/switching + USG firewall).

Robust to VRP's `#`-delimited sections: a section opener keyword (interface /
vlan / ip vpn-instance / acl / firewall zone / security-policy / nat-policy)
sets the current context regardless of leading whitespace; `#`/`return`/`quit`
close it (blank lines do not); one-line globals (sysname, ip route-static, vlan
batch, nat server, ntp server, hrp, !Software Version) are dispatched by keyword.
"""
from __future__ import annotations

from typing import List, Optional

from .models import (Acl, AclRule, AddressSet, AddressSetMember, FirewallZone,
                     Hrp, Interface, Ipv4Address, LocalUser, NatPolicyRule,
                     NatServer, NtpServer, SecurityRule, ServiceSet,
                     ServiceSetItem, StaticRoute, UserInterface, Vlan,
                     VlanRange, Vrf, VrpConfig, SnmpCommunity)
from .sourceref import SourceRef, Traced

_CONFIG_ENCODINGS = ("utf-8-sig", "gb18030")


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
    ctx_kind: Optional[str] = None   # interface | vlan | vrf | acl | fwzone | secpolicy | natpolicy
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
                cfg.analyzed_line_count += 1
                v = s[len("!Software Version"):].strip()
                cfg.software_version = Traced(v, SourceRef(filename, lineno, _col(raw, v), raw))
            continue

        cfg.analyzed_line_count += 1

        # --- section openers (match regardless of leading whitespace) ---
        # For user-interface body: dispatch before section-opener checks so that
        # sub-commands like `acl 2000 inbound` are not mistaken for new contexts.
        if ctx_kind == "userif":
            if not _user_interface_line(ctx_obj, s, raw, filename, lineno):
                cfg.unparsed_lines.append(SourceRef(filename, lineno, None, raw))
            continue

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
        if s == "nat-policy":
            ctx_kind, ctx_obj = "natpolicy", None
            continue
        if s.startswith("ip address-set "):
            ctx_obj = _open_address_set(cfg, s, raw, filename, lineno)
            ctx_kind = "addrset"
            continue
        if s.startswith("ip service-set "):
            ctx_obj = _open_service_set(cfg, s, raw, filename, lineno)
            ctx_kind = "svcset"
            continue
        if s.startswith("user-interface "):
            ctx_obj = _open_user_interface(cfg, s, raw, filename, lineno)
            ctx_kind = "userif"
            continue
        if s == "aaa":
            ctx_kind, ctx_obj = "aaa", None
            continue

        # --- one-line globals ---
        if s.startswith("sysname "):
            v = s[len("sysname "):].strip()
            cfg.hostname = Traced(v, SourceRef(filename, lineno, _col(raw, v), raw))
            continue
        if s.startswith("ip route-static "):
            _parse_static_route(cfg, s, raw, filename, lineno)
            continue
        if (
            s.startswith("ntp-service unicast-server ")
            or s.startswith("ntp unicast-server ")
        ):
            _parse_ntp_server(cfg, s, raw, filename, lineno)
            continue
        if s.startswith("snmp-agent community "):
            _parse_snmp_community(cfg, s, raw, filename, lineno)
            continue
        if s.startswith("nat server "):
            _parse_nat_server(cfg, s, raw, filename, lineno)
            continue
        if s.startswith("hrp "):
            _parse_hrp(cfg, s, raw, filename, lineno)
            continue
        if s == "telnet server enable":
            src = SourceRef(filename, lineno, None, raw)
            cfg.telnet_server_enabled = Traced(True, src)
            continue
        if s == "undo telnet server enable":
            src = SourceRef(filename, lineno, None, raw)
            cfg.telnet_server_enabled = Traced(False, src)
            continue
        if s == "http server enable":
            src = SourceRef(filename, lineno, None, raw)
            cfg.http_server_enabled = Traced(True, src)
            continue
        if s == "undo http server enable":
            src = SourceRef(filename, lineno, None, raw)
            cfg.http_server_enabled = Traced(False, src)
            continue
        if s.startswith("ssh server cipher "):
            _parse_ssh_server_cipher(cfg, s, raw, filename, lineno)
            continue

        # --- body lines: dispatch to current context ---
        parsed = False
        if ctx_kind == "interface":
            parsed = _iface_line(ctx_obj, s, raw, filename, lineno)
        elif ctx_kind == "vlan":
            parsed = _vlan_line(ctx_obj, s, raw, filename, lineno)
        elif ctx_kind == "vrf":
            parsed = _vrf_line(ctx_obj, s, raw, filename, lineno)
        elif ctx_kind == "acl":
            parsed = _acl_line(ctx_obj, s, raw, filename, lineno)
        elif ctx_kind == "fwzone":
            parsed = _zone_line(ctx_obj, s, raw, filename, lineno)
        elif ctx_kind == "secpolicy":
            ctx_obj, parsed = _secpolicy_dispatch(cfg, ctx_obj, s, raw, filename, lineno)
        elif ctx_kind == "natpolicy":
            ctx_obj, parsed = _natpolicy_dispatch(cfg, ctx_obj, s, raw, filename, lineno)
        elif ctx_kind == "addrset":
            parsed = _address_set_line(ctx_obj, s, raw, filename, lineno)
        elif ctx_kind == "svcset":
            parsed = _service_set_line(ctx_obj, s, raw, filename, lineno)
        elif ctx_kind == "userif":
            parsed = _user_interface_line(ctx_obj, s, raw, filename, lineno)
        elif ctx_kind == "aaa":
            parsed = _aaa_line(cfg, s, raw, filename, lineno)
        if not parsed:
            cfg.unparsed_lines.append(SourceRef(filename, lineno, None, raw))

    return cfg


def _iface_line(itf: Interface, s: str, raw: str, fn: str, ln: int) -> bool:
    if s.startswith("description "):
        v = s[len("description "):].strip()
        itf.description = Traced(v, SourceRef(fn, ln, _col(raw, v), raw))
        return True
    elif s == "shutdown":
        itf.shutdown = Traced(True, SourceRef(fn, ln, None, raw))
        return True
    elif s.startswith("ip address "):
        rest = s[len("ip address "):].split()
        if len(rest) >= 2:
            prefix = _mask_to_prefix(rest[1])
            if prefix is not None:
                src = SourceRef(fn, ln, _col(raw, rest[0]), raw)
                itf.ipv4.append(Ipv4Address(Traced(rest[0], src), Traced(prefix, src),
                                            is_secondary=(len(rest) >= 3 and rest[2] == "sub")))
        return True
    elif s.startswith("ip binding vpn-instance "):
        v = s[len("ip binding vpn-instance "):].strip()
        itf.vpn_instance = Traced(v, SourceRef(fn, ln, _col(raw, v), raw))
        return True
    elif s.startswith("port link-type "):
        v = s[len("port link-type "):].strip()
        itf.link_type = Traced(v, SourceRef(fn, ln, _col(raw, v), raw))
        return True
    elif s.startswith("port default vlan "):
        v = s[len("port default vlan "):].strip()
        if v.isdigit():
            itf.default_vlan = Traced(int(v), SourceRef(fn, ln, _col(raw, v), raw))
        return True
    elif s.startswith("port trunk allow-pass vlan "):
        toks = s[len("port trunk allow-pass vlan "):].split()
        itf.trunk_vlans.extend(_parse_vlan_ranges(toks, SourceRef(fn, ln, None, raw)))
        return True
    elif s.startswith("eth-trunk "):
        v = s[len("eth-trunk "):].strip()
        if v.isdigit():
            itf.eth_trunk = Traced(int(v), SourceRef(fn, ln, _col(raw, v), raw))
        return True
    elif s.startswith("vlan-type dot1q "):
        v = s[len("vlan-type dot1q "):].strip()
        if v.isdigit():
            itf.dot1q_vlan = Traced(int(v), SourceRef(fn, ln, _col(raw, v), raw))
        return True
    return False


def _vlan_line(vlan: Vlan, s: str, raw: str, fn: str, ln: int) -> bool:
    if s.startswith("description "):
        v = s[len("description "):].strip()
        vlan.description = Traced(v, SourceRef(fn, ln, _col(raw, v), raw))
        return True
    return False


def _vrf_line(vrf: Vrf, s: str, raw: str, fn: str, ln: int) -> bool:
    if s.startswith("route-distinguisher "):
        v = s[len("route-distinguisher "):].strip()
        vrf.route_distinguisher = Traced(v, SourceRef(fn, ln, _col(raw, v), raw))
        return True
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
        return True
    return False


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


def _acl_line(acl: Acl, s: str, raw: str, fn: str, ln: int) -> bool:
    if not s.startswith("rule "):
        return False
    rest = s[len("rule "):].split()
    if len(rest) >= 2 and rest[0].isdigit() and rest[1] in ("permit", "deny"):
        seq, action = rest[0], rest[1]
        body = " ".join(rest[2:]) or None
        src = SourceRef(fn, ln, _col(raw, seq), raw)
        acl.rules.append(AclRule(
            seq=Traced(int(seq), src), action=Traced(action, src), source=src,
            body=Traced(body, src) if body else None))
    return True


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


def _parse_ntp_server(cfg: VrpConfig, s: str, raw: str, fn: str, ln: int) -> None:
    if s.startswith("ntp-service unicast-server "):
        rest = s[len("ntp-service unicast-server "):].split()
    elif s.startswith("ntp unicast-server "):
        rest = s[len("ntp unicast-server "):].split()
    else:
        return
    if not rest:
        return

    address = rest[0]
    src = SourceRef(fn, ln, _col(raw, address), raw)
    vpn = None
    if "vpn-instance" in rest:
        i = rest.index("vpn-instance")
        if i + 1 < len(rest):
            vpn_name = rest[i + 1]
            vpn = Traced(vpn_name, SourceRef(fn, ln, _col(raw, vpn_name), raw))

    cfg.ntp_servers.append(NtpServer(
        address=Traced(address, src), source=src, vpn_instance=vpn))


def _parse_snmp_community(cfg: VrpConfig, s: str, raw: str, fn: str, ln: int) -> None:
    rest = s[len("snmp-agent community "):].split()
    if len(rest) < 2 or rest[0] not in ("read", "write"):
        return

    access = rest[0]
    access_src = SourceRef(fn, ln, _col(raw, access), raw)
    community = None
    encrypted = None
    if rest[1] == "cipher":
        encrypted = Traced(True, SourceRef(fn, ln, _col(raw, rest[1]), raw))
    else:
        community = Traced(rest[1], SourceRef(fn, ln, _col(raw, rest[1]), raw))

    cfg.snmp_communities.append(SnmpCommunity(
        access_mode=Traced(access, access_src),
        source=access_src,
        community=community,
        encrypted=encrypted,
    ))


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
        name = rest[0] if rest and rest[0] != "name" else ""
    src = SourceRef(fn, ln, _col(raw, name), raw)
    zone = FirewallZone(name=Traced(name, src), source=src, zone_id=zone_id)
    cfg.firewall_zones.append(zone)
    return zone


def _zone_line(zone: FirewallZone, s: str, raw: str, fn: str, ln: int) -> bool:
    if s.startswith("set priority "):
        v = s[len("set priority "):].strip()
        if v.isdigit():
            zone.priority = Traced(int(v), SourceRef(fn, ln, _col(raw, v), raw))
        return True
    elif s.startswith("add interface "):
        v = s[len("add interface "):].strip()
        zone.interfaces.append(Traced(v, SourceRef(fn, ln, _col(raw, v), raw)))
        return True
    return False


def _secpolicy_dispatch(cfg: VrpConfig, rule: Optional[SecurityRule], s: str,
                        raw: str, fn: str, ln: int):
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
        return rule, True
    elif s.startswith("default action ") or s.startswith("default-action "):
        # Policy-level default for traffic matching no rule. `default action
        # permit` is permit-any — the single most important fact NOT to lose,
        # and it is NOT a rule attribute (it can appear before any rule).
        prefix = "default action " if s.startswith("default action ") else "default-action "
        v = s[len(prefix):].strip()
        cfg.security_default_action = Traced(v, SourceRef(fn, ln, _col(raw, v), raw))
        return rule, True
    elif rule is not None:
        return rule, _secrule_line(rule, s, raw, fn, ln)
    return rule, False


def _secrule_line(rule: SecurityRule, s: str, raw: str, fn: str, ln: int) -> bool:
    if _policy_rule_line(rule, s, raw, fn, ln):
        return True
    if add("profile ", rule.profiles, s, raw, fn, ln):
        return True
    if s.startswith("session logging"):
        rule.session_logging = Traced(True, SourceRef(fn, ln, None, raw))
        return True
    return False


def _natpolicy_dispatch(cfg: VrpConfig, rule: Optional[NatPolicyRule], s: str,
                        raw: str, fn: str, ln: int):
    if s.startswith("rule name "):
        name = s[len("rule name "):].strip()
        src = SourceRef(fn, ln, _col(raw, name), raw)
        rule = NatPolicyRule(name=Traced(name, src), source=src)
        cfg.nat_policy_rules.append(rule)
        return rule, True
    elif rule is not None:
        return rule, _natpolicy_rule_line(rule, s, raw, fn, ln)
    return rule, False


def _natpolicy_rule_line(rule: NatPolicyRule, s: str, raw: str, fn: str, ln: int) -> bool:
    return _policy_rule_line(rule, s, raw, fn, ln)


def _open_address_set(cfg: VrpConfig, s: str, raw: str, fn: str, ln: int) -> AddressSet:
    rest = s[len("ip address-set "):].split()
    name = rest[0] if rest else ""
    set_type = None
    if "type" in rest:
        i = rest.index("type")
        if i + 1 < len(rest):
            set_type = Traced(rest[i + 1], SourceRef(fn, ln, _col(raw, rest[i + 1]), raw))
    src = SourceRef(fn, ln, _col(raw, name) if name else None, raw)
    aset = AddressSet(name=Traced(name, src), source=src, set_type=set_type)
    cfg.address_sets.append(aset)
    return aset


def _address_set_line(aset: AddressSet, s: str, raw: str, fn: str, ln: int) -> bool:
    if not s.startswith("address "):
        return False
    rest = s[len("address "):].split()
    if not rest:
        return True
    seq = rest[0]
    seq_src = SourceRef(fn, ln, _col(raw, seq), raw)
    member = AddressSetMember(seq=Traced(seq, seq_src), source=seq_src)
    body = rest[1:]
    if body:
        first = body[0]
        member.address = Traced(first, SourceRef(fn, ln, _col(raw, first), raw))
        if "mask" in body:
            mi = body.index("mask")
            if mi + 1 < len(body) and body[mi + 1].isdigit():
                n = int(body[mi + 1])
                if 0 <= n <= 32:
                    member.prefix_length = Traced(n, SourceRef(fn, ln, _col(raw, body[mi + 1]), raw))
        member.expression = Traced(" ".join(body), SourceRef(fn, ln, _col(raw, first), raw))
    aset.members.append(member)
    return True


def _open_service_set(cfg: VrpConfig, s: str, raw: str, fn: str, ln: int) -> ServiceSet:
    rest = s[len("ip service-set "):].split()
    name = rest[0] if rest else ""
    set_type = None
    if "type" in rest:
        i = rest.index("type")
        if i + 1 < len(rest):
            set_type = Traced(rest[i + 1], SourceRef(fn, ln, _col(raw, rest[i + 1]), raw))
    src = SourceRef(fn, ln, _col(raw, name) if name else None, raw)
    sset = ServiceSet(name=Traced(name, src), source=src, set_type=set_type)
    cfg.service_sets.append(sset)
    return sset


def _service_set_line(sset: ServiceSet, s: str, raw: str, fn: str, ln: int) -> bool:
    if not s.startswith("service "):
        return False
    rest = s[len("service "):].split()
    if not rest:
        return True
    seq = rest[0]
    seq_src = SourceRef(fn, ln, _col(raw, seq), raw)
    item = ServiceSetItem(seq=Traced(seq, seq_src), source=seq_src)
    body = rest[1:]
    if body:
        item.expression = Traced(" ".join(body), SourceRef(fn, ln, _col(raw, body[0]), raw))
    sset.items.append(item)
    return True


def add(prefix: str, lst: List[Traced[str]], s: str, raw: str, fn: str, ln: int) -> bool:
    if not s.startswith(prefix):
        return False
    v = s[len(prefix):].strip()
    lst.append(Traced(v, SourceRef(fn, ln, _col(raw, v), raw)))
    return True


def _policy_rule_line(rule, s: str, raw: str, fn: str, ln: int) -> bool:
    if add("source-zone ", rule.source_zones, s, raw, fn, ln):
        return True
    if add("destination-zone ", rule.destination_zones, s, raw, fn, ln):
        return True
    if add("source-address ", rule.source_addresses, s, raw, fn, ln):
        return True
    if add("destination-address ", rule.destination_addresses, s, raw, fn, ln):
        return True
    if add("service ", rule.services, s, raw, fn, ln):
        return True
    if s.startswith("action "):
        v = s[len("action "):].strip()
        rule.action = Traced(v, SourceRef(fn, ln, _col(raw, v), raw))
        return True
    return False


def _parse_nat_server(cfg: VrpConfig, s: str, raw: str, fn: str, ln: int) -> None:
    toks = s[len("nat server "):].split()
    kw = {"zone", "protocol", "global", "inside"}
    src = SourceRef(fn, ln, None, raw)

    # Per-token columns via an advancing cursor, so repeated values (e.g. the
    # same port on `global` and `inside`) each resolve to their own occurrence.
    pos = raw.find("nat server")
    pos = pos + len("nat server") if pos >= 0 else 0
    cols: List[Optional[int]] = []
    for t in toks:
        i = raw.find(t, pos)
        cols.append(i if i >= 0 else None)
        pos = i + len(t) if i >= 0 else pos

    def tt(i: int) -> Traced:
        return Traced(toks[i], SourceRef(fn, ln, cols[i], raw))

    def slot(k: str, offset: int) -> Optional[Traced]:
        if k not in toks:
            return None
        i = toks.index(k)
        # A port (offset 2) is only meaningful if the address (offset 1) is a
        # real value; otherwise reading offset 2 would borrow the next field.
        if offset == 2 and (i + 1 >= len(toks) or toks[i + 1] in kw):
            return None
        j = i + offset
        if j < len(toks) and toks[j] not in kw:
            return tt(j)
        return None

    name = tt(0) if toks and toks[0] not in kw else Traced("", src)
    cfg.nat_servers.append(NatServer(
        name=name, source=src,
        zone=slot("zone", 1), protocol=slot("protocol", 1),
        global_address=slot("global", 1), global_port=slot("global", 2),
        inside_address=slot("inside", 1), inside_port=slot("inside", 2)))


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


def _open_user_interface(cfg: VrpConfig, s: str, raw: str, fn: str, ln: int) -> UserInterface:
    rest = s[len("user-interface "):].split()
    src = SourceRef(fn, ln, None, raw)
    if not rest:
        ui = UserInterface(kind=Traced("", src), first=Traced(0, src), source=src)
        cfg.user_interfaces.append(ui)
        return ui
    kind_tok = rest[0]  # "con" or "vty"
    kind_src = SourceRef(fn, ln, _col(raw, kind_tok), raw)
    first_val = 0
    first_src = src
    last_val = None
    if len(rest) >= 2 and rest[1].isdigit():
        first_val = int(rest[1])
        first_src = SourceRef(fn, ln, _col(raw, rest[1]), raw)
    if len(rest) >= 3 and rest[2].isdigit():
        last_val = Traced(int(rest[2]), SourceRef(fn, ln, _col(raw, rest[2]), raw))
    ui = UserInterface(
        kind=Traced(kind_tok, kind_src),
        first=Traced(first_val, first_src),
        source=src,
        last=last_val,
    )
    cfg.user_interfaces.append(ui)
    return ui


def _user_interface_line(ui: UserInterface, s: str, raw: str, fn: str, ln: int) -> bool:
    if s.startswith("protocol inbound "):
        v = s[len("protocol inbound "):].strip()
        ui.protocol_inbound.append(Traced(v, SourceRef(fn, ln, _col(raw, v), raw)))
        return True
    elif s.startswith("acl ") and "inbound" in s:
        toks = s[len("acl "):].split()
        acl_id = toks[0] if toks else ""
        ui.acl_inbound = Traced(acl_id, SourceRef(fn, ln, _col(raw, acl_id), raw))
        return True
    elif s.startswith("authentication-mode "):
        v = s[len("authentication-mode "):].strip()
        ui.authentication_mode = Traced(v, SourceRef(fn, ln, _col(raw, v), raw))
        return True
    elif s.startswith("user privilege level "):
        v = s[len("user privilege level "):].strip()
        if v.isdigit():
            ui.privilege_level = Traced(int(v), SourceRef(fn, ln, _col(raw, v), raw))
        return True
    return False


def _parse_ssh_server_cipher(cfg: VrpConfig, s: str, raw: str, fn: str, ln: int) -> None:
    """Parse 'ssh server cipher <tok1> <tok2> ...' collecting each token with its column."""
    rest = s[len("ssh server cipher "):]
    toks = rest.split()
    prefix_end = raw.find("ssh server cipher ")
    search_from = (prefix_end + len("ssh server cipher ")) if prefix_end >= 0 else 0
    for tok in toks:
        col = raw.find(tok, search_from)
        if col >= 0:
            search_from = col + len(tok)
            cfg.ssh_server_ciphers.append(Traced(tok, SourceRef(fn, ln, col, raw)))
        else:
            cfg.ssh_server_ciphers.append(Traced(tok, SourceRef(fn, ln, None, raw)))


def _aaa_line(cfg: VrpConfig, s: str, raw: str, fn: str, ln: int) -> bool:
    """Parse ``local-user NAME service-type TYPE [TYPE ...]`` inside the aaa block."""
    if not s.startswith("local-user "):
        return False
    rest = s[len("local-user "):].split()
    if len(rest) < 3 or rest[1] != "service-type":
        return True
    name_tok = rest[0]
    name_src = SourceRef(fn, ln, _col(raw, name_tok), raw)
    src = SourceRef(fn, ln, None, raw)
    svc_start = raw.find("service-type")
    search_from = (svc_start + len("service-type ")) if svc_start >= 0 else 0
    service_types: List[Traced[str]] = []
    for tok in rest[2:]:
        col = raw.find(tok, search_from)
        if col >= 0:
            search_from = col + len(tok)
            service_types.append(Traced(tok, SourceRef(fn, ln, col, raw)))
        else:
            service_types.append(Traced(tok, SourceRef(fn, ln, None, raw)))
    cfg.local_users.append(LocalUser(name=Traced(name_tok, name_src),
                                     service_types=service_types, source=src))
    return True


def parse_file(path: str) -> VrpConfig:
    last_error: Optional[UnicodeDecodeError] = None
    for encoding in _CONFIG_ENCODINGS:
        try:
            with open(path, encoding=encoding) as f:
                return parse_text(f.read(), filename=path)
        except UnicodeDecodeError as exc:
            last_error = exc
    if last_error is not None:
        raise last_error
    raise RuntimeError("no configuration encodings configured")
