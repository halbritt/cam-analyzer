"""The typed boundary (Pillar A / D004).

No bare ``float`` crosses the CamProfile boundary. Every value is a ``Quantity``
carrying its unit, frame, and a *computed* provenance. ``provenance`` is a
monotone lattice with **no setter**: combining two quantities yields the *weakest*
input provenance (the lattice join is ``min``), so relabeling an inferred value as
measured is unconstructable (C3/D002).

This module is implemented (not a stub): it is small and load-bearing, and the
whole honesty argument depends on it behaving exactly as described.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Literal


class Provenance(IntEnum):
    """How a value came to be. Ordered: MEASURED is strongest.

    The join of two provenances is ``min`` — a result is only as trustworthy as
    its weakest input. There is deliberately no way to *raise* a value's
    provenance; trust is earned by measured support, never asserted.
    """

    EXTRAPOLATED = 0
    INFERRED = 1
    MEASURED = 2

    @staticmethod
    def join(*values: "Provenance") -> "Provenance":
        """The lattice join: the weakest (lowest) provenance among inputs."""
        if not values:
            raise ValueError("join requires at least one provenance")
        return Provenance(min(int(v) for v in values))


Unit = Literal["inch", "mm", "deg", "inch_per_deg", "inch_per_deg2", "inch_per_deg3", "inch_deg"]
Frame = Literal["valve_side", "cam_side"]


@dataclass(frozen=True, slots=True)
class Quantity:
    """An immutable, equality-by-value measurement crossing the boundary.

    Arithmetic is defined **only** between matching ``(unit, frame)`` pairs; the
    result inherits ``Provenance.join`` of the operands. A unit or frame mismatch
    is an error, not a silent coercion (C6).
    """

    magnitude: float
    unit: Unit
    frame: Frame
    provenance: Provenance

    def _require_compatible(self, other: "Quantity") -> None:
        if self.unit != other.unit or self.frame != other.frame:
            raise ValueError(
                f"incompatible quantities: ({self.unit},{self.frame}) vs "
                f"({other.unit},{other.frame}) — convert at the boundary, never implicitly"
            )

    def __add__(self, other: "Quantity") -> "Quantity":
        self._require_compatible(other)
        return Quantity(
            self.magnitude + other.magnitude,
            self.unit,
            self.frame,
            Provenance.join(self.provenance, other.provenance),
        )

    def __sub__(self, other: "Quantity") -> "Quantity":
        self._require_compatible(other)
        return Quantity(
            self.magnitude - other.magnitude,
            self.unit,
            self.frame,
            Provenance.join(self.provenance, other.provenance),
        )

    # NOTE: `.magnitude` is the documented escape hatch (round-1 risk D012). It is
    # intentionally plain so it is grep-able and lint-flaggable. Making the
    # in-system path strictly more convenient than this is the open round-2 problem.


@dataclass(frozen=True, slots=True)
class Angle:
    """A phantom-typed crank/cam angle. A crank/cam mix-up is a type error (C6)."""

    degrees: float
    frame: Literal["crank", "cam"]

    @staticmethod
    def crank(degrees: float) -> "Angle":
        return Angle(degrees % 720.0, "crank")  # periodic over the 720° cycle

    @staticmethod
    def cam(degrees: float) -> "Angle":
        return Angle(degrees % 360.0, "cam")
