"""Per-region fitness (Pillar C / D006).

Provenance is not a property of the profile; it is a property of *each query at
each crank region*. A ``ProvenanceMap`` answers "how trustworthy is the value at
this angle?" in O(log N) via bisect over half-open intervals.

The interval lookup is implemented; the Nyquist derivative-downgrade and the
``is_good_enough_for`` fitness policy are stubs naming the invariant they uphold.
"""

from __future__ import annotations

import bisect
from dataclasses import dataclass

from cam_analyzer.quantity import Provenance


@dataclass(frozen=True, slots=True)
class _Interval:
    start_deg: float  # inclusive
    provenance: Provenance


class ProvenanceMap:
    """Maps a crank region to its provenance.

    Built from sorted, contiguous half-open intervals over [0, 720). Example::

        ProvenanceMap([(0, MEASURED), (15, EXTRAPOLATED), (345, MEASURED)])

    means [0,15)=MEASURED, [15,345)=EXTRAPOLATED, [345,720)=MEASURED.
    """

    def __init__(self, intervals: list[tuple[float, Provenance]]):
        if not intervals or intervals[0][0] != 0:
            raise ValueError("provenance map must start at crank angle 0")
        starts = [s for s, _ in intervals]
        if starts != sorted(starts) or len(set(starts)) != len(starts):
            raise ValueError("intervals must have strictly increasing start angles")
        self._starts = starts
        self._intervals = [_Interval(s, p) for s, p in intervals]

    def at(self, crank_deg: float) -> Provenance:
        """Provenance covering ``crank_deg`` (periodic over 720°)."""
        a = crank_deg % 720.0
        i = bisect.bisect_right(self._starts, a) - 1
        return self._intervals[i].provenance

    def derivative_map(self, order: int) -> "ProvenanceMap":
        """Provenance for the n-th derivative.

        Invariant (D006): differentiation can only *lower* provenance, and must
        downgrade to EXTRAPOLATED where sampling density cannot support the n-th
        derivative (Nyquist). A half-sine cam-card backing cannot honestly report
        MEASURED jerk anywhere.
        """
        raise NotImplementedError(
            "Nyquist-aware derivative provenance downgrade — see D006 / Pillar C"
        )
