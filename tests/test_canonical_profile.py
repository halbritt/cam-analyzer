from __future__ import annotations

import pytest

from cam_analyzer.profile import AnalysisKind
from cam_analyzer.profile.canonical import CanonicalCamProfile, CanonicalLiftModel
from cam_analyzer.profile.provenance_map import ProvenanceMap
from cam_analyzer.quantity import Angle, Inch, Provenance, Quantity, Refusal, inferred


class TinyTriangularOperator:
    name = "TinyTriangular"

    def __init__(self, max_derivative_order: int = 1) -> None:
        self._max_derivative_order = max_derivative_order
        self.derivative_calls: list[int] = []

    def evaluate(self, crank_deg: float) -> float:
        angle = crank_deg % 720.0
        if 100.0 <= angle <= 200.0:
            return (angle - 100.0) / 100.0
        if 200.0 < angle <= 300.0:
            return (300.0 - angle) / 100.0
        return 0.0

    def derivative(self, order: int, crank_deg: float) -> float:
        self.derivative_calls.append(order)
        if order != 1:
            raise AssertionError("unsupported derivative was evaluated")
        angle = crank_deg % 720.0
        if 100.0 <= angle < 200.0:
            return 0.01
        if 200.0 < angle <= 300.0:
            return -0.01
        return 0.0

    def max_supported_derivative(self, crank_deg: float) -> int:
        return self._max_derivative_order


def _profile(
    operator: TinyTriangularOperator,
    provenance: ProvenanceMap | None = None,
    samples: tuple[float, ...] | None = None,
) -> CanonicalCamProfile:
    return CanonicalCamProfile(
        CanonicalLiftModel(
            samples_720=samples or (0.0,) * 720,
            operator=operator,
            provenance=provenance
            or ProvenanceMap(
                [
                    (0.0, Provenance.EXTRAPOLATED),
                    (100.0, Provenance.MEASURED),
                    (300.0, Provenance.EXTRAPOLATED),
                ]
            ),
        )
    )


def test_lift_and_supported_derivative_are_stamped_from_operator_and_map() -> None:
    operator = TinyTriangularOperator(max_derivative_order=1)
    profile = _profile(operator)

    lift = profile.lift_at(Angle.crank(150.0))
    velocity = profile.velocity_at(Angle.crank(150.0))

    assert float(lift) == pytest.approx(0.5)
    assert lift.unit == "inch"
    assert lift.frame == "valve_side"
    assert lift.provenance is Provenance.MEASURED
    assert isinstance(velocity, Quantity)
    assert float(velocity) == pytest.approx(0.01)
    assert velocity.unit == "inch_per_deg"
    assert velocity.provenance is Provenance.INFERRED
    assert operator.derivative_calls == [1]


def test_unsupported_derivative_returns_refusal_without_evaluating_derivative() -> None:
    operator = TinyTriangularOperator(max_derivative_order=1)
    profile = _profile(operator)

    refusal = profile.acceleration_at(Angle.crank(150.0))

    assert isinstance(refusal, Refusal)
    assert refusal.requested == "derivative order 2 at 150.000 deg"
    assert "not order 2" in refusal.reason
    assert refusal.provenance is Provenance.EXTRAPOLATED
    assert operator.derivative_calls == []


def test_reduction_queries_scan_and_integrate_the_same_operator() -> None:
    profile = _profile(TinyTriangularOperator())
    lift = inferred(0.5, Inch, "valve_side")

    events = profile.events_at_lift(lift)
    duration = profile.duration_at_lift(lift)
    seat_duration = profile.duration_at_lift(inferred(0.0, Inch, "valve_side"))
    max_lift = profile.max_lift()
    area = profile.area_under_curve()

    assert [event.degrees for event in events] == pytest.approx([150.0, 250.0])
    assert duration.degrees == pytest.approx(100.0)
    assert seat_duration.degrees == pytest.approx(200.0)
    assert float(max_lift) == pytest.approx(1.0)
    assert max_lift.provenance is Provenance.MEASURED
    assert float(area) == pytest.approx(100.0)
    assert area.unit == "inch_deg"
    assert area.provenance is Provenance.EXTRAPOLATED


def test_fitness_checks_are_conservative_about_safety_and_high_derivatives() -> None:
    profile = _profile(
        TinyTriangularOperator(max_derivative_order=1),
        provenance=ProvenanceMap.constant(Provenance.INFERRED),
    )

    assert profile.is_good_enough_for(AnalysisKind.TIMING)
    assert profile.is_good_enough_for(AnalysisKind.OVERLAP)
    assert not profile.is_good_enough_for(AnalysisKind.JERK)
    assert not profile.is_good_enough_for(AnalysisKind.PTV)
    assert not profile.is_good_enough_for(AnalysisKind.SPRING_SAFETY)


def test_sparse_measured_samples_do_not_pass_as_continuous_measured_curve() -> None:
    profile = _profile(
        TinyTriangularOperator(),
        provenance=ProvenanceMap.constant(Provenance.MEASURED),
        samples=(0.0, 0.050, 0.200, 0.360, 0.200, 0.050, 0.0, 0.0),
    )

    with pytest.raises(ValueError, match="measured sparse samples"):
        profile.lift_at(Angle.crank(45.0))
