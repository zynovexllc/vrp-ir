"""A small, dependency-free parser: Huawei VRP config text -> :class:`VrpConfig`.

v0.1 deliberately covers a narrow but real slice (hostname + interface basics)
with full :class:`SourceRef` provenance, rather than a broad-but-shallow parse.
Breadth (VRF/VLAN objects, ACL, routing, security policies) is future work; the
design goal is that *every* value we surface can be traced to its source line.

VRP conventions handled here:
  * ``sysname <name>`` sets the hostname.
  * ``interface <name>`` opens a stanza; indented lines belong to it until a
    ``#`` separator line or the next non-indented command.
  * ``description <text>``
  * ``ip address <addr> <mask|prefixlen>`` (dotted mask or prefix int)
  * ``shutdown`` (admin-down; VRP default is up)
  * ``port default vlan <id>`` (access VLAN)
  * ``ip binding vpn-instance <name>`` (VRF binding)
"""
from __future__ import annotations

from typing import List, Optional

from .models import Interface, Ipv4Address, VrpConfig
from .sourceref import SourceRef, Traced


def _mask_to_prefix(token: str) -> Optional[int]:
    """Convert ``255.255.255.0`` or ``24`` to an int prefix length, else None."""
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
    # A valid mask is a run of 1s followed by a run of 0s.
    if "01" in bits:
        return None
    return bits.count("1")


def _col_of(raw: str, token: str) -> Optional[int]:
    idx = raw.find(token)
    return idx if idx >= 0 else None


def parse_text(text: str, filename: str = "<config>") -> VrpConfig:
    """Parse VRP configuration *text* into a :class:`VrpConfig` with SourceRefs."""
    cfg = VrpConfig(source_file=filename)
    current: Optional[Interface] = None

    for lineno, raw in enumerate(text.splitlines(), start=1):
        stripped = raw.strip()
        if not stripped or stripped == "#":
            # `#` and blank lines close any open interface stanza.
            current = None
            continue

        indented = raw[:1].isspace()

        if not indented:
            # Top-level command -> any open interface stanza ends.
            current = None
            if stripped.startswith("sysname "):
                name = stripped[len("sysname "):].strip()
                cfg.hostname = Traced(
                    name, SourceRef(filename, lineno, _col_of(raw, name), raw))
            elif stripped.startswith("interface "):
                name = stripped[len("interface "):].strip()
                src = SourceRef(filename, lineno, _col_of(raw, name), raw)
                current = Interface(name=Traced(name, src), source=src)
                cfg.interfaces.append(current)
            continue

        # Indented line: belongs to the current interface stanza (if any).
        if current is None:
            continue
        _parse_interface_line(current, stripped, raw, filename, lineno)

    return cfg


def _parse_interface_line(
    itf: Interface, stripped: str, raw: str, filename: str, lineno: int
) -> None:
    if stripped.startswith("description "):
        val = stripped[len("description "):].strip()
        itf.description = Traced(
            val, SourceRef(filename, lineno, _col_of(raw, val), raw))
        return
    if stripped == "shutdown":
        itf.shutdown = Traced(True, SourceRef(filename, lineno, None, raw))
        return
    if stripped.startswith("ip address "):
        rest = stripped[len("ip address "):].split()
        if len(rest) >= 2:
            addr, mask_tok = rest[0], rest[1]
            prefix = _mask_to_prefix(mask_tok)
            if prefix is not None:
                src = SourceRef(filename, lineno, _col_of(raw, addr), raw)
                itf.ipv4.append(Ipv4Address(
                    address=Traced(addr, src),
                    prefix_length=Traced(prefix, src)))
        return
    if stripped.startswith("port default vlan "):
        tok = stripped[len("port default vlan "):].strip()
        if tok.isdigit():
            itf.access_vlan = Traced(
                int(tok), SourceRef(filename, lineno, _col_of(raw, tok), raw))
        return
    if stripped.startswith("ip binding vpn-instance "):
        val = stripped[len("ip binding vpn-instance "):].strip()
        itf.vpn_instance = Traced(
            val, SourceRef(filename, lineno, _col_of(raw, val), raw))
        return


def parse_file(path: str) -> VrpConfig:
    """Read *path* and parse it, using *path* as the SourceRef file name."""
    with open(path, encoding="utf-8") as f:
        return parse_text(f.read(), filename=path)
