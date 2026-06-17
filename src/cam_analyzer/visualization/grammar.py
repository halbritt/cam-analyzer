"""Provenance Rendering Grammar primitives from RFC 0004."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Final, Iterable, Literal, Mapping, Sequence, TypeAlias

from cam_analyzer.profile.provenance_map import ProvenanceMap
from cam_analyzer.quantity import Provenance, Refusal

Stroke: TypeAlias = Literal["solid", "short-dash", "long-dash", "none"]
Marker: TypeAlias = Literal["filled", "half-filled", "hollow", "none"]
BandFill: TypeAlias = Literal["none", "light", "hatched", "cross-hatch"]

_CYCLE_DEG: Final = 720.0
_ADJACENT_TOLERANCE: Final = 1e-9


class RenderingTag(Enum):
    """Rendering-only tags that are not value provenance."""

    UNDECIDABLE = "UNDECIDABLE"


SegmentTag: TypeAlias = Provenance | RenderingTag


@dataclass(frozen=True, slots=True)
class ProvenanceStyle:
    """Redundant visual encoding for one provenance class."""

    stroke: Stroke
    opacity: float
    marker: Marker
    band_fill: BandFill
    draw_line: bool
    label: str | None = None

    def to_json(self) -> dict[str, object]:
        """Return the renderer-neutral JSON shape for this style."""
        return {
            "stroke": self.stroke,
            "opacity": self.opacity,
            "marker": self.marker,
            "band_fill": self.band_fill,
            "draw_line": self.draw_line,
            "label": self.label,
        }


_STYLE_TABLE: Final[dict[SegmentTag, ProvenanceStyle]] = {
    Provenance.MEASURED: ProvenanceStyle(
        stroke="solid",
        opacity=1.0,
        marker="filled",
        band_fill="none",
        draw_line=True,
    ),
    Provenance.INFERRED: ProvenanceStyle(
        stroke="short-dash",
        opacity=0.70,
        marker="half-filled",
        band_fill="light",
        draw_line=True,
    ),
    Provenance.EXTRAPOLATED: ProvenanceStyle(
        stroke="long-dash",
        opacity=0.45,
        marker="hollow",
        band_fill="hatched",
        draw_line=True,
    ),
    RenderingTag.UNDECIDABLE: ProvenanceStyle(
        stroke="none",
        opacity=0.0,
        marker="none",
        band_fill="cross-hatch",
        draw_line=False,
        label="tool refuses to assert here",
    ),
}

STYLE_TABLE: Final[Mapping[SegmentTag, ProvenanceStyle]] = MappingProxyType(_STYLE_TABLE)


def style_legend_for_json() -> dict[str, dict[str, object]]:
    """Serialize the single provenance-to-ink table for projection exports."""
    return {
        _legend_key(tag): style.to_json()
        for tag, style in STYLE_TABLE.items()
    }


@dataclass(frozen=True, slots=True)
class SeriesSample:
    """One point from a profile projection before renderer-specific formatting."""

    x_deg: float
    y: float | None
    band_halfwidth: float | None = None
    refusal: Refusal | None = None

    def __post_init__(self) -> None:
        if self.band_halfwidth is not None and self.band_halfwidth < 0.0:
            raise ValueError("band_halfwidth must be non-negative")

    @property
    def is_refused(self) -> bool:
        return self.y is None or self.refusal is not None


@dataclass(frozen=True, slots=True)
class StyledSample:
    """A renderable point in a styled segment."""

    x_deg: float
    y: float


@dataclass(frozen=True, slots=True)
class StyledSegment:
    """Renderer-agnostic IR consumed by chart adapters."""

    tag: SegmentTag
    style: ProvenanceStyle
    x_range: tuple[float, float]
    y_samples: tuple[StyledSample, ...]
    band_halfwidth: float | None
    is_undecidable: bool


def split_series(
    samples: Sequence[SeriesSample],
    provenance_map: ProvenanceMap,
    *,
    min_arc_width_deg: float = 0.0,
    max_segments: int | None = None,
) -> tuple[StyledSegment, ...]:
    """Split a sampled curve into contiguous provenance-styled segments.

    Refused samples are hard breaks: the affected span becomes an
    ``UNDECIDABLE`` no-line segment, so a renderer cannot connect valid points
    across missing evidence.
    """

    _validate_split_request(samples, min_arc_width_deg, max_segments)
    segments: list[StyledSegment] = []
    for left_sample, right_sample in zip(samples, samples[1:]):
        if left_sample.is_refused or right_sample.is_refused:
            segments.append(_refusal_segment(left_sample, right_sample))
        else:
            segments.extend(_provenance_segments(left_sample, right_sample, provenance_map))
    same_tag_coalesced = _coalesce_same_tag(segments)
    return _coalesce_for_legibility(same_tag_coalesced, min_arc_width_deg, max_segments)


def _validate_split_request(
    samples: Sequence[SeriesSample],
    min_arc_width_deg: float,
    max_segments: int | None,
) -> None:
    if len(samples) < 2:
        raise ValueError("split_series requires at least two samples")
    if min_arc_width_deg < 0.0:
        raise ValueError("min_arc_width_deg must be non-negative")
    if max_segments is not None and max_segments < 1:
        raise ValueError("max_segments must be positive")
    previous_x = samples[0].x_deg
    if not 0.0 <= previous_x <= _CYCLE_DEG:
        raise ValueError("sample x_deg values must be in the [0, 720] crank cycle")
    for sample in samples[1:]:
        if not 0.0 <= sample.x_deg <= _CYCLE_DEG:
            raise ValueError("sample x_deg values must be in the [0, 720] crank cycle")
        if sample.x_deg <= previous_x:
            raise ValueError("samples must be sorted by strictly increasing x_deg")
        previous_x = sample.x_deg


def _provenance_segments(
    left_sample: SeriesSample,
    right_sample: SeriesSample,
    provenance_map: ProvenanceMap,
) -> tuple[StyledSegment, ...]:
    boundaries = _boundaries_between(left_sample.x_deg, right_sample.x_deg, provenance_map)
    segment_edges = (left_sample.x_deg, *boundaries, right_sample.x_deg)
    segments = []
    for start_deg, end_deg in zip(segment_edges, segment_edges[1:]):
        if end_deg - start_deg <= _ADJACENT_TOLERANCE:
            continue
        midpoint_deg = (start_deg + end_deg) / 2.0
        tag = provenance_map.at(midpoint_deg)
        start_point, start_band = _interpolate_sample(left_sample, right_sample, start_deg)
        end_point, end_band = _interpolate_sample(left_sample, right_sample, end_deg)
        segments.append(
            StyledSegment(
                tag=tag,
                style=STYLE_TABLE[tag],
                x_range=(start_deg, end_deg),
                y_samples=(start_point, end_point),
                band_halfwidth=_max_band(start_band, end_band),
                is_undecidable=False,
            )
        )
    return tuple(segments)


def _boundaries_between(
    left_deg: float,
    right_deg: float,
    provenance_map: ProvenanceMap,
) -> tuple[float, ...]:
    return tuple(
        start_deg
        for start_deg, _ in provenance_map.intervals()
        if left_deg + _ADJACENT_TOLERANCE < start_deg < right_deg - _ADJACENT_TOLERANCE
    )


def _interpolate_sample(
    left_sample: SeriesSample,
    right_sample: SeriesSample,
    x_deg: float,
) -> tuple[StyledSample, float | None]:
    if left_sample.y is None or right_sample.y is None:
        raise ValueError("cannot interpolate across a refused sample")
    span_deg = right_sample.x_deg - left_sample.x_deg
    fraction = (x_deg - left_sample.x_deg) / span_deg
    y = left_sample.y + (right_sample.y - left_sample.y) * fraction
    return StyledSample(x_deg=x_deg, y=y), _interpolate_band(left_sample, right_sample, fraction)


def _interpolate_band(
    left_sample: SeriesSample,
    right_sample: SeriesSample,
    fraction: float,
) -> float | None:
    left_band = left_sample.band_halfwidth
    right_band = right_sample.band_halfwidth
    if left_band is None:
        return right_band
    if right_band is None:
        return left_band
    return left_band + (right_band - left_band) * fraction


def _refusal_segment(left_sample: SeriesSample, right_sample: SeriesSample) -> StyledSegment:
    return StyledSegment(
        tag=RenderingTag.UNDECIDABLE,
        style=STYLE_TABLE[RenderingTag.UNDECIDABLE],
        x_range=(left_sample.x_deg, right_sample.x_deg),
        y_samples=(),
        band_halfwidth=_max_band(left_sample.band_halfwidth, right_sample.band_halfwidth),
        is_undecidable=True,
    )


def _coalesce_same_tag(segments: Sequence[StyledSegment]) -> tuple[StyledSegment, ...]:
    coalesced: list[StyledSegment] = []
    for segment in segments:
        if coalesced and _can_coalesce(coalesced[-1], segment) and coalesced[-1].tag == segment.tag:
            coalesced[-1] = _merge_segments(coalesced[-1], segment, segment.tag)
        else:
            coalesced.append(segment)
    return tuple(coalesced)


def _coalesce_for_legibility(
    segments: Sequence[StyledSegment],
    min_arc_width_deg: float,
    max_segments: int | None,
) -> tuple[StyledSegment, ...]:
    coalesced = list(segments)
    while len(coalesced) > 1 and _needs_legibility_merge(coalesced, min_arc_width_deg, max_segments):
        candidate_index = _legibility_candidate_index(coalesced, min_arc_width_deg, max_segments)
        neighbor_index = _merge_neighbor_index(coalesced, candidate_index)
        first_index = min(candidate_index, neighbor_index)
        merged_tag = _weakest_tag(coalesced[first_index].tag, coalesced[first_index + 1].tag)
        coalesced[first_index : first_index + 2] = [
            _merge_segments(coalesced[first_index], coalesced[first_index + 1], merged_tag)
        ]
        coalesced = list(_coalesce_same_tag(coalesced))
    return tuple(coalesced)


def _needs_legibility_merge(
    segments: Sequence[StyledSegment],
    min_arc_width_deg: float,
    max_segments: int | None,
) -> bool:
    if max_segments is not None and len(segments) > max_segments:
        return True
    return any(_segment_width(segment) < min_arc_width_deg for segment in segments)


def _legibility_candidate_index(
    segments: Sequence[StyledSegment],
    min_arc_width_deg: float,
    max_segments: int | None,
) -> int:
    if max_segments is not None and len(segments) > max_segments:
        candidate_indexes: Iterable[int] = range(len(segments))
    else:
        candidate_indexes = (
            index
            for index, segment in enumerate(segments)
            if _segment_width(segment) < min_arc_width_deg
        )
    return min(
        candidate_indexes,
        key=lambda index: (_segment_width(segments[index]), segments[index].x_range[0]),
    )


def _merge_neighbor_index(segments: Sequence[StyledSegment], candidate_index: int) -> int:
    neighbor_options: list[tuple[int, int]] = []
    if candidate_index > 0:
        neighbor_options.append((candidate_index - 1, 0))
    if candidate_index < len(segments) - 1:
        neighbor_options.append((candidate_index + 1, 1))

    candidate = segments[candidate_index]
    return min(
        neighbor_options,
        key=lambda option: _neighbor_rank(candidate, segments[option[0]], option[1]),
    )[0]


def _neighbor_rank(
    candidate: StyledSegment,
    neighbor: StyledSegment,
    side_rank: int,
) -> tuple[int, float, int]:
    same_tag_rank = 0 if neighbor.tag == candidate.tag else 1
    weaker_rank = 0 if _tag_strength(neighbor.tag) <= _tag_strength(candidate.tag) else 1
    return (same_tag_rank + weaker_rank, _segment_width(neighbor), side_rank)


def _merge_segments(
    left_segment: StyledSegment,
    right_segment: StyledSegment,
    tag: SegmentTag,
) -> StyledSegment:
    if not _can_coalesce(left_segment, right_segment):
        raise ValueError("segments must be adjacent to coalesce")
    style = STYLE_TABLE[tag]
    return StyledSegment(
        tag=tag,
        style=style,
        x_range=(left_segment.x_range[0], right_segment.x_range[1]),
        y_samples=_merged_samples(left_segment, right_segment) if style.draw_line else (),
        band_halfwidth=_max_band(left_segment.band_halfwidth, right_segment.band_halfwidth),
        is_undecidable=tag is RenderingTag.UNDECIDABLE,
    )


def _merged_samples(
    left_segment: StyledSegment,
    right_segment: StyledSegment,
) -> tuple[StyledSample, ...]:
    if not left_segment.y_samples:
        return right_segment.y_samples
    if not right_segment.y_samples:
        return left_segment.y_samples
    if abs(left_segment.y_samples[-1].x_deg - right_segment.y_samples[0].x_deg) <= _ADJACENT_TOLERANCE:
        return left_segment.y_samples + right_segment.y_samples[1:]
    return left_segment.y_samples + right_segment.y_samples


def _can_coalesce(left_segment: StyledSegment, right_segment: StyledSegment) -> bool:
    return abs(left_segment.x_range[1] - right_segment.x_range[0]) <= _ADJACENT_TOLERANCE


def _weakest_tag(left_tag: SegmentTag, right_tag: SegmentTag) -> SegmentTag:
    if left_tag is RenderingTag.UNDECIDABLE or right_tag is RenderingTag.UNDECIDABLE:
        return RenderingTag.UNDECIDABLE
    return Provenance.join(left_tag, right_tag)


def _tag_strength(tag: SegmentTag) -> int:
    if tag is RenderingTag.UNDECIDABLE:
        return -1
    return int(tag)


def _segment_width(segment: StyledSegment) -> float:
    return segment.x_range[1] - segment.x_range[0]


def _max_band(left_band: float | None, right_band: float | None) -> float | None:
    if left_band is None:
        return right_band
    if right_band is None:
        return left_band
    return max(left_band, right_band)


def _legend_key(tag: SegmentTag) -> str:
    if isinstance(tag, Provenance):
        return tag.name
    return tag.value


__all__ = [
    "STYLE_TABLE",
    "BandFill",
    "Marker",
    "ProvenanceStyle",
    "RenderingTag",
    "SegmentTag",
    "SeriesSample",
    "Stroke",
    "StyledSample",
    "StyledSegment",
    "style_legend_for_json",
    "split_series",
]
