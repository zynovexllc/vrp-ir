"""Intermediate Representation (IR) for Huawei VRP configurations.

v0.2 scope (routing/switching): hostname, software version, VLANs (incl. batch
ranges), VRFs (vpn-instance + RD/RT), interfaces (link-type, default/trunk
VLANs incl. ranges, Eth-Trunk membership, dot1q subinterfaces, secondary IPv4,
VRF binding, admin state), ACLs (number/name + rules), static routes.

Every meaningful field is wrapped in :class:`~vrp_ir.sourceref.Traced` so it
carries a :class:`~vrp_ir.sourceref.SourceRef` back to its origin line. The IR
is plain ``dataclasses`` (zero runtime dependencies).

USG firewall objects (zone / security-policy / nat / hrp) are added in a later
milestone and slot into the same generic serializer below.
"""
from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from typing import List, Optional

from .sourceref import SourceRef, Traced


@dataclass
class Ipv4Address:
    address: Traced[str]
    prefix_length: Traced[int]
    is_secondary: bool = False


@dataclass
class VlanRange:
    """A VLAN id or an inclusive range (``vlan batch 1000 to 1002``)."""
    start: int
    end: int  # == start for a single VLAN
    source: SourceRef


@dataclass
class Vlan:
    vlan_id: Traced[int]
    source: SourceRef
    description: Optional[Traced[str]] = None


@dataclass
class Vrf:
    name: Traced[str]
    source: SourceRef
    route_distinguisher: Optional[Traced[str]] = None
    export_targets: List[Traced[str]] = field(default_factory=list)
    import_targets: List[Traced[str]] = field(default_factory=list)


@dataclass
class AclRule:
    seq: Traced[int]
    action: Traced[str]            # permit | deny
    source: SourceRef
    body: Optional[Traced[str]] = None  # remaining match text (raw, traced)


@dataclass
class Acl:
    identifier: Traced[str]        # number (e.g. "3000") or name
    source: SourceRef
    kind: Optional[Traced[str]] = None  # basic | advance (named ACLs)
    rules: List[AclRule] = field(default_factory=list)


@dataclass
class StaticRoute:
    destination: Traced[str]
    mask: Traced[str]
    next_hop: Traced[str]
    source: SourceRef
    vpn_instance: Optional[Traced[str]] = None
    preference: Optional[Traced[int]] = None


@dataclass
class Interface:
    name: Traced[str]
    source: SourceRef
    description: Optional[Traced[str]] = None
    ipv4: List[Ipv4Address] = field(default_factory=list)
    shutdown: Optional[Traced[bool]] = None
    link_type: Optional[Traced[str]] = None       # access | trunk | hybrid
    default_vlan: Optional[Traced[int]] = None     # port default vlan <id>
    trunk_vlans: List[VlanRange] = field(default_factory=list)  # allow-pass
    eth_trunk: Optional[Traced[int]] = None        # member: eth-trunk <id>
    dot1q_vlan: Optional[Traced[int]] = None       # subif: vlan-type dot1q <id>
    vpn_instance: Optional[Traced[str]] = None     # ip binding vpn-instance <x>


@dataclass
class VrpConfig:
    source_file: str
    software_version: Optional[Traced[str]] = None
    hostname: Optional[Traced[str]] = None
    vlan_batches: List[VlanRange] = field(default_factory=list)
    vlans: List[Vlan] = field(default_factory=list)
    vrfs: List[Vrf] = field(default_factory=list)
    acls: List[Acl] = field(default_factory=list)
    interfaces: List[Interface] = field(default_factory=list)
    static_routes: List[StaticRoute] = field(default_factory=list)

    def to_dict(self) -> dict:
        """JSON-serialisable view; keeps SourceRef alongside each traced value."""
        return _to_jsonable(self)


def _to_jsonable(obj):
    """Recursively serialise IR objects, Traced values and SourceRefs to JSON.

    - Traced -> {"value": <jsonable>, "source": <sourceref>}
    - SourceRef -> {"file","line","col"}
    - dataclass -> {field: jsonable}  (None fields omitted to keep output lean)
    - list -> [jsonable]
    """
    if isinstance(obj, Traced):
        return {"value": _to_jsonable(obj.value), "source": _to_jsonable(obj.source)}
    if isinstance(obj, SourceRef):
        return {"file": obj.file, "line": obj.line, "col": obj.col}
    if is_dataclass(obj) and not isinstance(obj, type):
        out = {}
        for f in fields(obj):
            val = getattr(obj, f.name)
            if val is None or (isinstance(val, list) and not val):
                continue
            out[f.name] = _to_jsonable(val)
        return out
    if isinstance(obj, list):
        return [_to_jsonable(x) for x in obj]
    return obj
