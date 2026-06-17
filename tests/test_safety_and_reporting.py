from __future__ import annotations

import pytest

from cam_analyzer.analysis.dynamic_compression import DynamicCompressionInput, EngineGeometry
from cam_analyzer.analysis.piston_to_valve import (
    PistonToValveInput,
    PistonToValveVerdict,
    default_exhaust_policy,
    default_intake_policy,
    evaluate_piston_to_valve,
)
from cam_analyzer.analysis.reporting import render_markdown_report
from cam_analyzer.analysis.spring_safety import (
    SpringSafetyInput,
    SpringSafetyVerdict,
    default_spring_policy,
    evaluate_spring_safety,
)
from cam_analyzer.profile import AnalysisKind
from cam_analyzer.profile.canonical import CanonicalCamProfile, CanonicalLiftModel
from cam_analyzer.profile.provenance_map import ProvenanceMap
from cam_analyzer.quantity import Angle, Provenance, Quantity, Refusal
from cam_analyzer.sources.cam_card import CamCard, profiles_from_cam_card


class ReportProfile:
    def __init__(self, *, centerline_deg: float, good_for_safety: bool = False) -> None:
        self._centerline_deg = centerline_deg
        self._good_for_safety = good_for_safety

    def lift_at(self, angle: Angle) -> Quantity:
        return Quantity(0.050, "inch", "valve_side", Provenance.INFERRED)

    def velocity_at(self, angle: Angle) -> Quantity:
        return Quantity(0.0, "inch_per_deg", "valve_side", Provenance.EXTRAPOLATED)

    def acceleration_at(self, angle: Angle) -> Quantity:
        return Quantity(0.0, "inch_per_deg2", "valve_side", Provenance.EXTRAPOLATED)

    def jerk_at(self, angle: Angle) -> Quantity:
        return Quantity(0.0, "inch_per_deg3", "valve_side", Provenance.EXTRAPOLATED)

    def events_at_lift(self, lift: Quantity) -> list[Angle]:
        if float(lift) >= 0.360:
            return [Angle.crank(self._centerline_deg)]
        if self._centerline_deg < 360.0:
            return [Angle.crank(710.5), Angle.crank(228.5)]
        return [Angle.crank(492.5), Angle.crank(18.5)]

    def duration_at_lift(self, lift: Quantity) -> Angle:
        return Angle.crank(238.0 if self._centerline_deg < 360.0 else 246.0)

    def max_lift(self) -> Quantity:
        return Quantity(0.360, "inch", "valve_side", Provenance.INFERRED)

    def area_under_curve(self) -> Quantity:
        return Quantity(42.0, "inch_deg", "valve_side", Provenance.INFERRED)

    def is_good_enough_for(self, kind: AnalysisKind) -> bool:
        if kind in {AnalysisKind.PTV, AnalysisKind.SPRING_SAFETY}:
            return self._good_for_safety
        return True


class _MeasuredFlankOperator:
    """A measured-quality operator whose derivative support is configurable."""

    name = "MeasuredFlankTestOperator"

    def __init__(self, max_derivative_order: int) -> None:
        self._max_derivative_order = max_derivative_order

    def evaluate(self, crank_deg: float) -> float:
        return 0.0

    def derivative(self, order: int, crank_deg: float) -> float:
        return 0.0

    def max_supported_derivative(self, crank_deg: float) -> int:
        return self._max_derivative_order


def _measured_profile(max_derivative_order: int = 2) -> CanonicalCamProfile:
    return CanonicalCamProfile(
        CanonicalLiftModel(
            samples_720=(0.0,) * 720,
            operator=_MeasuredFlankOperator(max_derivative_order),
            provenance=ProvenanceMap.constant(Provenance.MEASURED),
        )
    )


def test_measured_profile_is_good_enough_for_ptv_and_spring_safety() -> None:
    profile = _measured_profile(max_derivative_order=2)

    assert profile.is_good_enough_for(AnalysisKind.PTV)
    assert profile.is_good_enough_for(AnalysisKind.SPRING_SAFETY)


