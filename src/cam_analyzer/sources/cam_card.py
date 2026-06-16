"""CamCard source (Milestone 1 / D003).

``CamCard`` is the sparse published-spec record. ``CamCardApproxProfile`` is the
crude, explicitly-throwaway Milestone-1 profile backed by one
``HalfSineCamCardOperator``. A cam-card approximation can never claim MEASURED
provenance — it invents the seat-ramp/low-lift region it does not know (D002/D006).
"""

from __future__ import annotations

from dataclasses import dataclass

from cam_analyzer.profile.canonical import CanonicalCamProfile, LiftOperator


@dataclass(frozen=True, slots=True)
class CamLobeSpec:
    valve_lift_in: float
    advertised_duration_deg: float
    duration_050_deg: float
    lobe_center_deg: float
    lash_in: float

    def __post_init__(self) -> None:
        # A conformance-relevant invariant: advertised duration cannot be tighter
        # than duration @ 0.050" (trap: `advertised_lt_050`).
        if self.advertised_duration_deg < self.duration_050_deg:
            raise ValueError("advertised_duration < duration@0.050\" — incoherent cam card")


@dataclass(frozen=True, slots=True)
class CamCard:
    """Sparse published timing specs. Never importable by analysis (C1)."""

    intake: CamLobeSpec
    exhaust: CamLobeSpec

    @staticmethod
    def wr250r_reference() -> "CamCard":
        """The Web Cam 81-651 reference numbers (see docs/reference/spec.md)."""
        return CamCard(
            intake=CamLobeSpec(0.360, 262.0, 238.0, 109.5, 0.006),
            exhaust=CamLobeSpec(0.360, 270.0, 246.0, 104.5, 0.008),
        )


class HalfSineCamCardOperator(LiftOperator):
    """`peak * sin^2` over the duration window, zero elsewhere (round-1 B4·I2).

    Crude, continuous, differentiable — but its smoothness is a *fiction* away
    from the cam-card anchors; jerk it reports must be marked low-provenance.
    """

    name = "HalfSineApproximation"

    def __init__(self, lobe: CamLobeSpec):
        self._lobe = lobe

    def evaluate(self, crank_deg: float) -> float:
        raise NotImplementedError("half-sine lobe from peak lift + duration + center")

    def derivative(self, order: int, crank_deg: float) -> float:
        raise NotImplementedError("analytic derivative of the half-sine; flag low provenance")


def CamCardApproxProfile(card: CamCard) -> CanonicalCamProfile:  # noqa: N802 (factory)
    """Milestone-1 factory: cam card -> CamProfile, all values INFERRED/EXTRAPOLATED."""
    raise NotImplementedError(
        "build a CanonicalLiftModel from a HalfSineCamCardOperator with an "
        "all-INFERRED ProvenanceMap (EXTRAPOLATED across the unsupported nose) — D003/D006"
    )
