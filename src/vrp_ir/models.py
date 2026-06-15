"""Intermediate Representation (IR) for Huawei VRP configurations.

v0.1 scope (intentionally narrow, see docs/spec-v0.1.md):
  - device hostname (``sysname``)
  - interfaces: name, description, IPv4 addresses, admin state, access VLAN,
    bound VPN-instance (VRF)

Every meaningful field is wrapped in :class:`~vrp_ir.sourceref.Traced` so it
carries a :class:`~vrp_ir.sourceref.SourceRef` back to its origin line.

The IR is plain ``dataclasses`` (zero runtime dependencies) so the core library
stays small and easy to embed. Richer constructs (VRF/VLAN objects, ACL,
routing, security policies) are deferred to later milestones.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from .sourceref import SourceRef, Traced


@dataclass
class Ipv4Address:
    """An IPv4 address + prefix length parsed from an interface."""

    address: Traced[str]
    prefix_length: Traced[int]


@dataclass
class Interface:
    """A single ``interface`` stanza."""

    name: Traced[str]
    source: SourceRef  # the `interface <name>` line itself
    description: Optional[Traced[str]] = None
    ipv4: List[Ipv4Address] = field(default_factory=list)
    shutdown: Optional[Traced[bool]] = None
    access_vlan: Optional[Traced[int]] = None
    vpn_instance: Optional[Traced[str]] = None  # VRP: `ip binding vpn-instance X`


@dataclass
class VrpConfig:
    """Top-level parsed model of a single VRP configuration file."""

    source_file: str
    hostname: Optional[Traced[str]] = None
    interfaces: List[Interface] = field(default_factory=list)

    def to_dict(self) -> dict:
        """JSON-serialisable view that keeps SourceRef alongside each value."""

        def tr(t: Optional[Traced]) -> Optional[dict]:
            if t is None:
                return None
            return {"value": t.value, "source": _src(t.source)}

        return {
            "source_file": self.source_file,
            "hostname": tr(self.hostname),
            "interfaces": [
                {
                    "name": tr(itf.name),
                    "source": _src(itf.source),
                    "description": tr(itf.description),
                    "ipv4": [
                        {"address": tr(a.address), "prefix_length": tr(a.prefix_length)}
                        for a in itf.ipv4
                    ],
                    "shutdown": tr(itf.shutdown),
                    "access_vlan": tr(itf.access_vlan),
                    "vpn_instance": tr(itf.vpn_instance),
                }
                for itf in self.interfaces
            ],
        }


def _src(s: SourceRef) -> dict:
    return {"file": s.file, "line": s.line, "col": s.col}
