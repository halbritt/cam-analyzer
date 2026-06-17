"""Canonical CamProfile facade and operator protocol."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol, final, runtime_checkable

from cam_analyzer.profile import AnalysisKind, CamProfile
from cam_analyzer.profile.provenance_map import ProvenanceMap
from cam_analyzer.quantity import Angle, Answer, Crank, ProvFloat, Provenance, Quantity, Refusal

_CYCLE_DEG = 720.0
_SCAN_STEP_DEG = 0.5
_BISECTION_STEPS = 48
_ROOT_TOLERANCE = 1e-9
_DEDUP_TOLERANCE_DEG = 1e-4
# Derivative order each cliff analysis needs the operator to justify everywhere
# (D014's Nyquist gate). PTV closest-approach needs a continuous, velocity-bearing
# curve; spring float is an acceleration phenomenon; jerk is jerk.
_PTV_REQUIRED_DERIVATIVE_ORDER = 1
_SPRING_REQUIRED_DERIVATIVE_ORDER = 2
_JERK_REQUIRED_DERIVATIVE_ORDER = 3
_SCAN_POINTS = tuple(
    point_index * _SCAN_STEP_DEG
    for point_index in range(int(_CYCLE_DEG / _SCAN_STEP_DEG) + 1)
)


@runtime_checkable
class LiftOperator(Protocol):
    """A named lift model. The facade delegates every C5 query here.

    Structural Protocol, ``runtime_checkable`` to match :class:`CamProfile` (#6) —
    concrete operators conform by shape, never by subclassing.
    """

    name: str

    def evaluate(self, crank_deg: float) -> float: ...
    def derivative(self, order: int, crank_deg: float) -> float: ...
    def max_supported_derivative(self, crank_deg: float) -> int: ...


@dataclass(frozen=True, slots=True)
class CanonicalLiftModel:
    """The immutable object backing a profile."""

    samples_720: tuple[float, ...]
    operator: LiftOperator
    provenance: ProvenanceMap
    lift_unit: str = "inch"
    lift_frame: str = "valve_side"
    source: str = "canonical"
    # Opt-in: answer otherwise-refused derivatives with an EXTRAPOLATED ballpark
    # (operator must expose approximate_derivative/max_approximate_derivative).
    approximate_derivatives: bool = False


@final
class CanonicalCamProfile:
    """Generic C5 facade implemented once for every source.

    Satisfies :class:`CamProfile` *structurally*, not by subclassing — see #6 and
    the static conformance assertion at the foot of this module.
    """

    def __init__(self, model: CanonicalLiftModel):
        self._model = model

    @property
    def operator_name(self) -> str:
        return self._model.operator.name

    @property
    def source(self) -> str:
        return self._model.source

    def lift_at(self, angle: Angle[Crank]) -> ProvFloat:
        crank_deg = angle.require_crank()
        provenance = self._model.provenance.at(crank_deg)
        if provenance is Provenance.MEASURED and not self._measured_sample_supports(crank_deg):
            raise ValueError("measured sparse samples cannot answer unsampled crank angles")
        return Quantity._mint(
            self._model.operator.evaluate(crank_deg),
            self._model.lift_unit,
            self._model.lift_frame,
            provenance,
        )

    def velocity_at(self, angle: Angle[Crank]) -> Answer:
        return self._derivative_at(1, angle, "inch_per_deg")

    def acceleration_at(self, angle: Angle[Crank]) -> Answer:
        return self._derivative_at(2, angle, "inch_per_deg2")

    def jerk_at(self, angle: Angle[Crank]) -> Answer:
        return self._derivative_at(3, angle, "inch_per_deg3")

    def events_at_lift(self, lift: ProvFloat) -> list[Angle[Crank]]:
        self._require_lift_compatible(lift)
        target_lift = float(lift)
        if target_lift < 0.0:
            raise ValueError("lift threshold must be non-negative")
        root_degrees = _roots_for_lift(self._model.operator, target_lift)
        return [Angle.crank(crank_deg) for crank_deg in root_degrees]

    def duration_at_lift(self, lift: ProvFloat) -> Angle[Crank]:
        self._require_lift_compatible(lift)
        event_degrees = [event.degrees for event in self.events_at_lift(lift)]
        duration_deg = _duration_above_lift(
            self._model.operator,
            float(lift),
            event_degrees,
        )
        # A duration (not a crank position) — construct without the periodic wrap
        # that Angle.crank() applies, so a full-cycle 720 stays 720.
        return Angle[Crank](duration_deg, "crank")

    def max_lift(self) -> ProvFloat:
        max_lift_deg = max(_SCAN_POINTS[:-1], key=self._model.operator.evaluate)
        return self.lift_at(Angle.crank(max_lift_deg))

    def area_under_curve(self) -> ProvFloat:
        return Quantity._mint(
            _integrate_lift(self._model.operator),
            f"{self._model.lift_unit}_deg",
            self._model.lift_frame,
            self._model.provenance.weakest(),
        )

    def is_good_enough_for(self, kind: AnalysisKind) -> bool:
        if kind in {AnalysisKind.TIMING, AnalysisKind.OVERLAP, AnalysisKind.REPORT}:
            return self._model.provenance.weakest() >= Provenance.INFERRED
        if kind is AnalysisKind.PTV:
            return self._supports_measured_safety(_PTV_REQUIRED_DERIVATIVE_ORDER)
        if kind is AnalysisKind.SPRING_SAFETY:
            return self._supports_measured_safety(_SPRING_REQUIRED_DERIVATIVE_ORDER)
        if kind is AnalysisKind.JERK:
            return self._supports_derivative_everywhere(_JERK_REQUIRED_DERIVATIVE_ORDER)
        return False

    def peak_angle(self) -> Angle[Crank]:
        """Source-blind helper for analyses that need the max-lift centerline."""
        max_lift_deg = max(_SCAN_POINTS[:-1], key=self._model.operator.evaluate)
        return Angle.crank(max_lift_deg)

    def _derivative_at(self, order: int, angle: Angle[Crank], unit: str) -> Answer:
        crank_deg = angle.require_crank()
        derivative_map = self._model.provenance.derivative_map(order)
        max_supported_order = self._model.operator.max_supported_derivative(crank_deg)
        if max_supported_order >= order:
            return Quantity._mint(
                self._model.operator.derivative(order, crank_deg),
                unit,
                self._model.lift_frame,
                derivative_map.at(crank_deg),
            )
        approximate = self._approximate_derivative_at(order, crank_deg, unit)
        if approximate is not None:
            return approximate
        return Refusal(
            requested=f"derivative order {order} at {crank_deg:.3f} deg",
            reason=(
                f"{self._model.operator.name} supports derivative order "
                f"{max_supported_order} at this crank angle, not order {order}"
            ),
            remedy="provide backing lift data with support for this derivative order",
            provenance=derivative_map.at(crank_deg),
        )

    def _approximate_derivative_at(
        self, order: int, crank_deg: float, unit: str
    ) -> ProvFloat | None:
        """Opt-in ballpark for an unsupported derivative, always EXTRAPOLATED.

        Returns ``None`` (caller then refuses) unless the model was built with
        ``approximate_derivatives=True`` and the operator can analytically
        approximate this order here. The value is stamped EXTRAPOLATED — it
        describes the operator's *assumed* shape, not the cam — so it never
        elevates derivative support: the cliff-analysis fitness gates
        (``is_good_enough_for``/``_supports_*``) read ``max_supported_derivative``
        and stay strict.
        """
        if not self._model.approximate_derivatives:
            return None
        max_approximate = getattr(self._model.operator, "max_approximate_derivative", None)
        approximate_derivative = getattr(self._model.operator, "approximate_derivative", None)
        if max_approximate is None or approximate_derivative is None:
            return None
        if max_approximate(crank_deg) < order:
            return None
        return Quantity._mint(
            approximate_derivative(order, crank_deg),
            unit,
            self._model.lift_frame,
            Provenance.EXTRAPOLATED,
        )

    def _measured_sample_supports(self, crank_deg: float) -> bool:
        if len(self._model.samples_720) >= int(_CYCLE_DEG):
            return True
        if not self._model.samples_720:
            return False
        sample_step_deg = _CYCLE_DEG / len(self._model.samples_720)
        nearest_sample = round(crank_deg / sample_step_deg) * sample_step_deg
        return abs(nearest_sample - crank_deg) <= _DEDUP_TOLERANCE_DEG

    def _require_lift_compatible(self, lift: ProvFloat) -> None:
        if lift.unit != self._model.lift_unit or lift.frame != self._model.lift_frame:
            raise ValueError(
                f"lift threshold must be {self._model.lift_unit}/{self._model.lift_frame}, "
                f"got {lift.unit}/{lift.frame}"
            )

    def _supports_measured_safety(self, derivative_order: int) -> bool:
        """Gate cliff verdicts (PTV, spring) behind measured, well-sampled curves.

        Cam-card approximations stay blocked: their lift provenance is never
        MEASURED and their operator surrenders derivative support at the nose and
        seat. A real measured profile whose operator justifies the required
        derivative order everywhere (D014) may carry a measured-clearance verdict.
        Unlike :meth:`_supports_derivative_everywhere`, this does not apply the
        derivative-map provenance ceiling: that ceiling governs what a returned
        derivative *value* may claim, not whether the curve is trustworthy enough
        to attach an externally measured clearance comparison.
        """
        return (
            self._model.provenance.weakest() is Provenance.MEASURED
            and self._operator_supports_derivative_everywhere(derivative_order)
        )

    def _operator_supports_derivative_everywhere(self, order: int) -> bool:
        return all(
            self._model.operator.max_supported_derivative(crank_deg) >= order
            for crank_deg in _SCAN_POINTS[:-1]
        )

    def _supports_derivative_everywhere(self, order: int) -> bool:
        return (
            self._operator_supports_derivative_everywhere(order)
            and self._model.provenance.derivative_map(order).weakest() >= Provenance.INFERRED
        )


def _roots_for_lift(operator: LiftOperator, target_lift: float) -> list[float]:
    deltas = [_lift_delta(operator, target_lift, crank_deg) for crank_deg in _SCAN_POINTS]
    roots = _exact_roots(deltas)
    roots.extend(_crossing_roots(operator, target_lift, deltas))
    return _dedupe_periodic(roots)


def _exact_roots(deltas: list[float]) -> list[float]:
    roots: list[float] = []
    for point_index, delta in enumerate(deltas[:-1]):
        previous_delta = deltas[point_index - 1 if point_index > 0 else -2]
        next_delta = deltas[point_index + 1]
        if _is_isolated_root(previous_delta, delta, next_delta):
            roots.append(_SCAN_POINTS[point_index])
    return roots


def _crossing_roots(
    operator: LiftOperator,
    target_lift: float,
    deltas: list[float],
) -> list[float]:
    roots: list[float] = []
    for point_index, left_delta in enumerate(deltas[:-1]):
        right_delta = deltas[point_index + 1]
        if left_delta * right_delta < 0.0:
            roots.append(
                _bisect_crossing(
                    operator,
                    target_lift,
                    _SCAN_POINTS[point_index],
                    _SCAN_POINTS[point_index + 1],
                )
            )
    return roots


def _bisect_crossing(
    operator: LiftOperator,
    target_lift: float,
    lower_deg: float,
    upper_deg: float,
) -> float:
    lower_delta = _lift_delta(operator, target_lift, lower_deg)
    for _ in range(_BISECTION_STEPS):
        midpoint_deg = (lower_deg + upper_deg) / 2.0
        midpoint_delta = _lift_delta(operator, target_lift, midpoint_deg)
        if abs(midpoint_delta) <= _ROOT_TOLERANCE:
            return midpoint_deg
        if lower_delta * midpoint_delta <= 0.0:
            upper_deg = midpoint_deg
        else:
            lower_deg = midpoint_deg
            lower_delta = midpoint_delta
    return (lower_deg + upper_deg) / 2.0


def _duration_above_lift(
    operator: LiftOperator,
    target_lift: float,
    event_degrees: list[float],
) -> float:
    if not event_degrees:
        return _CYCLE_DEG if _is_above_lift(operator.evaluate(0.0), target_lift) else 0.0
    boundaries = [0.0, *_dedupe_periodic(event_degrees), _CYCLE_DEG]
    duration_deg = 0.0
    for lower_deg, upper_deg in zip(boundaries, boundaries[1:]):
        span_deg = upper_deg - lower_deg
        if span_deg <= _DEDUP_TOLERANCE_DEG:
            continue
        midpoint_deg = lower_deg + span_deg / 2.0
        if _is_above_lift(operator.evaluate(midpoint_deg), target_lift):
            duration_deg += span_deg
    return duration_deg


def _integrate_lift(operator: LiftOperator) -> float:
    area = 0.0
    previous_lift = operator.evaluate(0.0)
    for crank_deg in _SCAN_POINTS[1:]:
        current_lift = operator.evaluate(crank_deg)
        area += (previous_lift + current_lift) * _SCAN_STEP_DEG / 2.0
        previous_lift = current_lift
    return area


def _lift_delta(operator: LiftOperator, target_lift: float, crank_deg: float) -> float:
    return operator.evaluate(crank_deg) - target_lift


def _is_above_lift(sample_lift: float, target_lift: float) -> bool:
    if target_lift <= _ROOT_TOLERANCE:
        return sample_lift > _ROOT_TOLERANCE
    return sample_lift >= target_lift


def _is_isolated_root(
    previous_delta: float,
    current_delta: float,
    next_delta: float,
) -> bool:
    return (
        abs(current_delta) <= _ROOT_TOLERANCE
        and not (
            abs(previous_delta) <= _ROOT_TOLERANCE
            and abs(next_delta) <= _ROOT_TOLERANCE
        )
    )


def _dedupe_periodic(roots: list[float]) -> list[float]:
    unique_roots: list[float] = []
    for root_deg in sorted(root % _CYCLE_DEG for root in roots):
        if not unique_roots or _periodic_distance(root_deg, unique_roots[-1]) > _DEDUP_TOLERANCE_DEG:
            unique_roots.append(root_deg)
    if len(unique_roots) > 1 and _periodic_distance(unique_roots[0], unique_roots[-1]) <= _DEDUP_TOLERANCE_DEG:
        unique_roots.pop()
    return unique_roots


def _periodic_distance(left_deg: float, right_deg: float) -> float:
    distance = abs((left_deg - right_deg) % _CYCLE_DEG)
    return min(distance, _CYCLE_DEG - distance)


if TYPE_CHECKING:
    # Static structural-conformance check (#6): mypy errors here if the facade
    # ever stops satisfying the CamProfile Protocol. This replaces the misleading
    # nominal `class CanonicalCamProfile(CamProfile)`, where an omitted method
    # would have inherited a `...` body and failed only at call time.
    def _assert_canonical_is_a_camprofile(profile: CanonicalCamProfile) -> CamProfile:
        return profile
