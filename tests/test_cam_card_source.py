from __future__ import annotations

import pytest

from cam_analyzer.profile import CamProfile
from cam_analyzer.quantity import Angle, Inch, Provenance, Refusal, inferred
from cam_analyzer.sources.cam_card import (
    CHECKING_LIFT_IN,
    CamCard,
    CamLobeSpec,
    PolynomialMotionLawCamCardOperator,
    exhaust_profile_from_cam_card,
    intake_profile_from_cam_card,
    profiles_from_cam_card,
)


def test_wr250r_reference_uses_web_cam_81_651_values() -> None:
    card = CamCard.wr250r_reference()

    assert card.intake == CamLobeSpec(0.360, 262.0, 238.0, 109.5, 0.006)
    assert card.exhaust == CamLobeSpec(0.360, 270.0, 246.0, 104.5, 0.008)


def test_cam_lobe_spec_validation_traps_incoherent_cards() -> None:
    with pytest.raises(ValueError, match="advertised_duration < duration@0.050"):
        CamLobeSpec(0.360, 238.0, 262.0, 109.5, 0.006)

    with pytest.raises(ValueError, match="valve_lift_in must exceed"):
        CamLobeSpec(CHECKING_LIFT_IN, 262.0, 238.0, 109.5, 0.006)

    with pytest.raises(ValueError, match="lash_in must be non-negative"):
        CamLobeSpec(0.360, 262.0, 238.0, 109.5, -0.001)


def test_public_factories_return_intake_and_exhaust_cam_profiles() -> None:
    card = CamCard.wr250r_reference()
    profiles = profiles_from_cam_card(card)

    assert isinstance(profiles.intake, CamProfile)
    assert isinstance(profiles.exhaust, CamProfile)
    assert intake_profile_from_cam_card(card).max_lift() == profiles.intake.max_lift()
    assert exhaust_profile_from_cam_card(card).max_lift() == profiles.exhaust.max_lift()


def test_motion_law_operator_fits_hard_timing_constraints() -> None:
    card = CamCard.wr250r_reference()
    intake_operator = PolynomialMotionLawCamCardOperator(card.intake, "intake")
    exhaust_operator = PolynomialMotionLawCamCardOperator(card.exhaust, "exhaust")

    assert intake_operator.evaluate(109.5) == pytest.approx(0.360)
    assert exhaust_operator.evaluate(615.5) == pytest.approx(0.360)
    assert intake_operator.evaluate(710.5) == pytest.approx(0.050)
    assert intake_operator.evaluate(228.5) == pytest.approx(0.050)
    assert exhaust_operator.evaluate(492.5) == pytest.approx(0.050)
    assert exhaust_operator.evaluate(18.5) == pytest.approx(0.050)


def test_motion_law_operator_has_continuous_velocity_and_acceleration_at_knots() -> None:
    operator = PolynomialMotionLawCamCardOperator(CamCard.wr250r_reference().intake, "intake")
    knot_degrees = (
        operator.advertised_open_deg,
        operator.opening_050_deg,
        (operator.centerline_crank_deg - operator.dwell_half_width_deg) % 720.0,
        (operator.centerline_crank_deg + operator.dwell_half_width_deg) % 720.0,
        operator.closing_050_deg,
        operator.advertised_close_deg,
    )

    for crank_deg in knot_degrees:
        for order in (1, 2):
            left = operator.derivative(order, crank_deg - 1e-6)
            right = operator.derivative(order, crank_deg + 1e-6)
            assert left == pytest.approx(right, abs=2e-4)


def test_generated_profiles_report_reference_events_and_durations_at_050() -> None:
    profiles = profiles_from_cam_card(CamCard.wr250r_reference())
    checking_lift = inferred(0.050, Inch, "valve_side")

    assert [event.degrees for event in profiles.intake.events_at_lift(checking_lift)] == pytest.approx(
        [228.5, 710.5],
        abs=0.001,
    )
    assert [event.degrees for event in profiles.exhaust.events_at_lift(checking_lift)] == pytest.approx(
        [18.5, 492.5],
        abs=0.001,
    )
    assert profiles.intake.duration_at_lift(checking_lift).degrees == pytest.approx(238.0, abs=0.001)
    assert profiles.exhaust.duration_at_lift(checking_lift).degrees == pytest.approx(246.0, abs=0.001)


def test_cam_card_profiles_never_emit_measured_lift_provenance() -> None:
    profiles = profiles_from_cam_card(CamCard.wr250r_reference())

    for profile in (profiles.intake, profiles.exhaust):
        assert profile.max_lift().provenance != Provenance.MEASURED
        assert profile.area_under_curve().provenance != Provenance.MEASURED

    assert profiles.intake.lift_at(Angle.crank(705.0)).provenance == Provenance.EXTRAPOLATED
    assert profiles.intake.lift_at(Angle.crank(109.5)).provenance == Provenance.EXTRAPOLATED
    assert profiles.intake.lift_at(Angle.crank(60.0)).provenance == Provenance.INFERRED


def test_published_050_open_and_close_boundaries_stamp_inferred() -> None:
    # events_at_lift returns the exact published @0.050" opening/closing angles.
    # Those boundary events must read back as INFERRED cam-card evidence so a
    # downstream consumer probing lift_at(closing) does not see EXTRAPOLATED.
    profiles = profiles_from_cam_card(CamCard.wr250r_reference())

    intake_open = PolynomialMotionLawCamCardOperator(CamCard.wr250r_reference().intake, "intake").opening_050_deg
    intake_close = PolynomialMotionLawCamCardOperator(CamCard.wr250r_reference().intake, "intake").closing_050_deg
    assert profiles.intake.lift_at(Angle.crank(intake_open)).provenance == Provenance.INFERRED
    assert profiles.intake.lift_at(Angle.crank(intake_close)).provenance == Provenance.INFERRED

    exhaust_close = PolynomialMotionLawCamCardOperator(CamCard.wr250r_reference().exhaust, "exhaust").closing_050_deg
    assert profiles.exhaust.lift_at(Angle.crank(exhaust_close)).provenance == Provenance.INFERRED

    # The nose centerline stays extrapolated; the published boundary fix is local.
    assert profiles.intake.lift_at(Angle.crank(109.5)).provenance == Provenance.EXTRAPOLATED


def test_cam_card_derivatives_are_model_derived_and_never_measured() -> None:
    profile = profiles_from_cam_card(CamCard.wr250r_reference()).intake

    velocity = profile.velocity_at(Angle.crank(60.0))
    assert not isinstance(velocity, Refusal)
    assert velocity.provenance != Provenance.MEASURED

    nose_velocity = profile.velocity_at(Angle.crank(109.5))
    assert not isinstance(nose_velocity, Refusal)
    assert nose_velocity.provenance == Provenance.EXTRAPOLATED

    acceleration = profile.acceleration_at(Angle.crank(60.0))
    jerk = profile.jerk_at(Angle.crank(60.0))
    assert not isinstance(acceleration, Refusal)
    assert not isinstance(jerk, Refusal)
    assert acceleration.provenance == Provenance.EXTRAPOLATED
    assert jerk.provenance == Provenance.EXTRAPOLATED
