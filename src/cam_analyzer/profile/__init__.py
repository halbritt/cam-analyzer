"""The CamProfile boundary: the only language analyses speak."""

from __future__ import annotations

from enum import Enum
from typing import Protocol, runtime_checkable

from cam_analyzer.quantity import Angle, Answer, ProvFloat, Refusal


class AnalysisKind(Enum):
    """What a profile fitness check is asked about."""

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
    """The continuous-query surface. Values are stamped or formally refused."""

    def lift_at(self, angle: Angle) -> ProvFloat: ...
    def velocity_at(self, angle: Angle) -> Answer: ...
    def acceleration_at(self, angle: Angle) -> Answer: ...
    def jerk_at(self, angle: Angle) -> Answer: ...
    def events_at_lift(self, lift: ProvFloat) -> list[Angle]: ...
    def duration_at_lift(self, lift: ProvFloat) -> Angle: ...
    def max_lift(self) -> ProvFloat: ...
    def area_under_curve(self) -> ProvFloat: ...

    def is_good_enough_for(self, kind: AnalysisKind) -> bool:
        """Can this profile answer ``kind`` without unsupported evidence?"""
        ...


__all__ = ["AnalysisKind", "Answer", "CamProfile", "ProvFloat", "Refusal"]
