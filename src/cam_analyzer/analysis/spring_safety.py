"""Valve spring and retainer safety surface."""

from __future__ import annotations

from dataclasses import dataclass

from cam_analyzer.analysis.safety import RETAINER_TO_GUIDE_POLICY, SPRING_COIL_POLICY
from cam_analyzer.profile import AnalysisKind, CamProfile
from cam_analyzer.quantity import ProvFloat, Refusal, SafetyVerdict

SpringSafetyVerdict = SafetyVerdict


@dataclass(frozen=True, slots=True)
class SpringThresholdPolicy:
    name: str
    retainer_to_guide_minimum: ProvFloat
    coil_minimum: ProvFloat
    owner: str


@dataclass(frozen=True, slots=True)
class SpringSafetyInput:
    threshold_policy: SpringThresholdPolicy
    retainer_to_guide_clearance: ProvFloat | None = None
    coil_clearance: ProvFloat | None = None


@dataclass(frozen=True, slots=True)
class SpringSafetyResult:
    verdict: SpringSafetyVerdict
    threshold_policy: SpringThresholdPolicy
    retainer_to_guide_margin: ProvFloat | None
    coil_margin: ProvFloat | None
    explanation: str


def default_spring_policy() -> SpringThresholdPolicy:
    return SpringThresholdPolicy(
        name="spring and retainer minimum clearances",
        retainer_to_guide_minimum=RETAINER_TO_GUIDE_POLICY.minimum,
        coil_minimum=SPRING_COIL_POLICY.minimum,
        owner="Camshaft_Analysis_Spec.md",
    )


def evaluate_spring_safety(profile: CamProfile, inputs: SpringSafetyInput) -> SpringSafetyResult | Refusal:
    if (
        inputs.retainer_to_guide_clearance is None
        or inputs.coil_clearance is None
        or not profile.is_good_enough_for(AnalysisKind.SPRING_SAFETY)
    ):
        return SpringSafetyResult(
            verdict=SpringSafetyVerdict.UNDECIDABLE_FROM_CAM_CARD,
            threshold_policy=inputs.threshold_policy,
            retainer_to_guide_margin=None,
            coil_margin=None,
            explanation=(
                "Cam card evidence and missing spring measurements are insufficient "
                "for a valve spring safety verdict."
            ),
        )

    try:
        _require_compatible(
            inputs.retainer_to_guide_clearance,
            inputs.threshold_policy.retainer_to_guide_minimum,
        )
        _require_compatible(inputs.coil_clearance, inputs.threshold_policy.coil_minimum)
    except ValueError as exc:
        return Refusal(
            requested="spring safety verdict",
            reason=str(exc),
            remedy="Provide spring clearances and thresholds with matching unit and frame.",
            provenance=inputs.retainer_to_guide_clearance.provenance,
        )
    retainer_margin = inputs.retainer_to_guide_clearance - inputs.threshold_policy.retainer_to_guide_minimum
    coil_margin = inputs.coil_clearance - inputs.threshold_policy.coil_minimum
    verdict = (
        SpringSafetyVerdict.PASS
        if float(retainer_margin) >= 0.0 and float(coil_margin) >= 0.0
        else SpringSafetyVerdict.FAIL
    )
    return SpringSafetyResult(
        verdict=verdict,
        threshold_policy=inputs.threshold_policy,
        retainer_to_guide_margin=retainer_margin,
        coil_margin=coil_margin,
        explanation=f"Spring clearances compared with {inputs.threshold_policy.owner}.",
    )


def _require_compatible(clearance: ProvFloat, threshold: ProvFloat) -> None:
    if clearance.unit != threshold.unit or clearance.frame != threshold.frame:
        raise ValueError("spring clearance and threshold must use the same unit/frame")


__all__ = [
    "SpringSafetyInput",
    "SpringSafetyResult",
    "SpringSafetyVerdict",
    "SpringThresholdPolicy",
    "default_spring_policy",
    "evaluate_spring_safety",
]
