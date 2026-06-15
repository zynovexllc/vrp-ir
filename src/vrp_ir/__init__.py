"""``vrp-ir`` package: source-traceable structured IR for Huawei VRP configs.

Public API:
    >>> from vrp_ir import parse_text, parse_file
    >>> cfg = parse_text("sysname R1\\n#\\ninterface GE0/0/1\\n ip address 10.0.0.1 24\\n")
    >>> cfg.hostname.value
    'R1'
    >>> cfg.interfaces[0].ipv4[0].address.source  # provenance
    SourceRef(file='<config>', line=4, col=12, raw=' ip address 10.0.0.1 24')
"""
from .models import Interface, Ipv4Address, VrpConfig
from .parser import parse_file, parse_text
from .sourceref import SourceRef, Traced

__all__ = [
    "parse_text",
    "parse_file",
    "VrpConfig",
    "Interface",
    "Ipv4Address",
    "SourceRef",
    "Traced",
]
__version__ = "0.1.0"