def test_measured_profile_without_acceleration_support_blocks_spring_only() -> None:
    profile = _measured_profile(max_derivative_order=1)

    assert profile.is_good_enough_for(AnalysisKind.PTV)
    assert not profile.is_good_enough_for(AnalysisKind.SPRING_SAFETY)


def test_measured_profile_yields_ptv_pass_or_fail_with_measured_clearance() -> None:
    profile = _measured_profile(max_derivative_order=2)

    safe = evaluate_piston_to_valve(
        profile,
        PistonToValveInput(
            valve="intake",
            threshold_policy=default_intake_policy(),
            measured_clearance=Quantity(0.060, "inch", "valve_side", Provenance.MEASURED),
        ),
    )
    unsafe = evaluate_piston_to_valve(
        profile,
        PistonToValveInput(
            valve="intake",
            threshold_policy=default_intake_policy(),
            measured_clearance=Quantity(0.040, "inch", "valve_side", Provenance.MEASURED),
        ),
    )

    assert safe.verdict is PistonToValveVerdict.PASS
    assert unsafe.verdict is PistonToValveVerdict.FAIL
    assert safe.margin is not None and safe.margin.provenance == Provenance.MEASURED


def test_measured_profile_yields_spring_pass_or_fail_with_measured_clearance() -> None:
    profile = _measured_profile(max_derivative_order=2)

    safe = evaluate_spring_safety(
        profile,
        SpringSafetyInput(
            threshold_policy=default_spring_policy(),
            retainer_to_guide_clearance=Quantity(0.040, "inch", "valve_side", Provenance.MEASURED),
            coil_clearance=Quantity(0.020, "inch", "valve_side", Provenance.MEASURED),
        ),
    )
    unsafe = evaluate_spring_safety(
        profile,
        SpringSafetyInput(
            threshold_policy=default_spring_policy(),
            retainer_to_guide_clearance=Quantity(0.010, "inch", "valve_side", Provenance.MEASURED),
            coil_clearance=Quantity(0.005, "inch", "valve_side", Provenance.MEASURED),
        ),
    )

    assert safe.verdict is SpringSafetyVerdict.PASS
    assert unsafe.verdict is SpringSafetyVerdict.FAIL


def test_cam_card_profile_stays_undecidable_even_with_measured_clearance() -> None:
    # Supplying a measured clearance must not let a cam-card approximation
    # fabricate a PASS/FAIL: the profile gate (extrapolated low-lift evidence)
    # keeps the verdict UNDECIDABLE regardless of the clearance number.
    intake = profiles_from_cam_card(CamCard.wr250r_reference()).intake

    assert not intake.is_good_enough_for(AnalysisKind.PTV)
    assert not intake.is_good_enough_for(AnalysisKind.SPRING_SAFETY)

    ptv = evaluate_piston_to_valve(
        intake,
        PistonToValveInput(
            valve="intake",
            threshold_policy=default_intake_policy(),
            measured_clearance=Quantity(0.090, "inch", "valve_side", Provenance.MEASURED),
        ),
    )
    spring = evaluate_spring_safety(
        intake,
        SpringSafetyInput(
            threshold_policy=default_spring_policy(),
            retainer_to_guide_clearance=Quantity(0.040, "inch", "valve_side", Provenance.MEASURED),
            coil_clearance=Quantity(0.020, "inch", "valve_side", Provenance.MEASURED),
        ),
    )

    assert ptv.verdict is PistonToValveVerdict.UNDECIDABLE_FROM_CAM_CARD
    assert spring.verdict is SpringSafetyVerdict.UNDECIDABLE_FROM_CAM_CARD


def test_piston_to_valve_returns_undecidable_without_clearance_evidence() -> None:
    profile = ReportProfile(centerline_deg=109.5)
    result = evaluate_piston_to_valve(
        profile,
        PistonToValveInput(valve="intake", threshold_policy=default_intake_policy()),
    )

    assert result.verdict is PistonToValveVerdict.UNDECIDABLE_FROM_CAM_CARD
    assert result.margin is None
    assert "cam card" in result.explanation.lower()


