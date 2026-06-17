"""Source-blind timing analysis."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from cam_analyzer.profile import CamProfile
from cam_analyzer.quantity import Angle, ProvFloat, Provenance


@dataclass(frozen=True, slots=True)
class TimingEvents:
    open_deg: float
    close_deg: float
    duration_deg: float


@dataclass(frozen=True, slots=True)
class TimingMap:
    intake_centerline: Angle
    exhaust_centerline: Angle
    lobe_separation: Angle
    intake_events: TimingEvents
    exhaust_events: TimingEvents


@dataclass(frozen=True, slots=True)
class BasicTimingMap:
    intake_centerline: Angle
    exhaust_centerline: Angle
    lobe_separation_angle: Angle
    intake_events_by_lift: dict[float, tuple[Angle, ...]]
    exhaust_events_by_lift: dict[float, tuple[Angle, ...]]
    intake_duration_by_lift: dict[float, Angle]
    exhaust_duration_by_lift: dict[float, Angle]
    overlap_by_lift: dict[float, Angle]


def centerline(profile: CamProfile) -> Angle:
    """Find max-lift centerline using only the C5 query surface."""
    peak_events = profile.events_at_lift(profile.max_lift())
    if peak_events:
        return _circular_mean(peak_events)

    best_angle = 0.0
    best_lift = float(profile.lift_at(Angle.crank(0.0)))
    step = 0.5
    for index in range(1, int(720.0 / step)):
        angle = index * step
        lift = float(profile.lift_at(Angle.crank(angle)))
        if lift > best_lift:
            best_lift = lift
            best_angle = angle

    lo = best_angle - step
    hi = best_angle + step
    for _ in range(40):
        left = lo + (hi - lo) / 3.0
        right = hi - (hi - lo) / 3.0
        if float(profile.lift_at(Angle.crank(left))) < float(profile.lift_at(Angle.crank(right))):
            lo = left
        else:
            hi = right
    return Angle.crank((lo + hi) / 2.0)


def lobe_separation_angle(intake: CamProfile, exhaust: CamProfile) -> Angle:
    """Return the conventional lobe separation angle from source-blind peaks."""
    intake_center = centerline(intake).degrees
    exhaust_center = centerline(exhaust).degrees
    separation_across_tdc = (intake_center - exhaust_center) % 720.0
    if separation_across_tdc > 360.0:
        separation_across_tdc = 720.0 - separation_across_tdc
    return Angle.crank(separation_across_tdc / 2.0)


def overlap_at_lift(intake: CamProfile, exhaust: CamProfile, lift: ProvFloat) -> Angle:
    """Crank degrees around overlap TDC where both valves exceed ``lift``."""
    total = 0.0
    for intake_start, intake_end in _open_intervals_at_lift(intake, lift):
        for exhaust_start, exhaust_end in _open_intervals_at_lift(exhaust, lift):
            start = max(intake_start, exhaust_start)
            end = min(intake_end, exhaust_end)
            if end > start:
                total += end - start
    return Angle.crank(total)


def events_for_profile(profile: CamProfile, lift: ProvFloat) -> TimingEvents:
    events = profile.events_at_lift(lift)
    if len(events) < 2:
        return TimingEvents(0.0, 0.0, 0.0)
    duration = profile.duration_at_lift(lift).degrees
    first = events[0].degrees
    second = events[1].degrees
    arc = (second - first) % 720.0
    midpoint = (first + arc / 2.0) % 720.0
    if float(profile.lift_at(Angle.crank(midpoint))) >= float(lift):
        open_deg = first
        close_deg = second
    else:
        open_deg = second
        close_deg = first
    return TimingEvents(open_deg=open_deg, close_deg=close_deg, duration_deg=duration)


def timing_map(
    intake: CamProfile,
    exhaust: CamProfile,
    lift: ProvFloat | None = None,
) -> TimingMap:
    threshold = lift or ProvFloat(0.050, "inch", "valve_side", Provenance.INFERRED)
    return TimingMap(
        intake_centerline=centerline(intake),
        exhaust_centerline=centerline(exhaust),
        lobe_separation=lobe_separation_angle(intake, exhaust),
        intake_events=events_for_profile(intake, threshold),
        exhaust_events=events_for_profile(exhaust, threshold),
    )


def basic_timing_map(
    intake: CamProfile,
    exhaust: CamProfile,
    lifts: Iterable[ProvFloat],
) -> BasicTimingMap:
    intake_events: dict[float, tuple[Angle, ...]] = {}
    exhaust_events: dict[float, tuple[Angle, ...]] = {}
    intake_durations: dict[float, Angle] = {}
    exhaust_durations: dict[float, Angle] = {}
    overlaps: dict[float, Angle] = {}

    for lift in lifts:
        key = float(lift)
        intake_events[key] = tuple(intake.events_at_lift(lift))
        exhaust_events[key] = tuple(exhaust.events_at_lift(lift))
        intake_durations[key] = intake.duration_at_lift(lift)
        exhaust_durations[key] = exhaust.duration_at_lift(lift)
        overlaps[key] = overlap_at_lift(intake, exhaust, lift)

    return BasicTimingMap(
        intake_centerline=centerline(intake),
        exhaust_centerline=centerline(exhaust),
        lobe_separation_angle=lobe_separation_angle(intake, exhaust),
        intake_events_by_lift=intake_events,
        exhaust_events_by_lift=exhaust_events,
        intake_duration_by_lift=intake_durations,
        exhaust_duration_by_lift=exhaust_durations,
        overlap_by_lift=overlaps,
    )


def _open_intervals_at_lift(profile: CamProfile, lift: ProvFloat) -> list[tuple[float, float]]:
    events = sorted({event.degrees % 720.0 for event in profile.events_at_lift(lift)})
    if not events:
        return []

    intervals: list[tuple[float, float]] = []
    for index, start in enumerate(events):
        end = events[(index + 1) % len(events)]
        segment_end = end if end > start else end + 720.0
        if segment_end == start:
            continue
        midpoint = start + (segment_end - start) / 2.0
        if float(profile.lift_at(Angle.crank(midpoint))) >= float(lift):
            intervals.extend(_split_interval(start, segment_end))
    return intervals


def _split_interval(start: float, end: float) -> list[tuple[float, float]]:
    if end <= 720.0:
        return [(start, end)]
    return [(start, 720.0), (0.0, end - 720.0)]


def _circular_mean(angles: Iterable[Angle]) -> Angle:
    degrees = [angle.degrees % 720.0 for angle in angles]
    if not degrees:
        return Angle.crank(0.0)
    reference = degrees[0]
    unwrapped = [reference]
    for degree in degrees[1:]:
        delta = ((degree - reference + 360.0) % 720.0) - 360.0
        unwrapped.append(reference + delta)
    return Angle.crank(sum(unwrapped) / len(unwrapped))
