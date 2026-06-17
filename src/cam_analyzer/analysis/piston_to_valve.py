"""Piston-to-valve safety surface."""

from __future__ import annotations

from dataclasses import dataclass

from cam_analyzer.analysis.safety import PTV_EXHAUST_POLICY, PTV_INTAKE_POLICY, ThresholdPolicy
from cam_analyzer.profile import AnalysisKind, CamProfile
from cam_analyzer.quantity import Inch, Quantity, Refusal, SafetyVerdict

PistonToValveVerdict = SafetyVerdict


@dataclass(frozen=True, slots=True)
class PistonToValveInput:
    valve: str
    threshold_policy: ThresholdPolicy
    measured_clearance: Quantity[Inch] | None = None


@dataclass(frozen=True, slots=True)
class PistonToValveResult:
    verdict: PistonToValveVerdict
    threshold_policy: ThresholdPolicy
    margin: Quantity[Inch] | None
    explanation: str


def default_intake_policy() -> ThresholdPolicy:
    return PTV_INTAKE_POLICY


def default_exhaust_policy() -> ThresholdPolicy:
    return PTV_EXHAUST_POLICY


def evaluate_piston_to_valve(
    profile: CamProfile,
    inputs: PistonToValveInput,
) -> PistonToValveResult | Refusal:
    if inputs.measured_clearance is None or not profile.is_good_enough_for(AnalysisKind.PTV):
        return PistonToValveResult(
            verdict=PistonToValveVerdict.UNDECIDABLE_FROM_CAM_CARD,
            threshold_policy=inputs.threshold_policy,
            margin=None,
            explanation=(
                "Cam card evidence is insufficient for a physical piston-to-valve "
                "clearance verdict without measured clearance data."
            ),
        )
    try:
        _require_policy_compatible(inputs.measured_clearance, inputs.threshold_policy)
    except ValueError as exc:
        return Refusal(
            requested=f"{inputs.valve} piston-to-valve verdict",
            reason=str(exc),
            remedy="Provide clearance and threshold values with matching unit and frame.",
            provenance=inputs.measured_clearance.provenance,
        )
    margin = inputs.measured_clearance - inputs.threshold_policy.minimum
    verdict = PistonToValveVerdict.PASS if float(margin) >= 0.0 else PistonToValveVerdict.FAIL
    return PistonToValveResult(
        verdict=verdict,
        threshold_policy=inputs.threshold_policy,
        margin=margin,
        explanation=(
            f"{inputs.valve} clearance compared with {inputs.threshold_policy.name} "
            f"owned by {inputs.threshold_policy.owner}."
        ),
    )


def _require_policy_compatible(clearance: Quantity[Inch], policy: ThresholdPolicy) -> None:
    if clearance.unit != policy.minimum.unit or clearance.frame != policy.minimum.frame:
        raise ValueError("clearance and PTV policy must use the same unit/frame")


__all__ = [
    "PistonToValveInput",
    "PistonToValveResult",
    "PistonToValveVerdict",
    "default_exhaust_policy",
    "default_intake_policy",
    "evaluate_piston_to_valve",
]
