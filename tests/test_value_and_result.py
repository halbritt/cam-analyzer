"""Focused tests for D012 stamped values and result primitives."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from cam_analyzer.quantity import ProvFloat, Provenance, Quantity
from cam_analyzer.result import Refusal, SafetyVerdict, VerdictResult


def _assert_inferred_lift(stamped_lift: ProvFloat) -> None:
    assert stamped_lift.unit == "inch"
    assert stamped_lift.frame == "valve_side"
    assert stamped_lift.provenance == Provenance.INFERRED


@pytest.mark.parametrize(
    ("expression", "expected_magnitude"),
    [
        (lambda stamped_lift: stamped_lift + 2.0, 3.5),
        (lambda stamped_lift: 2.0 + stamped_lift, 3.5),
        (lambda stamped_lift: stamped_lift - 0.5, 1.0),
        (lambda stamped_lift: 2.0 - stamped_lift, 0.5),
        (lambda stamped_lift: stamped_lift * 2.0, 3.0),
        (lambda stamped_lift: 2.0 * stamped_lift, 3.0),
        (lambda stamped_lift: stamped_lift / 2.0, 0.75),
        (lambda stamped_lift: 3.0 / stamped_lift, 2.0),
    ],
)
def test_plain_number_arithmetic_preserves_stamped_operand_metadata(
    expression: Callable[[ProvFloat], ProvFloat],
    expected_magnitude: float,
) -> None:
    stamped_lift = ProvFloat.inch(1.5, Provenance.INFERRED)

    arithmetic_result = expression(stamped_lift)

    assert float(arithmetic_result) == pytest.approx(expected_magnitude)
    _assert_inferred_lift(arithmetic_result)


def test_compatible_stamped_arithmetic_joins_weakest_provenance() -> None:
    measured_lift = ProvFloat.inch(0.360, Provenance.MEASURED)
    extrapolated_lift = ProvFloat.inch(0.010, Provenance.EXTRAPOLATED)

    combined_lift = measured_lift + extrapolated_lift

    assert float(combined_lift) == pytest.approx(0.370)
    assert combined_lift.unit == "inch"
    assert combined_lift.frame == "valve_side"
    assert combined_lift.provenance == Provenance.EXTRAPOLATED


@pytest.mark.parametrize(
    "other_lift",
    [
        ProvFloat(1.0, "mm", "valve_side", Provenance.INFERRED),
        ProvFloat(1.0, "inch", "cam_side", Provenance.INFERRED),
    ],
)
def test_mismatched_stamped_arithmetic_requires_explicit_conversion(
    other_lift: ProvFloat,
) -> None:
    measured_lift = ProvFloat.inch(0.360, Provenance.MEASURED)

    with pytest.raises(ValueError, match="incompatible stamped values"):
        _ = measured_lift + other_lift


def test_display_forms_include_unit_frame_and_provenance_stamp() -> None:
    stamped_lift = ProvFloat.inch(0.360, Provenance.INFERRED)

    assert "INFERRED" in str(stamped_lift)
    assert "inch" in str(stamped_lift)
    assert "valve_side" in str(stamped_lift)
    assert "INFERRED" in repr(stamped_lift)
    assert format(stamped_lift, ".3f") == "0.360 [INFERRED inch valve_side]"


def test_stamped_values_are_immutable_and_stamp_aware() -> None:
    inferred_lift = ProvFloat.inch(0.360, Provenance.INFERRED)
    measured_lift = ProvFloat.inch(0.360, Provenance.MEASURED)

    assert inferred_lift != measured_lift
    assert inferred_lift != 0.360
    assert 0.360 != inferred_lift
    assert hash(inferred_lift) != hash(measured_lift)
    with pytest.raises(AttributeError, match="immutable"):
        inferred_lift.provenance = Provenance.MEASURED


def test_quantity_alias_constructs_provfloat_without_magnitude_escape() -> None:
    stamped_lift = Quantity(0.050, "inch", "valve_side", Provenance.INFERRED)

    assert isinstance(stamped_lift, ProvFloat)
    assert float(stamped_lift) == pytest.approx(0.050)
    assert not hasattr(stamped_lift, "magnitude")


def test_refusal_carries_requested_reason_remedy_and_optional_provenance() -> None:
    refusal = Refusal(
        requested="jerk_at(109.5 deg)",
        reason="cam-card samples do not support third derivative",
        remedy="measure valve lift at smaller crank-angle intervals",
        provenance=Provenance.EXTRAPOLATED,
    )

    assert not refusal
    assert refusal.requested == "jerk_at(109.5 deg)"
    assert refusal.reason == "cam-card samples do not support third derivative"
    assert refusal.remedy == "measure valve lift at smaller crank-angle intervals"
    assert refusal.provenance == Provenance.EXTRAPOLATED


def test_verdict_result_represents_cam_card_undecidable_without_number() -> None:
    verdict_result = VerdictResult(
        requested="piston_to_valve",
        verdict=SafetyVerdict.UNDECIDABLE_FROM_CAM_CARD,
        reason="earliest and latest plausible cam-card curves disagree",
        remedy="measure valve lift near the clearance threshold",
        provenance=Provenance.INFERRED,
    )

    assert verdict_result.verdict is SafetyVerdict.UNDECIDABLE_FROM_CAM_CARD
    assert verdict_result.requested == "piston_to_valve"
    assert verdict_result.provenance == Provenance.INFERRED
