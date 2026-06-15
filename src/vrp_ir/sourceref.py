"""SourceRef — field-level provenance for parsed configuration facts.

This is the differentiating idea of ``vrp-ir``: every fact extracted from a
Huawei VRP configuration carries a reference back to the exact source location
(file + line, optionally column + raw text) it came from. No existing
open-source network config parser exposes field-level provenance like this
(ciscoconfparse2 only exposes an integer ``.linenum`` per line; Batfish only
surfaces file/line ranges inside parse *warnings*).

Why it matters for acceptance / audit work: when a reviewer sees a value that
looks wrong, they can jump straight to the originating line instead of grepping
the raw config by hand.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, Optional, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class SourceRef:
    """A pointer back to where a fact was read from.

    Attributes:
        file: Source file path (as given to the parser).
        line: 1-based line number.
        col: Optional 0-based column where the value token starts.
        raw: Optional raw text of the source line (handy for display/audit).
    """

    file: str
    line: int
    col: Optional[int] = None
    raw: Optional[str] = None

    def __str__(self) -> str:
        loc = f"{self.file}:{self.line}"
        if self.col is not None:
            loc += f":{self.col}"
        return loc


@dataclass(frozen=True)
class Traced(Generic[T]):
    """A value together with the :class:`SourceRef` it was parsed from."""

    value: T
    source: SourceRef

    def __str__(self) -> str:  # pragma: no cover - convenience only
        return f"{self.value!r} @ {self.source}"
