"""Opt-in approximate derivatives (cam-card backing).

Default: acceleration/jerk REFUSE off a cam card (a fitted sine-power can't justify
them). With approximate_derivatives=True the profile answers with an EXTRAPOLATED
ballpark instead — useful for a rough shape, never trustworthy enough to pass the
cliff-analysis fitness gates.
"""

from __future__ import annotations

import math

import pytest

from cam_analyzer.profile import AnalysisKind
from cam_analyzer.quantity import Angle, ProvFloat, Provenance, Refusal
from cam_analyzer.sources.cam_card import CamCard, profiles_from_cam_card

_CARD = CamCard.wr250r_reference()
_MIDFLANK = Angle.crank(120.0)  # offset ~10.5deg from the 109.5deg intake centerline


def test_default_profile_still_refuses_acceleration_and_jerk() -> None:
    intake = profiles_from_cam_card(_CARD).intake
    assert isinstance(intake.acceleration_at(_MIDFLANK), Refusal)
    assert isinstance(intake.jerk_at(_MIDFLANK), Refusal)


def test_approximate_profile_returns_extrapolated_acceleration_and_jerk() -> None:
    intake = profiles_from_cam_card(_CARD, approximate_derivatives=True).intake

    accel = intake.acceleration_at(_MIDFLANK)
    jerk = intake.jerk_at(_MIDFLANK)

    assert isinstance(accel, ProvFloat) and not isinstance(accel, Refusal)
    assert isinstance(jerk, ProvFloat) and not isinstance(jerk, Refusal)
    assert accel.provenance is Provenance.EXTRAPOLATED
    assert jerk.provenance is Provenance.EXTRAPOLATED
    assert accel.unit == "inch_per_deg2"
    assert jerk.unit == "inch_per_deg3"
    assert math.isfinite(float(accel))
    assert math.isfinite(float(jerk))


def test_supported_velocity_is_unchanged_by_the_flag() -> None:
    # Mid-flank velocity is genuinely supported (INFERRED) either way — the opt-in
    # only affects otherwise-refused orders, never the supported path.
    strict = profiles_from_cam_card(_CARD).intake.velocity_at(_MIDFLANK)
    approx = profiles_from_cam_card(_CARD, approximate_derivatives=True).intake.velocity_at(_MIDFLANK)
    assert isinstance(strict, ProvFloat) and strict.provenance is Provenance.INFERRED
    assert isinstance(approx, ProvFloat) and approx.provenance is Provenance.INFERRED
    assert float(strict) == float(approx)


def test_approximation_does_not_elevate_cliff_fitness_gates() -> None:
    intake = profiles_from_cam_card(_CARD, approximate_derivatives=True).intake
    # The whole point: a ballpark must NOT make spring-float / jerk verdicts trustable.
    assert intake.is_good_enough_for(AnalysisKind.JERK) is False
    assert intake.is_good_enough_for(AnalysisKind.SPRING_SAFETY) is False
    assert intake.is_good_enough_for(AnalysisKind.PTV) is False


def test_approximate_velocity_in_the_nose_is_extrapolated() -> None:
    # The nose is order-1 *unsupported* (strict refuses); the opt-in gives a ballpark.
    intake = profiles_from_cam_card(_CARD, approximate_derivatives=True).intake
    nose = intake.peak_angle()
    strict_nose = profiles_from_cam_card(_CARD).intake.velocity_at(nose)
    approx_nose = intake.velocity_at(nose)
    assert isinstance(strict_nose, Refusal)
    assert isinstance(approx_nose, ProvFloat) and approx_nose.provenance is Provenance.EXTRAPOLATED


@pytest.mark.parametrize("order_method", ["acceleration_at", "jerk_at"])
def test_extreme_flank_edge_still_refuses_even_when_approximating(order_method: str) -> None:
    # Where sin(phase) is tiny the analytic high-order derivatives blow up; the opt-in
    # refuses there rather than return a meaningless spike.
    intake = profiles_from_cam_card(_CARD, approximate_derivatives=True).intake
    # Far out on the flank, near the advertised opening (well outside duration@0.050").
    edge = Angle.crank(109.5 - 130.0)
    result = getattr(intake, order_method)(edge)
    assert isinstance(result, Refusal)
