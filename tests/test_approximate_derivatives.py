"""Cam-card motion-law derivative behavior.

The cam-card operator now exposes model-derived velocity/acceleration/jerk for
visualization and quality checks. They are always provenance-capped and never make
the sparse card good enough for cliff analyses.
"""

from __future__ import annotations

import pytest

from cam_analyzer.profile import AnalysisKind
from cam_analyzer.quantity import Angle, Quantity, Provenance, Refusal
from cam_analyzer.sources.cam_card import CamCard, profiles_from_cam_card

_CARD = CamCard.wr250r_reference()
_MIDFLANK = Angle.crank(120.0)  # offset ~10.5deg from the 109.5deg intake centerline


def test_default_profile_returns_extrapolated_acceleration_and_jerk() -> None:
    intake = profiles_from_cam_card(_CARD).intake

    accel = intake.acceleration_at(_MIDFLANK)
    jerk = intake.jerk_at(_MIDFLANK)

    assert isinstance(accel, Quantity) and not isinstance(accel, Refusal)
    assert isinstance(jerk, Quantity) and not isinstance(jerk, Refusal)
    assert accel.provenance is Provenance.EXTRAPOLATED
    assert jerk.provenance is Provenance.EXTRAPOLATED
    assert accel.unit == "inch_per_deg2"
    assert jerk.unit == "inch_per_deg3"
    assert abs(float(accel)) < 0.001
    assert abs(float(jerk)) < 0.001


def test_supported_velocity_is_unchanged_by_the_flag() -> None:
    # Mid-flank velocity is genuinely supported (INFERRED) either way — the opt-in
    # only affects otherwise-refused orders, never the supported path.
    strict = profiles_from_cam_card(_CARD).intake.velocity_at(_MIDFLANK)
    approx = profiles_from_cam_card(_CARD, approximate_derivatives=True).intake.velocity_at(_MIDFLANK)
    assert isinstance(strict, Quantity) and strict.provenance is Provenance.INFERRED
    assert isinstance(approx, Quantity) and approx.provenance is Provenance.INFERRED
    assert float(strict) == float(approx)


def test_approximation_does_not_elevate_cliff_fitness_gates() -> None:
    intake = profiles_from_cam_card(_CARD, approximate_derivatives=True).intake
    # The whole point: a ballpark must NOT make spring-float / jerk verdicts trustable.
    assert intake.is_good_enough_for(AnalysisKind.JERK) is False
    assert intake.is_good_enough_for(AnalysisKind.SPRING_SAFETY) is False
    assert intake.is_good_enough_for(AnalysisKind.PTV) is False


def test_velocity_in_the_nose_is_extrapolated() -> None:
    intake = profiles_from_cam_card(_CARD, approximate_derivatives=True).intake
    nose = intake.peak_angle()
    strict_nose = profiles_from_cam_card(_CARD).intake.velocity_at(nose)
    approx_nose = intake.velocity_at(nose)
    assert isinstance(strict_nose, Quantity) and strict_nose.provenance is Provenance.EXTRAPOLATED
    assert isinstance(approx_nose, Quantity) and approx_nose.provenance is Provenance.EXTRAPOLATED


@pytest.mark.parametrize("order_method", ["acceleration_at", "jerk_at"])
def test_extreme_flank_edge_returns_finite_model_derivatives(order_method: str) -> None:
    intake = profiles_from_cam_card(_CARD, approximate_derivatives=True).intake
    edge = Angle.crank(109.5 - 130.0)
    result = getattr(intake, order_method)(edge)
    assert isinstance(result, Quantity)
    assert result.provenance is Provenance.EXTRAPOLATED
    assert abs(float(result)) < 0.001
