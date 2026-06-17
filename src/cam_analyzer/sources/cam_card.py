"""Cam-card source factories for Milestone 1 (D003)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from cam_analyzer.profile.canonical import CanonicalCamProfile, CanonicalLiftModel, LiftOperator
from cam_analyzer.profile.provenance_map import ProvenanceMap
from cam_analyzer.quantity import Provenance

CHECKING_LIFT_IN = 0.050
NOSE_UNSUPPORTED_HALF_WIDTH_DEG = 6.0
_HIGH_LIFT_DWELL_FRACTION = 0.08
_MIN_DWELL_HALF_WIDTH_DEG = 6.0
_MAX_DWELL_HALF_WIDTH_DEG = 14.0
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
class _HermiteSegment:
    start_offset_deg: float
    end_offset_deg: float
    start_lift_in: float
    end_lift_in: float
    start_velocity_in_per_deg: float
    end_velocity_in_per_deg: float
    start_accel_in_per_deg2: float = 0.0
    end_accel_in_per_deg2: float = 0.0

    def __post_init__(self) -> None:
        if self.end_offset_deg <= self.start_offset_deg:
            raise ValueError("Hermite segment end must be after start")

    def contains(self, offset_deg: float) -> bool:
        return self.start_offset_deg <= offset_deg <= self.end_offset_deg

    def evaluate(self, offset_deg: float, order: int = 0) -> float:
        span_deg = self.end_offset_deg - self.start_offset_deg
        u = (offset_deg - self.start_offset_deg) / span_deg
        values = _quintic_basis(order, u)
        scale = span_deg**order
        return (
            values[0] * self.start_lift_in
            + values[1] * span_deg * self.start_velocity_in_per_deg
            + values[2] * span_deg**2 * self.start_accel_in_per_deg2
            + values[3] * self.end_lift_in
            + values[4] * span_deg * self.end_velocity_in_per_deg
            + values[5] * span_deg**2 * self.end_accel_in_per_deg2
        ) / scale


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


class PolynomialMotionLawCamCardOperator:
    """Constrained cam-card reconstruction using piecewise quintic motion laws.

    Satisfies :class:`LiftOperator` structurally, not by subclassing (#6); the
    static conformance check lives at the foot of this module.

    The sparse cam card provides hard timing/lift constraints, not a measured lobe.
    This operator therefore uses a conservative motion-law reconstruction:
    lash ramp, opening flank, high-lift dwell, closing flank, and closing ramp
    are each quintic Hermite segments. Lift, velocity, and acceleration are
    continuous at every knot and jerk is finite, while all published events are
    enforced as construction constraints. The curve remains inferred/extrapolated
    cam-card evidence and never produces MEASURED lift.
    """

    name = "PolynomialMotionLawCamCardApproximation"

    def __init__(self, lobe: CamLobeSpec, side: CamSide):
        self._lobe = lobe
        self._side = side
        self._centerline_crank_deg = _centerline_crank_deg(lobe, side)
        self._dwell_half_width_deg = _dwell_half_width(lobe)
        self._threshold_velocity_in_per_deg = _threshold_velocity(lobe, self._dwell_half_width_deg)
        self._segments = _motion_segments(
            lobe,
            dwell_half_width_deg=self._dwell_half_width_deg,
            threshold_velocity_in_per_deg=self._threshold_velocity_in_per_deg,
        )

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
    def dwell_half_width_deg(self) -> float:
        return self._dwell_half_width_deg

    @property
    def threshold_velocity_in_per_deg(self) -> float:
        return self._threshold_velocity_in_per_deg

    def evaluate(self, crank_deg: float) -> float:
        offset = self._offset_from_center(crank_deg)
        return self._evaluate_offset(offset, order=0)

    def derivative(self, order: int, crank_deg: float) -> float:
        if order not in (1, 2, 3):
            raise ValueError("cam-card motion-law operator supports derivative orders 1-3")
        offset = self._offset_from_center(crank_deg)
        return self._evaluate_offset(offset, order=order)

    def max_supported_derivative(self, crank_deg: float) -> int:
        return 3

    def max_approximate_derivative(self, crank_deg: float) -> int:
        """Compatibility hook for the opt-in derivative path."""
        return self.max_supported_derivative(crank_deg)

    def approximate_derivative(self, order: int, crank_deg: float) -> float:
        return self.derivative(order, crank_deg)

    def _offset_from_center(self, crank_deg: float) -> float:
        return ((crank_deg - self._centerline_crank_deg + 360.0) % 720.0) - 360.0

    def _evaluate_offset(self, offset_deg: float, order: int) -> float:
        half_duration = self._lobe.advertised_duration_deg / 2.0
        if abs(offset_deg) > half_duration:
            return 0.0
        for segment in self._segments:
            if segment.contains(offset_deg):
                return float(segment.evaluate(offset_deg, order=order))
        if -self._dwell_half_width_deg <= offset_deg <= self._dwell_half_width_deg:
            return self._lobe.valve_lift_in if order == 0 else 0.0
        return 0.0


def profiles_from_cam_card(
    card: CamCard, *, approximate_derivatives: bool = False
) -> CamCardProfiles:
    """Return source-agnostic intake and exhaust profiles from one cam card.

    The cam-card operator answers velocity, acceleration, and jerk from its
    constrained motion law, stamped as model-derived profile answers rather than
    measured valvetrain data. ``approximate_derivatives`` remains a compatibility
    hook for operators that would otherwise refuse a derivative query; it does not
    upgrade cam-card trust.
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
    operator = PolynomialMotionLawCamCardOperator(lobe, side)
    samples = tuple(operator.evaluate(float(degree)) for degree in range(720))
    model = CanonicalLiftModel(
        samples_720=samples,
        operator=operator,
        provenance=_provenance_for_cam_card_operator(operator),
        approximate_derivatives=approximate_derivatives,
    )
    return CanonicalCamProfile(model)


def _provenance_for_cam_card_operator(operator: PolynomialMotionLawCamCardOperator) -> ProvenanceMap:
    center = operator.centerline_crank_deg
    unsupported_half_width = max(NOSE_UNSUPPORTED_HALF_WIDTH_DEG, operator.dwell_half_width_deg)
    inferred_regions = (
        (
            operator.opening_050_deg - _BOUNDARY_EPSILON_DEG,
            (center - unsupported_half_width) % 720.0,
            Provenance.INFERRED,
        ),
        (
            (center + unsupported_half_width) % 720.0,
            operator.closing_050_deg + _BOUNDARY_EPSILON_DEG,
            Provenance.INFERRED,
        ),
    )
    return ProvenanceMap.from_default_and_regions(Provenance.EXTRAPOLATED, inferred_regions)


def _motion_segments(
    lobe: CamLobeSpec,
    *,
    dwell_half_width_deg: float,
    threshold_velocity_in_per_deg: float,
) -> tuple[_HermiteSegment, ...]:
    half_advertised = lobe.advertised_duration_deg / 2.0
    half_050 = lobe.duration_050_deg / 2.0
    return (
        _HermiteSegment(
            -half_advertised,
            -half_050,
            0.0,
            CHECKING_LIFT_IN,
            0.0,
            threshold_velocity_in_per_deg,
        ),
        _HermiteSegment(
            -half_050,
            -dwell_half_width_deg,
            CHECKING_LIFT_IN,
            lobe.valve_lift_in,
            threshold_velocity_in_per_deg,
            0.0,
        ),
        _HermiteSegment(
            dwell_half_width_deg,
            half_050,
            lobe.valve_lift_in,
            CHECKING_LIFT_IN,
            0.0,
            -threshold_velocity_in_per_deg,
        ),
        _HermiteSegment(
            half_050,
            half_advertised,
            CHECKING_LIFT_IN,
            0.0,
            -threshold_velocity_in_per_deg,
            0.0,
        ),
    )


def _dwell_half_width(lobe: CamLobeSpec) -> float:
    requested = lobe.duration_050_deg * _HIGH_LIFT_DWELL_FRACTION / 2.0
    available = lobe.duration_050_deg / 2.0 - 1.0
    return min(max(requested, _MIN_DWELL_HALF_WIDTH_DEG), _MAX_DWELL_HALF_WIDTH_DEG, available)


def _threshold_velocity(lobe: CamLobeSpec, dwell_half_width_deg: float) -> float:
    ramp_width = (lobe.advertised_duration_deg - lobe.duration_050_deg) / 2.0
    flank_width = lobe.duration_050_deg / 2.0 - dwell_half_width_deg
    ramp_average = CHECKING_LIFT_IN / ramp_width
    flank_average = (lobe.valve_lift_in - CHECKING_LIFT_IN) / flank_width
    return min(1.5 * ramp_average, 1.5 * flank_average)


def _quintic_basis(order: int, u: float) -> tuple[float, float, float, float, float, float]:
    if order == 0:
        return _quintic_position_basis(u)
    if order == 1:
        return _quintic_velocity_basis(u)
    if order == 2:
        return _quintic_acceleration_basis(u)
    if order == 3:
        return _quintic_jerk_basis(u)
    raise ValueError("quintic Hermite basis supports derivative orders 0-3")


def _quintic_position_basis(u: float) -> tuple[float, float, float, float, float, float]:
    u2 = u * u
    u3 = u2 * u
    u4 = u3 * u
    u5 = u4 * u
    return (
        1.0 - 10.0 * u3 + 15.0 * u4 - 6.0 * u5,
        u - 6.0 * u3 + 8.0 * u4 - 3.0 * u5,
        0.5 * u2 - 1.5 * u3 + 1.5 * u4 - 0.5 * u5,
        10.0 * u3 - 15.0 * u4 + 6.0 * u5,
        -4.0 * u3 + 7.0 * u4 - 3.0 * u5,
        0.5 * u3 - u4 + 0.5 * u5,
    )


def _quintic_velocity_basis(u: float) -> tuple[float, float, float, float, float, float]:
    u2 = u * u
    u3 = u2 * u
    u4 = u3 * u
    return (
        -30.0 * u2 + 60.0 * u3 - 30.0 * u4,
        1.0 - 18.0 * u2 + 32.0 * u3 - 15.0 * u4,
        u - 4.5 * u2 + 6.0 * u3 - 2.5 * u4,
        30.0 * u2 - 60.0 * u3 + 30.0 * u4,
        -12.0 * u2 + 28.0 * u3 - 15.0 * u4,
        1.5 * u2 - 4.0 * u3 + 2.5 * u4,
    )


def _quintic_acceleration_basis(u: float) -> tuple[float, float, float, float, float, float]:
    u2 = u * u
    u3 = u2 * u
    return (
        -60.0 * u + 180.0 * u2 - 120.0 * u3,
        -36.0 * u + 96.0 * u2 - 60.0 * u3,
        1.0 - 9.0 * u + 18.0 * u2 - 10.0 * u3,
        60.0 * u - 180.0 * u2 + 120.0 * u3,
        -24.0 * u + 84.0 * u2 - 60.0 * u3,
        3.0 * u - 12.0 * u2 + 10.0 * u3,
    )


def _quintic_jerk_basis(u: float) -> tuple[float, float, float, float, float, float]:
    u2 = u * u
    return (
        -60.0 + 360.0 * u - 360.0 * u2,
        -36.0 + 192.0 * u - 180.0 * u2,
        -9.0 + 36.0 * u - 30.0 * u2,
        60.0 - 360.0 * u + 360.0 * u2,
        -24.0 + 168.0 * u - 180.0 * u2,
        3.0 - 24.0 * u + 30.0 * u2,
    )


def _centerline_crank_deg(lobe: CamLobeSpec, side: CamSide) -> float:
    if side == "intake":
        return lobe.lobe_center_deg % 720.0
    return (-lobe.lobe_center_deg) % 720.0


if TYPE_CHECKING:
    # Static structural-conformance check (#6): mypy errors here if the operator
    # stops satisfying the LiftOperator Protocol.
    def _assert_motion_law_is_a_lift_operator(
        op: PolynomialMotionLawCamCardOperator,
    ) -> LiftOperator:
        return op


__all__ = [
    "CHECKING_LIFT_IN",
    "CamCard",
    "CamCardProfiles",
    "CamLobeSpec",
    "PolynomialMotionLawCamCardOperator",
    "exhaust_profile_from_cam_card",
    "intake_profile_from_cam_card",
    "profiles_from_cam_card",
]
