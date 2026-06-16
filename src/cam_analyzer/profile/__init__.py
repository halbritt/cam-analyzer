"""The CamProfile boundary — the only language analyses speak (C5).

``CamProfile`` is a Protocol describing the eight-query surface. Concrete profiles
are ``@final`` facades over one ``CanonicalLiftModel`` (see canonical.py / Pillar
B): they do not implement these methods by hand — the methods are *generated*
projections of one named operator, so inconsistent derivatives are unconstructable.
"""

from __future__ import annotations

from enum import Enum
from typing import Protocol, runtime_checkable

from cam_analyzer.quantity import Angle, Quantity


class AnalysisKind(Enum):
    """What a fitness check (``is_good_enough_for``) is asked about."""

    TIMING = "timing"
    OVERLAP = "overlap"
    DCR = "dcr"
    PTV = "ptv"
    SPRING_SAFETY = "spring_safety"
    JERK = "jerk"
    SENSITIVITY = "sensitivity"
    REPORT = "report"


@runtime_checkable
class CamProfile(Protocol):
    """The continuous-query surface. Every return is a Quantity/Angle, never a float."""

    def lift_at(self, angle: Angle) -> Quantity: ...
    def velocity_at(self, angle: Angle) -> Quantity: ...
    def acceleration_at(self, angle: Angle) -> Quantity: ...
    def jerk_at(self, angle: Angle) -> Quantity: ...
    def events_at_lift(self, lift: Quantity) -> list[Angle]: ...
    def duration_at_lift(self, lift: Quantity) -> Angle: ...
    def max_lift(self) -> Quantity: ...
    def area_under_curve(self) -> Quantity: ...

    def is_good_enough_for(self, kind: AnalysisKind) -> bool:
        """Can this profile answer *kind* with adequate provenance (G5/D006)?"""
        ...


__all__ = ["CamProfile", "AnalysisKind"]
