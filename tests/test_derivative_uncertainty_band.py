"""Opt-in derivative uncertainty band (follow-up to #11).

The band brackets an approximate (EXTRAPOLATED) derivative across the cam card's
numeric tolerance (D013-style earliest/latest fits). It quantifies card-tolerance
sensitivity only — never the flank-shape model error — so it must never license a
value for the cliff gates.
"""

from __future__ import annotations

import math

import pytest

from cam_analyzer.profile import AnalysisKind
from cam_analyzer.profile.canonical import DerivativeBand
from cam_analyzer.quantity import Angle, Provenance, Refusal
from cam_analyzer.sources.cam_card import (
    CamCard,
    SinePowerCamCardOperator,
    profiles_from_cam_card,
)

_CARD = CamCard.wr250r_reference()
_MIDFLANK = Angle.crank(120.0)


def _approx_intake():
    return profiles_from_cam_card(_CARD, approximate_derivatives=True).intake


@pytest.mark.parametrize(
    ("band_method", "value_method", "unit"),
    [
        ("velocity_band_at", "velocity_at", "inch_per_deg"),
        ("acceleration_band_at", "acceleration_at", "inch_per_deg2"),
        ("jerk_band_at", "jerk_at", "inch_per_deg3"),
    ],
)
def test_band_brackets_the_extrapolated_value(band_method: str, value_method: str, unit: str) -> None:
    intake = _approx_intake()

    band = getattr(intake, band_method)(_MIDFLANK)
    assert isinstance(band, DerivativeBand)

    low, value, high = float(band.low), float(band.value), float(band.high)
    assert low <= value <= high
    assert math.isfinite(low) and math.isfinite(high)
    # Mid-flank is sensitive to the fit, so the band has real width (not degenerate).
    assert low < high
    # Everything is EXTRAPOLATED and correctly stamped.
    for part in (band.value, band.low, band.high):
        assert part.provenance is Provenance.EXTRAPOLATED
        assert part.unit == unit
        assert part.frame == "valve_side"
    # The central value is exactly the ordinary approximate-derivative answer.
    central = getattr(intake, value_method)(_MIDFLANK)
    assert not isinstance(central, Refusal)
    assert float(central) == float(band.value)


def test_band_refuses_in_strict_mode() -> None:
    strict = profiles_from_cam_card(_CARD).intake  # approximate_derivatives off
    result = strict.acceleration_band_at(_MIDFLANK)
    assert isinstance(result, Refusal)
    assert "approximate_derivatives is off" in result.reason


def test_band_refuses_at_the_extreme_flank_edge_even_when_approximating() -> None:
    # Where the analytic high-order derivatives blow up, the value refuses — so must
    # the band, rather than fabricate a spread around a meaningless spike.
    intake = _approx_intake()
    edge = Angle.crank(109.5 - 130.0)
    assert isinstance(intake.acceleration_band_at(edge), Refusal)
    assert isinstance(intake.jerk_band_at(edge), Refusal)


def test_band_is_available_in_the_nose_where_strict_velocity_refuses() -> None:
    intake = _approx_intake()
    nose = intake.peak_angle()
    band = intake.velocity_band_at(nose)
    assert isinstance(band, DerivativeBand)
    assert band.value.provenance is Provenance.EXTRAPOLATED


def test_band_does_not_elevate_cliff_fitness_gates() -> None:
    # The whole point: an uncertainty band, however tight, must not make any
    # cliff verdict trustable.
    intake = _approx_intake()
    # Touch the bands first to be sure querying them has no side effect on fitness.
    intake.acceleration_band_at(_MIDFLANK)
    intake.jerk_band_at(_MIDFLANK)
    assert intake.is_good_enough_for(AnalysisKind.JERK) is False
    assert intake.is_good_enough_for(AnalysisKind.SPRING_SAFETY) is False
    assert intake.is_good_enough_for(AnalysisKind.PTV) is False


def test_operator_band_rejects_unsupported_orders() -> None:
    operator = SinePowerCamCardOperator(_CARD.intake, "intake")
    with pytest.raises(ValueError, match="orders 1-3"):
        operator.approximate_derivative_band(4, 120.0)


def test_operator_band_brackets_the_central_fit() -> None:
    operator = SinePowerCamCardOperator(_CARD.intake, "intake")
    low, high = operator.approximate_derivative_band(2, 120.0)
    central = operator.approximate_derivative(2, 120.0)
    assert low <= central <= high