def test_piston_to_valve_compares_measured_clearance_when_available() -> None:
    profile = ReportProfile(centerline_deg=109.5, good_for_safety=True)
    result = evaluate_piston_to_valve(
        profile,
        PistonToValveInput(
            valve="exhaust",
            threshold_policy=default_exhaust_policy(),
            measured_clearance=Quantity(0.090, "inch", "valve_side", Provenance.MEASURED),
        ),
    )

    assert result.verdict is PistonToValveVerdict.PASS
    assert result.margin is not None
    assert float(result.margin) == pytest.approx(0.010)
    assert result.margin.provenance == Provenance.MEASURED


def test_piston_to_valve_refuses_incompatible_clearance_units() -> None:
    profile = ReportProfile(centerline_deg=109.5, good_for_safety=True)
    result = evaluate_piston_to_valve(
        profile,
        PistonToValveInput(
            valve="intake",
            threshold_policy=default_intake_policy(),
            measured_clearance=Quantity(2.0, "mm", "valve_side", Provenance.MEASURED),
        ),
    )

    assert isinstance(result, Refusal)
    assert result.requested == "intake piston-to-valve verdict"
    assert "same unit/frame" in result.reason


def test_spring_safety_returns_undecidable_without_physical_spring_evidence() -> None:
    result = evaluate_spring_safety(
        ReportProfile(centerline_deg=109.5),
        SpringSafetyInput(threshold_policy=default_spring_policy()),
    )

    assert result.verdict is SpringSafetyVerdict.UNDECIDABLE_FROM_CAM_CARD
    assert "spring" in result.explanation.lower()


def test_spring_safety_compares_measured_margins_when_available() -> None:
    result = evaluate_spring_safety(
        ReportProfile(centerline_deg=109.5, good_for_safety=True),
        SpringSafetyInput(
            threshold_policy=default_spring_policy(),
            retainer_to_guide_clearance=Quantity(0.040, "inch", "valve_side", Provenance.MEASURED),
            coil_clearance=Quantity(0.020, "inch", "valve_side", Provenance.MEASURED),
        ),
    )

    assert result.verdict is SpringSafetyVerdict.PASS
    assert result.retainer_to_guide_margin is not None
    assert result.coil_margin is not None
    assert float(result.retainer_to_guide_margin) == pytest.approx(0.010)
    assert float(result.coil_margin) == pytest.approx(0.005)
    assert result.retainer_to_guide_margin.provenance == Provenance.MEASURED
    assert result.coil_margin.provenance == Provenance.MEASURED


def test_spring_safety_refuses_incompatible_clearance_units() -> None:
    result = evaluate_spring_safety(
        ReportProfile(centerline_deg=109.5, good_for_safety=True),
        SpringSafetyInput(
            threshold_policy=default_spring_policy(),
            retainer_to_guide_clearance=Quantity(1.0, "mm", "valve_side", Provenance.MEASURED),
            coil_clearance=Quantity(0.020, "inch", "valve_side", Provenance.MEASURED),
        ),
    )

    assert isinstance(result, Refusal)
    assert result.requested == "spring safety verdict"
    assert "same unit/frame" in result.reason


def test_report_lists_stamped_values_refusals_and_undecidable_verdicts() -> None:
    intake = ReportProfile(centerline_deg=109.5)
    exhaust = ReportProfile(centerline_deg=615.5)
    lift = Quantity(0.050, "inch", "valve_side", Provenance.INFERRED)
    dcr_input = DynamicCompressionInput(
        static_compression_ratio=12.8,
        geometry=EngineGeometry.from_mm(bore=77.0, stroke=53.6, rod_length=96.9),
        closing_lift=Quantity(0.050, "inch", "valve_side", Provenance.INFERRED),
    )

    report = render_markdown_report(
        intake,
        exhaust,
        timing_lifts=(lift,),
        dynamic_compression_input=dcr_input,
        ptv_inputs=(PistonToValveInput("intake", default_intake_policy()),),
        spring_input=SpringSafetyInput(default_spring_policy()),
    )

    assert "0.360 inch [valve_side, INFERRED]" in report
    assert "Lobe separation angle: 107.000 deg [crank]" in report
    assert "Dynamic compression ratio:" in report
    assert "UNDECIDABLE FROM CAM CARD" in report
    assert "cam card" in report.lower()
    assert not isinstance(report, Refusal)
