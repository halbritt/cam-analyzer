from __future__ import annotations

from cam_analyzer.analysis.dynamic_compression import (
    DynamicCompressionInput,
    EngineGeometry,
    analyze_dynamic_compression,
    dynamic_compression_ratio,
)
from cam_analyzer.profile import AnalysisKind
from cam_analyzer.quantity import (
    Angle,
    Inch,
    InchDeg,
    InchPerDeg,
    InchPerDeg2,
    InchPerDeg3,
    Provenance,
    Quantity,
    Refusal,
    extrapolated,
    inferred,
)
from cam_analyzer.sources.cam_card import CamCard, profiles_from_cam_card


class IntakeClosingProfile:
    def __init__(self, closing_provenance: Provenance) -> None:
        self._closing_provenance = closing_provenance

    def lift_at(self, angle: Angle) -> Quantity:
        provenance = self._closing_provenance if angle == Angle.crank(228.5) else Provenance.INFERRED
        # White-box test double: stamp a runtime-chosen provenance the way the
        # profile facade does, via the keyed projection mint.
        return Quantity._mint(0.050, "inch", "valve_side", provenance)

    def velocity_at(self, angle: Angle) -> Quantity:
        return extrapolated(0.0, InchPerDeg, "valve_side")

    def acceleration_at(self, angle: Angle) -> Quantity:
        return extrapolated(0.0, InchPerDeg2, "valve_side")

    def jerk_at(self, angle: Angle) -> Quantity:
        return extrapolated(0.0, InchPerDeg3, "valve_side")

    def events_at_lift(self, lift: Quantity) -> list[Angle]:
        return [Angle.crank(710.5), Angle.crank(228.5)]

    def duration_at_lift(self, lift: Quantity) -> Angle:
        return Angle.crank(238.0)

    def max_lift(self) -> Quantity:
        return inferred(0.360, Inch, "valve_side")

    def area_under_curve(self) -> Quantity:
        return inferred(42.0, InchDeg, "valve_side")

    def is_good_enough_for(self, kind: AnalysisKind) -> bool:
        return kind in {AnalysisKind.DCR, AnalysisKind.REPORT}


def _input(*, allow_extrapolated: bool = False, rod_length: float = 96.9) -> DynamicCompressionInput:
    return DynamicCompressionInput(
        static_compression_ratio=12.8,
        geometry=EngineGeometry.from_mm(bore=77.0, stroke=53.6, rod_length=rod_length),
        closing_lift=inferred(0.050, Inch, "valve_side"),
        allow_extrapolated=allow_extrapolated,
    )


def test_analyze_dynamic_compression_returns_stamped_result_from_intake_closing() -> None:
    result = analyze_dynamic_compression(IntakeClosingProfile(Provenance.INFERRED), _input())

    assert not isinstance(result, Refusal)
    assert 1.0 < float(result.dynamic_compression_ratio) < 12.8
    assert result.dynamic_compression_ratio.provenance == Provenance.INFERRED
    assert result.intake_closing_angle == Angle.crank(228.5)


def test_dynamic_compression_refuses_unsupported_low_lift_evidence_by_default() -> None:
    result = analyze_dynamic_compression(IntakeClosingProfile(Provenance.EXTRAPOLATED), _input())

    assert isinstance(result, Refusal)
    assert result.requested == "dynamic compression ratio"
    assert result.provenance == Provenance.EXTRAPOLATED
    assert "intake closing" in result.reason


def test_dynamic_compression_can_loudly_downgrade_when_allowed() -> None:
    result = analyze_dynamic_compression(
        IntakeClosingProfile(Provenance.EXTRAPOLATED),
        _input(allow_extrapolated=True),
    )

    assert not isinstance(result, Refusal)
    assert result.dynamic_compression_ratio.provenance == Provenance.EXTRAPOLATED


def test_legacy_dynamic_compression_ratio_wrapper_accepts_source_agnostic_numbers() -> None:
    result = dynamic_compression_ratio(
        IntakeClosingProfile(Provenance.INFERRED),
        static_cr=12.8,
        bore_mm=77.0,
        stroke_mm=53.6,
        rod_length_mm=96.9,
    )

    assert not isinstance(result, Refusal)
    assert 1.0 < float(result) < 12.8


def test_cam_card_dcr_accepts_published_closing_boundary() -> None:
    # The intake closing event sits exactly on the published @0.050" boundary.
    # That event must read back as INFERRED cam-card evidence, not extrapolated,
    # so DCR at the published threshold does not spuriously refuse.
    intake = profiles_from_cam_card(CamCard.wr250r_reference()).intake

    result = analyze_dynamic_compression(intake, _input())

    assert not isinstance(result, Refusal)
    assert result.dynamic_compression_ratio.provenance == Provenance.INFERRED
    assert 1.0 < float(result.dynamic_compression_ratio) < 12.8


def test_effective_stroke_and_dcr_depend_on_rod_length() -> None:
    # Same profile, static CR, bore, stroke, and closing lift; only the rod length
    # changes. Crank-slider geometry must make both effective stroke and DCR move.
    intake = profiles_from_cam_card(CamCard.wr250r_reference()).intake

    short_rod = analyze_dynamic_compression(intake, _input(rod_length=96.9))
    long_rod = analyze_dynamic_compression(intake, _input(rod_length=140.0))

    assert not isinstance(short_rod, Refusal)
    assert not isinstance(long_rod, Refusal)
    assert float(short_rod.effective_stroke_mm) != float(long_rod.effective_stroke_mm)
    assert float(short_rod.dynamic_compression_ratio) != float(long_rod.dynamic_compression_ratio)
