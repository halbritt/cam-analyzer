from __future__ import annotations

import math

from cam_analyzer.analysis.timing import (
    basic_timing_map,
    centerline,
    lobe_separation_angle,
    overlap_at_lift,
)
from cam_analyzer.profile import AnalysisKind
from cam_analyzer.quantity import (
    Angle,
    Inch,
    InchDeg,
    InchPerDeg,
    InchPerDeg2,
    InchPerDeg3,
    Quantity,
    extrapolated,
    inferred,
)


class WindowProfile:
    def __init__(self, *, open_deg: float, close_deg: float, peak_deg: float, peak_lift: float) -> None:
        self._open_deg = open_deg % 720.0
        self._close_deg = close_deg % 720.0
        self._peak_deg = peak_deg % 720.0
        self._peak_lift = peak_lift

    def lift_at(self, angle: Angle) -> Quantity:
        degrees = angle.degrees % 720.0
        if not self._is_open(degrees):
            lift = 0.0
        else:
            lift = self._peak_lift * max(0.0, math.cos(math.radians(degrees - self._peak_deg)))
        return inferred(lift, Inch, "valve_side")

    def velocity_at(self, angle: Angle) -> Quantity:
        return extrapolated(0.0, InchPerDeg, "valve_side")

    def acceleration_at(self, angle: Angle) -> Quantity:
        return extrapolated(0.0, InchPerDeg2, "valve_side")

    def jerk_at(self, angle: Angle) -> Quantity:
        return extrapolated(0.0, InchPerDeg3, "valve_side")

    def events_at_lift(self, lift: Quantity) -> list[Angle]:
        if float(lift) >= self._peak_lift:
            return [Angle.crank(self._peak_deg)]
        return [Angle.crank(self._open_deg), Angle.crank(self._close_deg)]

    def duration_at_lift(self, lift: Quantity) -> Angle:
        if self._close_deg >= self._open_deg:
            return Angle.crank(self._close_deg - self._open_deg)
        return Angle.crank(720.0 - self._open_deg + self._close_deg)

    def max_lift(self) -> Quantity:
        return inferred(self._peak_lift, Inch, "valve_side")

    def area_under_curve(self) -> Quantity:
        return inferred(42.0, InchDeg, "valve_side")

    def is_good_enough_for(self, kind: AnalysisKind) -> bool:
        return kind in {AnalysisKind.TIMING, AnalysisKind.OVERLAP, AnalysisKind.REPORT}

    def _is_open(self, degrees: float) -> bool:
        if self._open_deg <= self._close_deg:
            return self._open_deg <= degrees <= self._close_deg
        return degrees >= self._open_deg or degrees <= self._close_deg


def test_centerline_uses_profile_boundary_events() -> None:
    intake = WindowProfile(open_deg=710.5, close_deg=228.5, peak_deg=109.5, peak_lift=0.360)

    assert centerline(intake) == Angle.crank(109.5)


def test_lobe_separation_angle_uses_absolute_profile_centerlines() -> None:
    intake = WindowProfile(open_deg=710.5, close_deg=228.5, peak_deg=109.5, peak_lift=0.360)
    exhaust = WindowProfile(open_deg=492.5, close_deg=18.5, peak_deg=615.5, peak_lift=0.360)

    assert lobe_separation_angle(intake, exhaust) == Angle.crank(107.0)


def test_overlap_at_lift_intersects_wrapping_open_windows() -> None:
    intake = WindowProfile(open_deg=710.5, close_deg=228.5, peak_deg=109.5, peak_lift=0.360)
    exhaust = WindowProfile(open_deg=492.5, close_deg=18.5, peak_deg=615.5, peak_lift=0.360)
    lift = inferred(0.050, Inch, "valve_side")

    assert overlap_at_lift(intake, exhaust, lift) == Angle.crank(28.0)


def test_basic_timing_map_contains_centerlines_lsa_overlap_and_events() -> None:
    intake = WindowProfile(open_deg=710.5, close_deg=228.5, peak_deg=109.5, peak_lift=0.360)
    exhaust = WindowProfile(open_deg=492.5, close_deg=18.5, peak_deg=615.5, peak_lift=0.360)
    lift = inferred(0.050, Inch, "valve_side")

    timing_map = basic_timing_map(intake, exhaust, (lift,))

    assert timing_map.intake_centerline == Angle.crank(109.5)
    assert timing_map.exhaust_centerline == Angle.crank(615.5)
    assert timing_map.lobe_separation_angle == Angle.crank(107.0)
    assert timing_map.overlap_by_lift[0.050] == Angle.crank(28.0)
    assert timing_map.intake_events_by_lift[0.050] == (Angle.crank(710.5), Angle.crank(228.5))
