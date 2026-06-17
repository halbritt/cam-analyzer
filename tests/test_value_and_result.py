"""Focused tests for RFC 0001 sealed stamped values and result primitives."""

from __future__ import annotations

from collections.abc import Callable

import pytest

from cam_analyzer.quantity import (
    Inch,
    Mm,
    Provenance,
    Quantity,
    Refusal,
    SafetyVerdict,
    VerdictResult,
    extrapolated,
    inferred,
    measured,
)


def _assert_inferred_lift(stamped_lift: Quantity[Inch]) -> None:
    assert stamped_lift.unit == "inch"
    assert stamped_lift.frame == "valve_side"
    assert stamped_lift.provenance == Provenance.INFERRED


@pytest.mark.parametrize(
    ("expression", "expected_magnitude"),
    [
        (lambda stamped_lift: stamped_lift * 2.0, 3.0),
        (lambda stamped_lift: 2.0 * stamped_lift, 3.0),
        (lambda stamped_lift: stamped_lift / 2.0, 0.75),
    ],
)
def test_scaling_by_a_ratio_preserves_stamped_metadata(
    expression: Callable[[Quantity[Inch]], Quantity[Inch]],
    expected_magnitude: float,
) -> None:
    # Scaling a dimensioned value by a dimensionless ratio is meaningful and keeps
    # the unit/frame/provenance stamp.
    stamped_lift = inferred(1.5, Inch, "valve_side")

    arithmetic_result = expression(stamped_lift)

    assert float(arithmetic_result) == pytest.approx(expected_magnitude)
    _assert_inferred_lift(arithmetic_result)


@pytest.mark.parametrize(
    "expression",
    [
        lambda stamped_lift: stamped_lift + 2.0,
        lambda stamped_lift: 2.0 + stamped_lift,
        lambda stamped_lift: stamped_lift - 0.5,
        lambda stamped_lift: 3.0 / stamped_lift,
    ],
)
def test_adding_a_bare_number_to_a_dimensioned_value_is_rejected(
    expression: Callable[[Quantity[Inch]], object],
) -> None:
    # Adding/subtracting a bare scalar to a dimensioned quantity (or inverting it)
    # is dimensional nonsense — it was only ever possible because the old value was
    # a float subclass. The sealed value object refuses it at runtime (and it is a
    # mypy error too). The one explicit exit to a raw float stays ``float(x)``.
    stamped_lift = inferred(1.5, Inch, "valve_side")

    with pytest.raises(TypeError):
        expression(stamped_lift)


def test_compatible_stamped_arithmetic_joins_weakest_provenance() -> None:
    measured_lift = measured(0.360, Inch, "valve_side")
    extrapolated_lift = extrapolated(0.010, Inch, "valve_side")

    combined_lift = measured_lift + extrapolated_lift

    assert float(combined_lift) == pytest.approx(0.370)
    assert combined_lift.unit == "inch"
    assert combined_lift.frame == "valve_side"
    assert combined_lift.provenance == Provenance.EXTRAPOLATED


@pytest.mark.parametrize(
    "other_lift",
    [
        inferred(1.0, Mm, "valve_side"),
        inferred(1.0, Inch, "cam_side"),
    ],
)
def test_mismatched_stamped_arithmetic_requires_explicit_conversion(
    other_lift: Quantity[Inch],
) -> None:
    measured_lift = measured(0.360, Inch, "valve_side")

    with pytest.raises(ValueError, match="incompatible stamped values"):
        _ = measured_lift + other_lift


def test_display_forms_include_unit_frame_and_provenance_stamp() -> None:
    stamped_lift = inferred(0.360, Inch, "valve_side")

    assert "INFERRED" in str(stamped_lift)
    assert "inch" in str(stamped_lift)
    assert "valve_side" in str(stamped_lift)
    assert "INFERRED" in repr(stamped_lift)
    assert format(stamped_lift, ".3f") == "0.360 [INFERRED inch valve_side]"


def test_stamped_values_are_immutable_and_stamp_aware() -> None:
    inferred_lift = inferred(0.360, Inch, "valve_side")
    measured_lift = measured(0.360, Inch, "valve_side")

    assert inferred_lift != measured_lift
    assert inferred_lift != 0.360
    assert 0.360 != inferred_lift
    assert hash(inferred_lift) != hash(measured_lift)
    with pytest.raises(AttributeError, match="cannot assign"):
        inferred_lift.provenance = Provenance.MEASURED  # type: ignore[misc]


def test_factory_built_value_has_no_magnitude_escape() -> None:
    stamped_lift = inferred(0.050, Inch, "valve_side")

    assert isinstance(stamped_lift, Quantity)
    assert float(stamped_lift) == pytest.approx(0.050)
    # The honest exit is float(x); there is deliberately no .magnitude to strip.
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
