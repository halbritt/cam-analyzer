"""Stamped scalar values for the CamProfile boundary.

``ProvFloat`` is the D012 value shape: it behaves like a float for ordinary
math, but carries the unit, frame, and provenance that make the number honest.
The only way to discard the stamp is the explicit, grep-able ``float(x)``.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum, IntEnum
from typing import Literal, TypeAlias, cast


class Provenance(IntEnum):
    """How a value came to be. Ordered: MEASURED is strongest."""

    EXTRAPOLATED = 0
    INFERRED = 1
    MEASURED = 2

    @staticmethod
    def join(*values: "Provenance") -> "Provenance":
        """Return the weakest provenance among all inputs."""
        if not values:
            raise ValueError("join requires at least one provenance")
        return Provenance(min(int(v) for v in values))


Unit: TypeAlias = str
Frame: TypeAlias = str
_Stamp: TypeAlias = tuple[Unit, Frame, Provenance]


def _unsupported_operand() -> "ProvFloat":
    # Binary dunders need this sentinel; mypy types float overrides as float-only.
    return cast("ProvFloat", NotImplemented)


class ProvFloat(float):
    """A float subclass carrying provenance, unit, and frame.

    Arithmetic with another ``ProvFloat`` requires matching unit/frame and
    propagates the weakest provenance. Arithmetic with a plain number keeps the
    stamped operand's metadata; explicit unit conversion remains a boundary
    concern, not an implicit arithmetic side effect.
    """

    __slots__ = ("_sealed", "frame", "provenance", "unit")

    unit: Unit
    frame: Frame
    provenance: Provenance
    _sealed: bool

    def __new__(
        cls,
        magnitude: float,
        unit: Unit,
        frame: Frame,
        provenance: Provenance,
    ) -> "ProvFloat":
        obj = float.__new__(cls, magnitude)
        object.__setattr__(obj, "_sealed", False)
        object.__setattr__(obj, "unit", unit)
        object.__setattr__(obj, "frame", frame)
        object.__setattr__(obj, "provenance", provenance)
        object.__setattr__(obj, "_sealed", True)
        return obj

    def __setattr__(self, name: str, value: object) -> None:
        if getattr(self, "_sealed", False):
            raise AttributeError("ProvFloat is immutable")
        object.__setattr__(self, name, value)

    @classmethod
    def inch(cls, magnitude: float, provenance: Provenance) -> "ProvFloat":
        return cls(magnitude, "inch", "valve_side", provenance)

    @classmethod
    def degree(cls, magnitude: float, provenance: Provenance) -> "ProvFloat":
        return cls(magnitude, "deg", "crank", provenance)

    @classmethod
    def ratio(cls, magnitude: float, provenance: Provenance) -> "ProvFloat":
        return cls(magnitude, "ratio", "dimensionless", provenance)

    def _metadata_for(self, other: object) -> _Stamp | None:
        if isinstance(other, ProvFloat):
            self._require_compatible(other)
            return (
                self.unit,
                self.frame,
                Provenance.join(self.provenance, other.provenance),
            )
        if isinstance(other, (int, float)):
            return self.unit, self.frame, self.provenance
        return None

    def _require_compatible(self, other: "ProvFloat") -> None:
        if self.unit != other.unit or self.frame != other.frame:
            raise ValueError(
                f"incompatible stamped values: ({self.unit},{self.frame}) vs "
                f"({other.unit},{other.frame}); convert explicitly at the boundary"
            )

    @staticmethod
    def _numeric_operand(operand: object) -> float | None:
        if isinstance(operand, (int, float)):
            return float(operand)
        return None

    @staticmethod
    def _wrap(magnitude: float, unit: Unit, frame: Frame, provenance: Provenance) -> "ProvFloat":
        return ProvFloat(magnitude, unit, frame, provenance)

    def _binary_operation(
        self,
        other: object,
        operation: Callable[[float, float], float],
    ) -> "ProvFloat":
        metadata = self._metadata_for(other)
        operand = self._numeric_operand(other)
        if metadata is None or operand is None:
            return _unsupported_operand()
        unit, frame, provenance = metadata
        return self._wrap(operation(float(self), operand), unit, frame, provenance)

    def _reverse_plain_operation(
        self,
        other: object,
        operation: Callable[[float, float], float],
    ) -> "ProvFloat":
        operand = self._numeric_operand(other)
        if operand is None:
            return _unsupported_operand()
        return self._wrap(operation(operand, float(self)), self.unit, self.frame, self.provenance)

    def __add__(self, other: object) -> "ProvFloat":
        return self._binary_operation(other, lambda left, right: left + right)

    def __radd__(self, other: object) -> "ProvFloat":
        return self.__add__(other)

    def __sub__(self, other: object) -> "ProvFloat":
        return self._binary_operation(other, lambda left, right: left - right)

    def __rsub__(self, other: object) -> "ProvFloat":
        return self._reverse_plain_operation(other, lambda left, right: left - right)

    def __mul__(self, other: object) -> "ProvFloat":
        return self._binary_operation(other, lambda left, right: left * right)

    def __rmul__(self, other: object) -> "ProvFloat":
        return self.__mul__(other)

    def __truediv__(self, other: object) -> "ProvFloat":
        return self._binary_operation(other, lambda left, right: left / right)

    def __rtruediv__(self, other: object) -> "ProvFloat":
        return self._reverse_plain_operation(other, lambda left, right: left / right)

    def __neg__(self) -> "ProvFloat":
        return self._wrap(-float(self), self.unit, self.frame, self.provenance)

    def __pos__(self) -> "ProvFloat":
        return self._wrap(+float(self), self.unit, self.frame, self.provenance)

    def __abs__(self) -> "ProvFloat":
        return self._wrap(abs(float(self)), self.unit, self.frame, self.provenance)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ProvFloat):
            return False
        return (
            float(self) == float(other)
            and self.unit == other.unit
            and self.frame == other.frame
            and self.provenance == other.provenance
        )

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash((float(self), self.unit, self.frame, self.provenance))

    def __repr__(self) -> str:
        return (
            f"ProvFloat({float(self)!r}, unit={self.unit!r}, frame={self.frame!r}, "
            f"provenance={self.provenance.name})"
        )

    def __str__(self) -> str:
        return f"{float(self)} [{self.provenance.name} {self.unit} {self.frame}]"

    def __format__(self, spec: str) -> str:
        return f"{format(float(self), spec)} [{self.provenance.name} {self.unit} {self.frame}]"


# Backward-compatible import name during the D012 transition. In-system code uses
# ProvFloat directly; there is intentionally no .magnitude escape hatch.
Quantity: TypeAlias = ProvFloat


@dataclass(frozen=True, slots=True)
class Refusal:
    """A first-class refusal result instead of fabricated precision."""

    requested: str
    reason: str
    remedy: str
    provenance: Provenance | None = None

    def __bool__(self) -> bool:
        return False


Answer: TypeAlias = ProvFloat | Refusal


class SafetyVerdict(Enum):
    """Verdicts for cliff analyses whose evidence may be insufficient."""

    PASS = "PASS"
    FAIL = "FAIL"
    UNDECIDABLE_FROM_CAM_CARD = "UNDECIDABLE FROM CAM CARD"


@dataclass(frozen=True, slots=True)
class VerdictResult:
    """A named safety verdict with the evidence stamp that supports it."""

    requested: str
    verdict: SafetyVerdict
    reason: str
    remedy: str | None = None
    provenance: Provenance | None = None


Result: TypeAlias = ProvFloat | Refusal | VerdictResult


@dataclass(frozen=True, slots=True)
class Angle:
    """A phantom-typed crank/cam angle. Crank values are periodic over 720 deg."""

    degrees: float
    frame: Literal["crank", "cam"]

    @staticmethod
    def crank(degrees: float) -> "Angle":
        return Angle(degrees % 720.0, "crank")

    @staticmethod
    def cam(degrees: float) -> "Angle":
        return Angle(degrees % 360.0, "cam")

    def require_crank(self) -> float:
        if self.frame != "crank":
            raise ValueError(f"expected crank angle, got {self.frame}")
        return self.degrees


__all__ = [
    "Angle",
    "Answer",
    "Frame",
    "ProvFloat",
    "Provenance",
    "Quantity",
    "Refusal",
    "Result",
    "SafetyVerdict",
    "Unit",
    "VerdictResult",
]
