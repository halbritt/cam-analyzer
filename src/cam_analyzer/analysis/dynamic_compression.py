"""Approximate dynamic compression from a source-blind CamProfile."""

from __future__ import annotations

import math
from dataclasses import dataclass

from cam_analyzer.profile import CamProfile
from cam_analyzer.quantity import Answer, Angle, ProvFloat, Provenance, Refusal


@dataclass(frozen=True, slots=True)
class EngineGeometry:
    bore_mm: float
    stroke_mm: float
    rod_length_mm: float

    def __post_init__(self) -> None:
        if self.bore_mm <= 0 or self.stroke_mm <= 0 or self.rod_length_mm <= 0:
            raise ValueError("engine dimensions must be positive")

    @staticmethod
    def from_mm(
        *,
        bore: float,
        stroke: float,
        rod_length: float,
    ) -> "EngineGeometry":
        return EngineGeometry(bore, stroke, rod_length)


@dataclass(frozen=True, slots=True)
class DynamicCompressionInput:
    static_compression_ratio: float
    geometry: EngineGeometry
    closing_lift: ProvFloat
    allow_extrapolated: bool = False

    def __post_init__(self) -> None:
        if self.static_compression_ratio <= 1.0:
            raise ValueError("static compression ratio must be greater than 1")


@dataclass(frozen=True, slots=True)
class DynamicCompressionResult:
    ratio: ProvFloat
    effective_stroke: ProvFloat
    intake_closing: Angle

    @property
    def dynamic_compression_ratio(self) -> ProvFloat:
        return self.ratio

    @property
    def effective_stroke_mm(self) -> ProvFloat:
        return self.effective_stroke

    @property
    def intake_closing_angle(self) -> Angle:
        return self.intake_closing


def dynamic_compression_ratio(
    intake: CamProfile,
    static_cr: float,
    bore_mm: float,
    stroke_mm: float,
    rod_length_mm: float,
) -> Answer:
    """Compatibility wrapper returning only the stamped DCR or a refusal."""
    result = analyze_dynamic_compression(
        intake,
        DynamicCompressionInput(
            static_compression_ratio=static_cr,
            geometry=EngineGeometry(bore_mm, stroke_mm, rod_length_mm),
            closing_lift=ProvFloat(0.050, "inch", "valve_side", Provenance.INFERRED),
        ),
    )
    if isinstance(result, Refusal):
        return result
    return result.dynamic_compression_ratio


def analyze_dynamic_compression(
    intake: CamProfile,
    inputs: DynamicCompressionInput,
) -> DynamicCompressionResult | Refusal:
    """Compute approximate DCR from the intake closing event.

    Seat/low-lift closing is exactly where a cam-card approximation is weakest.
    If the profile reports that closing evidence as extrapolated, this function
    refuses instead of laundering it into a precise compression number.
    """
    threshold = inputs.closing_lift
    events = intake.events_at_lift(threshold)
    closing = _intake_closing_event(events)
    if closing is None:
        return Refusal(
            requested="dynamic compression ratio",
            reason="profile did not produce an intake closing event at the requested seat lift",
            remedy="Use a profile with measured low-lift closing data or request a supported lift threshold.",
            provenance=threshold.provenance,
        )

    closing_lift = intake.lift_at(closing)
    provenance = Provenance.join(threshold.provenance, closing_lift.provenance)
    if provenance <= Provenance.EXTRAPOLATED and not inputs.allow_extrapolated:
        return Refusal(
            requested="dynamic compression ratio",
            reason="intake closing depends on extrapolated low-lift cam-card evidence",
            remedy="Measure seat/low-lift intake closing or use a measured lift profile.",
            provenance=provenance,
        )

    effective_stroke = _effective_stroke_from_closing(
        inputs.geometry.stroke_mm,
        inputs.geometry.rod_length_mm,
        closing.degrees,
    )
    dcr = 1.0 + (
        inputs.static_compression_ratio - 1.0
    ) * (effective_stroke / inputs.geometry.stroke_mm)
    return DynamicCompressionResult(
        ratio=ProvFloat.ratio(dcr, provenance),
        effective_stroke=ProvFloat(effective_stroke, "mm", "engine", provenance),
        intake_closing=closing,
    )


def _intake_closing_event(events: list[Angle]) -> Angle | None:
    if not events:
        return None
    after_bdc = [event for event in events if 180.0 <= event.degrees <= 360.0]
    if after_bdc:
        return min(after_bdc, key=lambda event: event.degrees)
    after_tdc = [event for event in events if event.degrees > 180.0]
    if after_tdc:
        return min(after_tdc, key=lambda event: event.degrees)
    return max(events, key=lambda event: event.degrees)


def _effective_stroke_from_closing(stroke_mm: float, rod_length_mm: float, crank_deg: float) -> float:
    """Piston displacement from TDC at intake closing, via crank-slider geometry.

    The effective stroke is how far the piston has yet to travel toward TDC when
    the intake valve closes; that is the portion of the stroke over which real
    compression happens. Using the crank-slider relation (rather than a linear
    ABDC approximation) makes rod length a first-class input: a longer rod dwells
    the piston nearer TDC, changing the displacement at a fixed closing angle.
    The number stays approximate, but every supplied geometry input now matters.
    """
    crank_radius_mm = stroke_mm / 2.0
    if rod_length_mm <= crank_radius_mm:
        raise ValueError("rod length is too short for the supplied stroke")
    closing_abdc = (crank_deg - 180.0) % 360.0
    if closing_abdc > 180.0:
        # Closing resolved before BDC; the whole stroke is still available.
        closing_abdc = 0.0
    # Crank angle measured from TDC. Intake closing sits at 180 deg + ABDC.
    theta = math.radians(180.0 + closing_abdc)
    rod_ratio = crank_radius_mm / rod_length_mm
    axial_displacement_mm = crank_radius_mm * (1.0 - math.cos(theta)) + rod_length_mm * (
        1.0 - math.sqrt(1.0 - (rod_ratio * math.sin(theta)) ** 2)
    )
    return max(0.0, axial_displacement_mm)
