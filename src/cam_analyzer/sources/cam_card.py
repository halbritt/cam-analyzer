"""Cam-card source factories for Milestone 1 (D003)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from cam_analyzer.profile.canonical import CanonicalCamProfile, CanonicalLiftModel, LiftOperator
from cam_analyzer.profile.provenance_map import ProvenanceMap
from cam_analyzer.quantity import Provenance

CHECKING_LIFT_IN = 0.050
NOSE_UNSUPPORTED_HALF_WIDTH_DEG = 6.0
# Below this sin(phase) the fitted sine-power's high-order analytic derivatives
# blow up (negative fractional powers near the flank edges). Even the opt-in
# approximation refuses there rather than return a meaningless spike.
_APPROX_MIN_SINE = 0.05
# The published @0.050" opening/closing angles sit on the inferred region's
# boundary. Regions are half-open [start, end), so the closing angle (a region
# end) would otherwise read back as EXTRAPOLATED. Pad each inferred span by a
# sub-detection epsilon — far below any real crank-angle spacing and orders of
# magnitude above the event finder's precision — so both published boundary
# events stamp INFERRED while the nose gap and pre-open/post-close arcs stay
# EXTRAPOLATED.
_BOUNDARY_EPSILON_DEG = 1e-6

CamSide = Literal["intake", "exhaust"]


@dataclass(frozen=True, slots=True)
class CamLobeSpec:
    valve_lift_in: float
    advertised_duration_deg: float
    duration_050_deg: float
    lobe_center_deg: float
    lash_in: float

    def __post_init__(self) -> None:
        # Physically-impossible cam cards must not construct (GitHub issue #4):
        # a valve lift, advertised duration, and duration@0.050" are all strictly
        # positive magnitudes, and valve lash is a non-negative clearance.
        if self.valve_lift_in <= 0.0:
            raise ValueError("valve_lift_in must be positive")
        if self.valve_lift_in <= CHECKING_LIFT_IN:
            raise ValueError("valve_lift_in must exceed duration@0.050 checking lift")
        if self.advertised_duration_deg <= 0.0:
            raise ValueError("advertised_duration_deg must be positive")
        if self.duration_050_deg <= 0.0:
            raise ValueError("duration_050_deg must be positive")
        # A conformance-relevant invariant: advertised duration cannot be tighter
        # than duration @ 0.050" (trap: `advertised_lt_050`).
        if self.advertised_duration_deg < self.duration_050_deg:
            raise ValueError("advertised_duration < duration@0.050\" — incoherent cam card")
        if self.advertised_duration_deg == self.duration_050_deg:
            raise ValueError("advertised_duration must be wider than duration@0.050")
        if self.advertised_duration_deg >= 720.0:
            raise ValueError("advertised_duration_deg must be less than one crank cycle")
        if not 0.0 <= self.lobe_center_deg < 720.0:
            raise ValueError("lobe_center_deg must be in [0, 720)")
        if self.lash_in < 0.0:
            raise ValueError("lash_in must be non-negative")


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


@dataclass(frozen=True, slots=True)
class CamCardProfiles:
    """The explicit two-profile result of a cam-card source ingest."""

    intake: CanonicalCamProfile
    exhaust: CanonicalCamProfile


class SinePowerCamCardOperator:
    """Sine-power cam-card approximation fitted to the published card.

    Satisfies :class:`LiftOperator` structurally, not by subclassing (#6); the
    static conformance check lives at the foot of this module.

    A fixed ``sin^2`` half-sine cannot fit both advertised duration and the
    duration at 0.050 in for the reference card. This operator uses the named
    variant ``peak * sin(pi * t / advertised_duration) ** power`` and solves the
    exponent so the curve crosses 0.050 in at the published duration. The curve
    remains an approximation and never produces MEASURED evidence.
    """

    name = "SinePowerCamCardApproximation"

    def __init__(self, lobe: CamLobeSpec, side: CamSide):
        self._lobe = lobe
        self._side = side
        self._centerline_crank_deg = _centerline_crank_deg(lobe, side)
        self._power = self._fit_power(lobe)

    @property
    def side(self) -> CamSide:
        return self._side

    @property
    def centerline_crank_deg(self) -> float:
        return self._centerline_crank_deg

    @property
    def advertised_open_deg(self) -> float:
        return (self._centerline_crank_deg - self._lobe.advertised_duration_deg / 2.0) % 720.0

    @property
    def advertised_close_deg(self) -> float:
        return (self._centerline_crank_deg + self._lobe.advertised_duration_deg / 2.0) % 720.0

    @property
    def opening_050_deg(self) -> float:
        return (self._centerline_crank_deg - self._lobe.duration_050_deg / 2.0) % 720.0

    @property
    def closing_050_deg(self) -> float:
        return (self._centerline_crank_deg + self._lobe.duration_050_deg / 2.0) % 720.0

    @property
    def power(self) -> float:
        return self._power

    def evaluate(self, crank_deg: float) -> float:
        offset = self._offset_from_center(crank_deg)
        half_duration = self._lobe.advertised_duration_deg / 2.0
        if abs(offset) > half_duration:
            return 0.0

        t = offset + half_duration
        phase = math.pi * t / self._lobe.advertised_duration_deg
        sine = max(0.0, math.sin(phase))
        return float(self._lobe.valve_lift_in * sine**self._power)

    def derivative(self, order: int, crank_deg: float) -> float:
        if order != 1:
            raise ValueError("cam-card approximation supports only first derivative in mid-flank regions")
        if self.max_supported_derivative(crank_deg) < 1:
            raise ValueError("first derivative unsupported in low-lift, nose, or closed regions")

        offset = self._offset_from_center(crank_deg)
        t = offset + self._lobe.advertised_duration_deg / 2.0
        phase = math.pi * t / self._lobe.advertised_duration_deg
        sine = math.sin(phase)
        cosine = math.cos(phase)
        scale = math.pi / self._lobe.advertised_duration_deg
        return float(
            self._lobe.valve_lift_in
            * self._power
            * sine ** (self._power - 1.0)
            * cosine
            * scale
        )

    def max_supported_derivative(self, crank_deg: float) -> int:
        offset = abs(self._offset_from_center(crank_deg))
        if offset >= self._lobe.duration_050_deg / 2.0:
            return 0
        if offset <= NOSE_UNSUPPORTED_HALF_WIDTH_DEG:
            return 0
        return 1

    def max_approximate_derivative(self, crank_deg: float) -> int:
        """Highest order this operator can *approximate* (orders 1-3).

        A ballpark only — distinct from :meth:`max_supported_derivative`, which is
        what the operator can *justify*. Returns 3 across the active lobe (nose and
        mid-flank), 0 in the closed region and at the extreme flank edges where the
        analytic high-order derivatives blow up.
        """
        offset = self._offset_from_center(crank_deg)
        half_duration = self._lobe.advertised_duration_deg / 2.0
        if abs(offset) >= half_duration:
            return 0
        phase = math.pi * (offset + half_duration) / self._lobe.advertised_duration_deg
        if math.sin(phase) < _APPROX_MIN_SINE:
            return 0
        return 3

    def approximate_derivative(self, order: int, crank_deg: float) -> float:
        """Analytic n-th derivative of the fitted sine-power lobe (orders 1-3).

        For the opt-in approximate path only; callers stamp the result
        EXTRAPOLATED. The 2nd/3rd derivatives are governed by the assumed
        sine-power flank shape, not the cam card, so they are a ballpark, not
        analysis-grade.
        """
        if order not in (1, 2, 3):
            raise ValueError("approximate_derivative supports orders 1-3")
        offset = self._offset_from_center(crank_deg)
        half_duration = self._lobe.advertised_duration_deg / 2.0
        if abs(offset) > half_duration:
            return 0.0
        phase = math.pi * (offset + half_duration) / self._lobe.advertised_duration_deg
        cosine = math.cos(phase)
        sine = max(math.sin(phase), _APPROX_MIN_SINE)  # guard negative-power blow-up
        scale = math.pi / self._lobe.advertised_duration_deg
        power = self._power
        lift = self._lobe.valve_lift_in
        if order == 1:
            return float(lift * power * sine ** (power - 1.0) * cosine * scale)
        if order == 2:
            return float(
                lift * power * scale**2
                * ((power - 1.0) * sine ** (power - 2.0) * cosine**2 - sine**power)
            )
        return float(
            lift * power * scale**3
            * (
                (power - 1.0) * (power - 2.0) * sine ** (power - 3.0) * cosine**3
                - (3.0 * power - 2.0) * sine ** (power - 1.0) * cosine
            )
        )

    def _offset_from_center(self, crank_deg: float) -> float:
        return ((crank_deg - self._centerline_crank_deg + 360.0) % 720.0) - 360.0

    @staticmethod
    def _fit_power(lobe: CamLobeSpec) -> float:
        ramp_width = (lobe.advertised_duration_deg - lobe.duration_050_deg) / 2.0
        base = math.sin(math.pi * ramp_width / lobe.advertised_duration_deg)
        target = CHECKING_LIFT_IN / lobe.valve_lift_in
        if not 0.0 < base < 1.0 or not 0.0 < target < 1.0:
            raise ValueError("cam-card durations cannot fit a sine-power approximation")
        return math.log(target) / math.log(base)


def profiles_from_cam_card(
    card: CamCard, *, approximate_derivatives: bool = False
) -> CamCardProfiles:
    """Return source-agnostic intake and exhaust profiles from one cam card.

    With ``approximate_derivatives=True`` the profiles answer otherwise-refused
    higher derivatives (acceleration/jerk, and velocity at the nose) with an
    EXTRAPOLATED ballpark instead of a Refusal — useful for a rough shape, but
    never trustworthy enough to pass the cliff-analysis fitness gates.
    """
    return CamCardProfiles(
        intake=intake_profile_from_cam_card(
            card, approximate_derivatives=approximate_derivatives
        ),
        exhaust=exhaust_profile_from_cam_card(
            card, approximate_derivatives=approximate_derivatives
        ),
    )


def intake_profile_from_cam_card(
    card: CamCard, *, approximate_derivatives: bool = False
) -> CanonicalCamProfile:
    return _profile_from_lobe(
        card.intake, "intake", approximate_derivatives=approximate_derivatives
    )


def exhaust_profile_from_cam_card(
    card: CamCard, *, approximate_derivatives: bool = False
) -> CanonicalCamProfile:
    return _profile_from_lobe(
        card.exhaust, "exhaust", approximate_derivatives=approximate_derivatives
    )


def _profile_from_lobe(
    lobe: CamLobeSpec, side: CamSide, *, approximate_derivatives: bool = False
) -> CanonicalCamProfile:
    operator = SinePowerCamCardOperator(lobe, side)
    samples = tuple(operator.evaluate(float(degree)) for degree in range(720))
    model = CanonicalLiftModel(
        samples_720=samples,
        operator=operator,
        provenance=_provenance_for_cam_card_operator(operator),
        approximate_derivatives=approximate_derivatives,
    )
    return CanonicalCamProfile(model)


def _provenance_for_cam_card_operator(operator: SinePowerCamCardOperator) -> ProvenanceMap:
    center = operator.centerline_crank_deg
    inferred_regions = (
        (
            operator.opening_050_deg - _BOUNDARY_EPSILON_DEG,
            (center - NOSE_UNSUPPORTED_HALF_WIDTH_DEG) % 720.0,
            Provenance.INFERRED,
        ),
        (
            (center + NOSE_UNSUPPORTED_HALF_WIDTH_DEG) % 720.0,
            operator.closing_050_deg + _BOUNDARY_EPSILON_DEG,
            Provenance.INFERRED,
        ),
    )
    return ProvenanceMap.from_default_and_regions(Provenance.EXTRAPOLATED, inferred_regions)


def _centerline_crank_deg(lobe: CamLobeSpec, side: CamSide) -> float:
    if side == "intake":
        return lobe.lobe_center_deg % 720.0
    return (-lobe.lobe_center_deg) % 720.0


if TYPE_CHECKING:
    # Static structural-conformance check (#6): mypy errors here if the operator
    # stops satisfying the LiftOperator Protocol.
    def _assert_sine_power_is_a_lift_operator(op: SinePowerCamCardOperator) -> LiftOperator:
        return op


__all__ = [
    "CHECKING_LIFT_IN",
    "CamCard",
    "CamCardProfiles",
    "CamLobeSpec",
    "SinePowerCamCardOperator",
    "exhaust_profile_from_cam_card",
    "intake_profile_from_cam_card",
    "profiles_from_cam_card",
]
