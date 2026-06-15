"""Huawei VRP config text -> :class:`VrpConfig` (v0.2 routing/switching).

Robust to VRP's `#`-delimited sections: a section opener keyword (interface /
vlan / ip vpn-instance / acl) sets the current context regardless of leading
whitespace; `#`/blank lines close it; one-line globals (sysname, ip
route-static, vlan batch, !Software Version) are dispatched by keyword.
"""
from __future__ import annotations

from typing import List, Optional

from .models import (Acl, AclRule, Interface, Ipv4Address, StaticRoute, Vlan,
                     VlanRange, Vrf, VrpConfig)
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
    ctx_kind: Optional[str] = None   # interface | vlan | vrf | acl
    ctx_obj = None

    for lineno, raw in enumerate(text.splitlines(), start=1):
        s = raw.strip()
        if not s or s == "#" or s == "return" or s == "quit":
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

        # --- one-line globals ---
        if s.startswith("sysname "):
            v = s[len("sysname "):].strip()
            cfg.hostname = Traced(v, SourceRef(filename, lineno, _col(raw, v), raw))
            continue
        if s.startswith("ip route-static "):
            _parse_static_route(cfg, s, raw, filename, lineno)
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
        rest = s[len("vpn-target "):].split()
        if rest:
            rt = rest[0]
            tr = Traced(rt, SourceRef(fn, ln, _col(raw, rt), raw))
            if "import-extcommunity" in s:
                vrf.import_targets.append(tr)
            else:
                vrf.export_targets.append(tr)


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


def parse_file(path: str) -> VrpConfig:
    with open(path, encoding="utf-8") as f:
        return parse_text(f.read(), filename=path)
