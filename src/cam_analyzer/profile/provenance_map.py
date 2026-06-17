"""Per-crank-region provenance maps for profile queries."""

from __future__ import annotations

import bisect
from dataclasses import dataclass
from typing import Iterable

from cam_analyzer.quantity import Provenance


@dataclass(frozen=True, slots=True)
class _Interval:
    start_deg: float
    provenance: Provenance


class ProvenanceMap:
    """Maps crank regions to provenance over the periodic [0, 720) cycle."""

    def __init__(self, intervals: Iterable[tuple[float, Provenance]]):
        ordered = [(start % 720.0, provenance) for start, provenance in intervals]
        if not ordered:
            raise ValueError("provenance map requires at least one interval")
        ordered.sort(key=lambda item: item[0])
        if ordered[0][0] != 0.0:
            raise ValueError("provenance map must start at crank angle 0")
        starts = [start for start, _ in ordered]
        if len(set(starts)) != len(starts):
            raise ValueError("interval starts must be unique")
        self._starts = starts
        self._intervals = [_Interval(start, provenance) for start, provenance in ordered]

    @classmethod
    def constant(cls, provenance: Provenance) -> "ProvenanceMap":
        return cls([(0.0, provenance)])

    @classmethod
    def from_default_and_regions(
        cls,
        default: Provenance,
        regions: Iterable[tuple[float, float, Provenance]],
    ) -> "ProvenanceMap":
        """Build a map from default provenance plus possibly wrapping regions.

        Regions are half-open arcs ``[start, end)`` in crank degrees. Later
        regions override earlier ones; this is intentionally small and explicit
        because Milestone 1 only needs a few cam-card support intervals.
        """
        breakpoints: set[float] = {0.0}
        normalized: list[tuple[float, float, Provenance]] = []
        for start, end, provenance in regions:
            start = start % 720.0
            end = end % 720.0
            if start == end:
                normalized.append((0.0, 720.0, provenance))
                breakpoints.update({0.0})
            elif start < end:
                normalized.append((start, end, provenance))
                breakpoints.update({start, end})
            else:
                normalized.append((start, 720.0, provenance))
                normalized.append((0.0, end, provenance))
                breakpoints.update({0.0, start, end})

        intervals: list[tuple[float, Provenance]] = []
        for start in sorted(breakpoints):
            if start >= 720.0:
                continue
            probe = (start + 1e-7) % 720.0
            provenance = default
            for region_start, region_end, region_provenance in normalized:
                if region_start <= probe < region_end:
                    provenance = region_provenance
            if not intervals or intervals[-1][1] != provenance:
                intervals.append((start, provenance))
        if intervals[0][0] != 0.0:
            intervals.insert(0, (0.0, default))
        return cls(intervals)

    def at(self, crank_deg: float) -> Provenance:
        angle = crank_deg % 720.0
        index = bisect.bisect_right(self._starts, angle) - 1
        return self._intervals[index].provenance

    def derivative_map(self, order: int) -> "ProvenanceMap":
        """Return a conservative derivative provenance map.

        Differentiation cannot improve evidence. First derivatives keep inferred
        regions inferred at best; higher derivatives are extrapolated unless a
        concrete operator says it has support through its capability gate.
        """
        if order < 0:
            raise ValueError("derivative order must be non-negative")
        if order == 0:
            return self
        ceiling = Provenance.INFERRED if order == 1 else Provenance.EXTRAPOLATED
        return ProvenanceMap(
            (interval.start_deg, Provenance.join(interval.provenance, ceiling))
            for interval in self._intervals
        )

    def weakest(self) -> Provenance:
        return Provenance.join(*(interval.provenance for interval in self._intervals))

    def intervals(self) -> tuple[tuple[float, Provenance], ...]:
        return tuple((interval.start_deg, interval.provenance) for interval in self._intervals)
