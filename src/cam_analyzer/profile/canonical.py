"""Single canonical representation (Pillar B / D005).

A profile is a ``@final`` facade over exactly one immutable ``CanonicalLiftModel``
= normalized 720° samples + one *named* ``LiftOperator``. Every C5 query delegates
to that one operator: derivatives differentiate it, reductions sample/solve it.
Implementers supply the canonical object — never a method body — so a profile
whose ``velocity_at`` disagrees with the slope of ``lift_at`` is unconstructable.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, final

from cam_analyzer.profile import AnalysisKind, CamProfile
from cam_analyzer.profile.provenance_map import ProvenanceMap
from cam_analyzer.quantity import Angle, Quantity


class LiftOperator(Protocol):
    """A named, sealed lift model. The single source of every query.

    Concrete operators: HalfSineApproximation, CubicPeriodicSpline,
    MeasuredPeriodicSeries. A new data source supplies one of these — nothing more.
    """

    name: str

    def evaluate(self, crank_deg: float) -> float: ...
    def derivative(self, order: int, crank_deg: float) -> float: ...


@dataclass(frozen=True, slots=True)
class CanonicalLiftModel:
    """The one immutable object backing a profile."""

    samples_720: tuple[float, ...]  # normalized lift per crank degree
    operator: LiftOperator
    provenance: ProvenanceMap


@final
class CanonicalCamProfile(CamProfile):
    """The generic facade. All eight queries are generated from ``model.operator``.

    This is where the C5 surface is *implemented once* and reused by every source,
    rather than re-implemented (and free to disagree) per source.
    """

    def __init__(self, model: CanonicalLiftModel):
        self._model = model

    def lift_at(self, angle: Angle) -> Quantity:
        raise NotImplementedError(
            "generate from model.operator.evaluate; stamp Quantity provenance "
            "from model.provenance.at(angle) — Pillar B + C"
        )

    def velocity_at(self, angle: Angle) -> Quantity:
        raise NotImplementedError("model.operator.derivative(1, …); provenance via derivative_map(1)")

    def acceleration_at(self, angle: Angle) -> Quantity:
        raise NotImplementedError("model.operator.derivative(2, …); provenance via derivative_map(2)")

    def jerk_at(self, angle: Angle) -> Quantity:
        raise NotImplementedError("model.operator.derivative(3, …); provenance via derivative_map(3)")

    def events_at_lift(self, lift: Quantity) -> list[Angle]:
        raise NotImplementedError("solve operator == lift over [0,720)")

    def duration_at_lift(self, lift: Quantity) -> Angle:
        raise NotImplementedError("reduce events_at_lift to a duration")

    def max_lift(self) -> Quantity:
        raise NotImplementedError("reduce the operator")

    def area_under_curve(self) -> Quantity:
        raise NotImplementedError("integrate the operator")

    def is_good_enough_for(self, kind: AnalysisKind) -> bool:
        raise NotImplementedError("compare required-confidence mask vs model.provenance — D006")
