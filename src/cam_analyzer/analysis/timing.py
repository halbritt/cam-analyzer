"""Timing analysis — centerlines, LSA, overlap, the 720° map.

Consumes only the CamProfile boundary. Imports nothing from cam_analyzer.sources.
"""

from __future__ import annotations

from cam_analyzer.profile import AnalysisKind, CamProfile
from cam_analyzer.quantity import Angle, Quantity


def overlap_at_lift(intake: CamProfile, exhaust: CamProfile, lift: Quantity) -> Angle:
    """Crank degrees where both valves exceed ``lift``.

    Source-blind: works identically for a cam-card approximation and a measured
    profile (C4). Whether the answer is trustworthy is told by each Quantity's
    provenance, not by knowing where the profile came from.
    """
    raise NotImplementedError("intersect events_at_lift(intake) and events_at_lift(exhaust)")


def lobe_separation_angle(intake: CamProfile, exhaust: CamProfile) -> Angle:
    raise NotImplementedError("from each profile's max-lift centerline")
