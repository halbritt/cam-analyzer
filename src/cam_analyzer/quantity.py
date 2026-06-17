"""Sealed, phantom-typed stamped values for the CamProfile boundary (RFC 0001).

A :class:`Quantity` is the value shape the boundary speaks: a magnitude in a
unit/frame carrying the :class:`Provenance` that says whether the number was
``MEASURED``, ``INFERRED``, or ``EXTRAPOLATED``. Two honesty invariants are
enforced by *mechanism*, not convention:

* **Sealed construction (Pillar A / C3).** ``Quantity`` cannot be built directly;
  the constructor demands a module-private mint token. Provenance is *conferred*
  by acquisition factories (:func:`measured` / :func:`inferred` /
  :func:`extrapolated`) and only ever *descends* through combinators (arithmetic
  min-joins its inputs). No public callable accepts a ``provenance=`` argument, so
  a value can neither fabricate ``MEASURED`` from nothing nor raise its own
  provenance by being reconstructed. ``measured()`` confers the strongest stamp
  and is confined to the source layer (see ``tests/test_conformance_traps.py``).
* **Phantom-typed units & frames (Pillar B / C6).** The unit is a *type parameter*
  ``U`` (an empty marker class), so ``mm(5) + inch(1)`` is a ``mypy`` error, not a
  runtime hope; angles are phantom-typed by frame (``Angle[Crank]`` /
  ``Angle[Cam]``) so a cam angle passed where a crank angle is required is a type
  error too.

There is no ``.magnitude`` escape hatch. The one grep-able exit to a bare scalar
is ``float(x)``; rendering goes through ``__format__``/``__str__``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any, ClassVar, Final, Generic, Literal, TypeAlias, TypeVar


class Provenance(IntEnum):
    """How a value came to be. Ordered: MEASURED is strongest (min-join descends)."""

    EXTRAPOLATED = 0
    INFERRED = 1
    MEASURED = 2

    @staticmethod
    def join(*values: "Provenance") -> "Provenance":
        """Return the weakest provenance among all inputs (the lattice meet)."""
        if not values:
            raise ValueError("join requires at least one provenance")
        return Provenance(min(int(v) for v in values))


# --- Phantom unit tags -------------------------------------------------------
# Empty marker classes that exist only at the type level. They never get
# instantiated; their ``symbol`` is the runtime unit string a factory stamps.
class UnitTag:
    """Base for phantom unit markers; ``symbol`` is the runtime unit string."""

    symbol: ClassVar[str] = "?"


class Inch(UnitTag):
    symbol = "inch"


class Mm(UnitTag):
    symbol = "mm"


class InchPerDeg(UnitTag):
    symbol = "inch_per_deg"


class InchPerDeg2(UnitTag):
    symbol = "inch_per_deg2"


class InchPerDeg3(UnitTag):
    symbol = "inch_per_deg3"


class InchDeg(UnitTag):
    symbol = "inch_deg"


U = TypeVar("U", bound=UnitTag)

Unit: TypeAlias = str  # runtime unit string (kept for messages / back-compat)
Frame: TypeAlias = str

_MINT: Final = object()  # module-private mint token; never exported
_SPENT: Final = object()  # what a minted value stores instead, so it can't be re-minted


@dataclass(frozen=True, repr=False)
class Quantity(Generic[U]):
    """A sealed, phantom-typed stamped scalar.

    The phantom ``U`` carries the unit at the type level; ``unit``/``frame`` carry
    it at runtime for messages and the defence-in-depth compatibility check.
    Construct only via the acquisition factories or arithmetic combinators — the
    ``_token`` seal makes a bare ``Quantity(...)`` raise.
    """

    _value: float
    unit: str
    frame: str
    provenance: Provenance
    _token: object = field(compare=False)

    def __post_init__(self) -> None:
        if self._token is not _MINT:
            raise TypeError(
                "Quantity is sealed; mint via measured()/inferred()/extrapolated() "
                "or an arithmetic combinator, never by direct construction"
            )
        # Spend the token so a minted value cannot be re-minted by carrying its
        # stored token back through dataclasses.replace()/copy/pickle — which would
        # otherwise let `replace(q, provenance=MEASURED)` raise a value's provenance.
        object.__setattr__(self, "_token", _SPENT)

    @classmethod
    def _mint(cls, value: float, unit: str, frame: str, provenance: Provenance) -> "Quantity[Any]":
        """The single keyed construction point (projection / combinator mint)."""
        return cls(value, unit, frame, provenance, _MINT)

    def __reduce__(self) -> tuple[Any, tuple[float, str, str, Provenance]]:
        # Route pickle/copy back through the keyed mint instead of re-running
        # __init__ with the spent token (which would raise). Provenance is
        # preserved, never conferred — this is not a way to fabricate MEASURED.
        return (_unpickle_quantity, (self._value, self.unit, self.frame, self.provenance))

    # ---- the one grep-able exit ----
    def __float__(self) -> float:
        return self._value

    # ---- combinators: arithmetic descends provenance, never raises it ----
    def _require_compatible(self, other: "Quantity[Any]") -> None:
        if self.unit != other.unit or self.frame != other.frame:
            raise ValueError(
                f"incompatible stamped values: ({self.unit},{self.frame}) vs "
                f"({other.unit},{other.frame}); convert explicitly at the boundary"
            )

    def __add__(self, other: "Quantity[U]") -> "Quantity[U]":
        if not isinstance(other, Quantity):
            return NotImplemented
        self._require_compatible(other)
        return Quantity._mint(
            self._value + other._value,
            self.unit,
            self.frame,
            Provenance.join(self.provenance, other.provenance),
        )

    def __sub__(self, other: "Quantity[U]") -> "Quantity[U]":
        if not isinstance(other, Quantity):
            return NotImplemented
        self._require_compatible(other)
        return Quantity._mint(
            self._value - other._value,
            self.unit,
            self.frame,
            Provenance.join(self.provenance, other.provenance),
        )

    def __mul__(self, ratio: float) -> "Quantity[U]":
        if isinstance(ratio, Quantity):
            return NotImplemented
        return Quantity._mint(self._value * ratio, self.unit, self.frame, self.provenance)

    def __rmul__(self, ratio: float) -> "Quantity[U]":
        return self.__mul__(ratio)

    def __truediv__(self, ratio: float) -> "Quantity[U]":
        if isinstance(ratio, Quantity):
            return NotImplemented
        return Quantity._mint(self._value / ratio, self.unit, self.frame, self.provenance)

    def __neg__(self) -> "Quantity[U]":
        return Quantity._mint(-self._value, self.unit, self.frame, self.provenance)

    def __pos__(self) -> "Quantity[U]":
        return Quantity._mint(+self._value, self.unit, self.frame, self.provenance)

    def __abs__(self) -> "Quantity[U]":
        return Quantity._mint(abs(self._value), self.unit, self.frame, self.provenance)

    # ---- display (no bare-magnitude grab leaks here) ----
    def __repr__(self) -> str:
        return (
            f"Quantity({self._value!r}, unit={self.unit!r}, frame={self.frame!r}, "
            f"provenance={self.provenance.name})"
        )

    def __str__(self) -> str:
        return f"{self._value} [{self.provenance.name} {self.unit} {self.frame}]"

    def __format__(self, spec: str) -> str:
        return f"{format(self._value, spec)} [{self.provenance.name} {self.unit} {self.frame}]"


# --- Acquisition factories: the only public mints. Provenance is in the NAME,
# never an argument, so no public callable can pick a value's provenance. -------
def measured(magnitude: float, unit: type[U], frame: str) -> Quantity[U]:
    """Confer ``MEASURED`` — a value that entered as an authoritative reading/spec.

    Confined to the source layer (and the spec-policy authority); see the
    ``measured_confined_to_sources`` conformance trap.
    """
    return Quantity._mint(magnitude, unit.symbol, frame, Provenance.MEASURED)


def inferred(magnitude: float, unit: type[U], frame: str) -> Quantity[U]:
    """Confer ``INFERRED`` — a value derived/declared, not directly measured."""
    return Quantity._mint(magnitude, unit.symbol, frame, Provenance.INFERRED)


def extrapolated(magnitude: float, unit: type[U], frame: str) -> Quantity[U]:
    """Confer ``EXTRAPOLATED`` — the weakest stamp, a model-shaped ballpark."""
    return Quantity._mint(magnitude, unit.symbol, frame, Provenance.EXTRAPOLATED)


def _unpickle_quantity(
    value: float, unit: str, frame: str, provenance: Provenance
) -> "Quantity[Any]":
    """Reconstruct a Quantity from pickle/copy via the keyed mint (see __reduce__)."""
    return Quantity._mint(value, unit, frame, provenance)


# Back-compat: ``ProvFloat`` was the float-subclass value name. It is now an
# annotation alias for a unit-erased ``Quantity`` so existing annotations keep
# compiling under ``--strict`` (explicit ``Any``, not a missing type parameter).
# It is for annotations only — use the bare class ``Quantity`` for ``isinstance``.
ProvFloat: TypeAlias = Quantity[Any]


@dataclass(frozen=True, slots=True)
class Refusal:
    """A first-class refusal result instead of fabricated precision."""

    requested: str
    reason: str
    remedy: str
    provenance: Provenance | None = None

    def __bool__(self) -> bool:
        return False


Answer: TypeAlias = "Quantity[Any] | Refusal"


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


Result: TypeAlias = "Quantity[Any] | Refusal | VerdictResult"


# --- Phantom frame tags & the phantom-typed Angle ----------------------------
class FrameTag:
    """Base for phantom angle-frame markers; ``name`` is the runtime frame string."""

    name: ClassVar[str] = "?"


class Crank(FrameTag):
    name = "crank"


class Cam(FrameTag):
    name = "cam"


Fr = TypeVar("Fr", bound=FrameTag)


@dataclass(frozen=True)
class Angle(Generic[Fr]):
    """A phantom-typed crank/cam angle. Crank values are periodic over 720 deg.

    The phantom ``Fr`` makes ``lift_at(some_cam_angle)`` a ``mypy`` error; the
    runtime ``frame`` string and :meth:`require_crank` remain as defence-in-depth.
    """

    degrees: float
    frame: Literal["crank", "cam"]

    @staticmethod
    def crank(degrees: float) -> "Angle[Crank]":
        return Angle(degrees % 720.0, "crank")

    @staticmethod
    def cam(degrees: float) -> "Angle[Cam]":
        return Angle(degrees % 360.0, "cam")

    def require_crank(self) -> float:
        if self.frame != "crank":
            raise ValueError(f"expected crank angle, got {self.frame}")
        return self.degrees


__all__ = [
    "Angle",
    "Answer",
    "Cam",
    "Crank",
    "Frame",
    "FrameTag",
    "Inch",
    "InchDeg",
    "InchPerDeg",
    "InchPerDeg2",
    "InchPerDeg3",
    "Mm",
    "ProvFloat",
    "Provenance",
    "Quantity",
    "Refusal",
    "Result",
    "SafetyVerdict",
    "Unit",
    "UnitTag",
    "VerdictResult",
    "extrapolated",
    "inferred",
    "measured",
]
