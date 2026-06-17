"""Source-blind profile quality summaries for reports and charts."""

from __future__ import annotations

from dataclasses import dataclass

from cam_analyzer.profile import CamProfile
from cam_analyzer.quantity import Angle, Crank, Inch, ProvFloat, Provenance, Quantity, Refusal, inferred

DEFAULT_THRESHOLD_LIFTS_IN = (0.001, 0.006, 0.020, 0.050, 0.100, 0.200)
_CYCLE_DEGREES = 720.0
_SAMPLE_STEP_DEG = 2.0
_SYMMETRY_OFFSETS_DEG = (20.0, 40.0, 60.0, 80.0, 100.0)
_SYMMETRY_RATIO_TOLERANCE = 0.025
_HIGH_LIFT_DWELL_RATIO = 0.98
_HIGH_LIFT_DWELL_WARN_DEG = 24.0
_ACCELERATION_WARN_IN_PER_DEG2 = 0.001
_JERK_WARN_IN_PER_DEG3 = 0.001


@dataclass(frozen=True, slots=True)
class LiftThresholdDuration:
    threshold: ProvFloat
    events: tuple[Angle[Crank], ...]
    duration: Angle[Crank]


@dataclass(frozen=True, slots=True)
class ProfileQualityWarning:
    code: str
    severity: str
    message: str


def threshold_duration_table(
    profile: CamProfile,
    thresholds_in: tuple[float, ...] = DEFAULT_THRESHOLD_LIFTS_IN,
) -> tuple[LiftThresholdDuration, ...]:
    """Return the standard cam-card duration table through the CamProfile API."""

    rows: list[LiftThresholdDuration] = []
    for threshold_in in thresholds_in:
        threshold = inferred(threshold_in, Inch, "valve_side")
        rows.append(
            LiftThresholdDuration(
                threshold=threshold,
                events=tuple(profile.events_at_lift(threshold)),
                duration=profile.duration_at_lift(threshold),
            )
        )
    return tuple(rows)


def confidence_band_for_answer(answer: object, scale: float) -> dict[str, object] | None:
    """Return 50/95 percent half-widths for a serialized sample scale."""

    if not isinstance(answer, Quantity):
        return None
    base = max(abs(scale), abs(float(answer)), 1e-9)
    p50_ratio, p95_ratio = _uncertainty_ratios(answer.provenance)
    return {
        "p50_half_width": base * p50_ratio,
        "p95_half_width": base * p95_ratio,
        "unit": answer.unit,
        "basis": answer.provenance.name,
    }


def profile_quality_warnings(profile: CamProfile) -> tuple[ProfileQualityWarning, ...]:
    """Flag profile shapes that are suspicious or underconstrained."""

    warnings: list[ProfileQualityWarning] = []
    max_lift = profile.max_lift()
    max_lift_value = float(max_lift)
    if max_lift.provenance is not Provenance.MEASURED:
        warnings.append(
            ProfileQualityWarning(
                "underconstrained_reconstruction",
                "warning",
                "Cam-card reconstruction is model-derived; replace with measured lift data before using derivative-sensitive conclusions.",
            )
        )
    warnings.extend(_symmetry_warnings(profile, max_lift_value))
    warnings.extend(_high_lift_warnings(profile, max_lift_value))
    warnings.extend(_derivative_warnings(profile))
    return tuple(warnings)


def _uncertainty_ratios(provenance: Provenance) -> tuple[float, float]:
    if provenance is Provenance.MEASURED:
        return 0.001, 0.002
    if provenance is Provenance.INFERRED:
        return 0.015, 0.050
    return 0.050, 0.180


def _symmetry_warnings(
    profile: CamProfile,
    max_lift_value: float,
) -> tuple[ProfileQualityWarning, ...]:
    if max_lift_value <= 0.0:
        return ()
    peak_deg = _peak_degree(profile)
    differences = []
    for offset in _SYMMETRY_OFFSETS_DEG:
        left = float(profile.lift_at(Angle.crank(peak_deg - offset)))
        right = float(profile.lift_at(Angle.crank(peak_deg + offset)))
        differences.append(abs(left - right))
    mean_difference = sum(differences) / len(differences)
    if mean_difference / max_lift_value > _SYMMETRY_RATIO_TOLERANCE:
        return ()
    return (
        ProfileQualityWarning(
            "implausibly_symmetric_lobe",
            "warning",
            "Opening and closing flanks are nearly mirror-symmetric; the cam card does not constrain real asymmetric flank behavior.",
        ),
    )


def _high_lift_warnings(
    profile: CamProfile,
    max_lift_value: float,
) -> tuple[ProfileQualityWarning, ...]:
    if max_lift_value <= 0.0:
        return ()
    high_lift = inferred(max_lift_value * _HIGH_LIFT_DWELL_RATIO, Inch, "valve_side")
    duration = profile.duration_at_lift(high_lift).degrees
    if duration <= _HIGH_LIFT_DWELL_WARN_DEG:
        return ()
    return (
        ProfileQualityWarning(
            "long_high_lift_dwell",
            "warning",
            f"Duration above {_HIGH_LIFT_DWELL_RATIO:.0%} of peak lift is {duration:.1f} crank degrees; treat the plateau as a motion-law assumption, not measured dwell.",
        ),
    )


def _derivative_warnings(profile: CamProfile) -> tuple[ProfileQualityWarning, ...]:
    acceleration = _max_abs_derivative(profile, order=2)
    jerk = _max_abs_derivative(profile, order=3)
    warnings: list[ProfileQualityWarning] = [
        ProfileQualityWarning(
            "model_derived_derivatives",
            "info",
            "Velocity, acceleration, and jerk are derivatives of the cam-card motion law, not measured valvetrain data.",
        )
    ]
    if acceleration > _ACCELERATION_WARN_IN_PER_DEG2:
        warnings.append(
            ProfileQualityWarning(
                "excessive_model_acceleration",
                "warning",
                f"Model acceleration reaches {acceleration:.6f} in/deg^2; inspect the SVAJ stack before trusting the reconstruction.",
            )
        )
    if jerk > _JERK_WARN_IN_PER_DEG3:
        warnings.append(
            ProfileQualityWarning(
                "excessive_model_jerk",
                "warning",
                f"Model jerk reaches {jerk:.6f} in/deg^3; inspect the SVAJ stack before trusting the reconstruction.",
            )
        )
    return tuple(warnings)


def _peak_degree(profile: CamProfile) -> float:
    sampled = tuple(
        (degree, float(profile.lift_at(Angle.crank(degree))))
        for degree in _sample_degrees()
    )
    max_lift = max(lift for _, lift in sampled)
    plateau_degrees = [
        degree for degree, lift in sampled if lift >= max_lift * 0.999
    ]
    return sum(plateau_degrees) / len(plateau_degrees)


def _max_abs_derivative(profile: CamProfile, *, order: int) -> float:
    values = []
    for degree in _sample_degrees():
        answer = profile.acceleration_at(Angle.crank(degree)) if order == 2 else profile.jerk_at(Angle.crank(degree))
        if not isinstance(answer, Refusal):
            values.append(abs(float(answer)))
    return max(values, default=0.0)


def _sample_degrees() -> tuple[float, ...]:
    return tuple(
        point_index * _SAMPLE_STEP_DEG
        for point_index in range(int(_CYCLE_DEGREES / _SAMPLE_STEP_DEG))
    )


__all__ = [
    "DEFAULT_THRESHOLD_LIFTS_IN",
    "LiftThresholdDuration",
    "ProfileQualityWarning",
    "confidence_band_for_answer",
    "profile_quality_warnings",
    "threshold_duration_table",
]
