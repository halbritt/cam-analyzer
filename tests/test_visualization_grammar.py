from __future__ import annotations

import pytest

from cam_analyzer.profile.provenance_map import ProvenanceMap
from cam_analyzer.quantity import Provenance, Refusal
from cam_analyzer.visualization import (
    RenderingTag,
    SeriesSample,
    StyledSegment,
    split_series,
    style_legend_for_json,
)


def _assert_gapless(
    segments: tuple[StyledSegment, ...],
    start_deg: float,
    end_deg: float,
) -> None:
    assert segments[0].x_range[0] == pytest.approx(start_deg)
    assert segments[-1].x_range[1] == pytest.approx(end_deg)
    for left_segment, right_segment in zip(segments, segments[1:]):
        assert left_segment.x_range[1] == pytest.approx(right_segment.x_range[0])


def test_split_series_tiles_sample_domain_at_provenance_boundaries() -> None:
    provenance_map = ProvenanceMap(
        [
            (0.0, Provenance.MEASURED),
            (30.0, Provenance.INFERRED),
            (75.0, Provenance.EXTRAPOLATED),
        ]
    )
    samples = (
        SeriesSample(0.0, 0.0),
        SeriesSample(30.0, 3.0),
        SeriesSample(60.0, 6.0),
        SeriesSample(90.0, 9.0),
    )

    segments = split_series(samples, provenance_map)

    _assert_gapless(segments, 0.0, 90.0)
    assert [segment.tag for segment in segments] == [
        Provenance.MEASURED,
        Provenance.INFERRED,
        Provenance.EXTRAPOLATED,
    ]
    assert [segment.x_range for segment in segments] == [
        (0.0, 30.0),
        (30.0, 75.0),
        (75.0, 90.0),
    ]
    assert segments[1].y_samples[-1].x_deg == pytest.approx(75.0)
    assert segments[1].y_samples[-1].y == pytest.approx(7.5)


def test_short_segments_coalesce_toward_weaker_provenance() -> None:
    provenance_map = ProvenanceMap(
        [
            (0.0, Provenance.EXTRAPOLATED),
            (10.0, Provenance.MEASURED),
            (12.0, Provenance.EXTRAPOLATED),
        ]
    )
    samples = (
        SeriesSample(0.0, 0.0),
        SeriesSample(30.0, 3.0),
    )

    segments = split_series(samples, provenance_map, min_arc_width_deg=5.0)

    assert len(segments) == 1
    assert segments[0].tag is Provenance.EXTRAPOLATED
    assert segments[0].x_range == (0.0, 30.0)
    assert segments[0].style.stroke == "long-dash"
    assert segments[0].style.draw_line is True


def test_refused_samples_emit_no_line_without_interpolating_across_gap() -> None:
    provenance_map = ProvenanceMap.constant(Provenance.MEASURED)
    refusal = Refusal(
        requested="lift at 10 deg",
        reason="operator refused this sample",
        remedy="provide measured lift data",
        provenance=Provenance.EXTRAPOLATED,
    )
    samples = (
        SeriesSample(0.0, 0.0),
        SeriesSample(5.0, 0.5),
        SeriesSample(10.0, None, refusal=refusal),
        SeriesSample(15.0, 1.5),
        SeriesSample(20.0, 2.0),
    )

    segments = split_series(samples, provenance_map)

    _assert_gapless(segments, 0.0, 20.0)
    assert [segment.tag for segment in segments] == [
        Provenance.MEASURED,
        RenderingTag.UNDECIDABLE,
        Provenance.MEASURED,
    ]
    refused_segment = segments[1]
    assert refused_segment.x_range == (5.0, 15.0)
    assert refused_segment.y_samples == ()
    assert refused_segment.is_undecidable is True
    assert refused_segment.style.draw_line is False
    assert refused_segment.style.band_fill == "cross-hatch"
    assert all(segment.x_range != (0.0, 20.0) for segment in segments if segment.style.draw_line)


def test_style_legend_for_json_serializes_the_single_style_table() -> None:
    legend = style_legend_for_json()

    assert legend["INFERRED"]["stroke"] == "short-dash"
    assert legend["EXTRAPOLATED"]["stroke"] == "long-dash"
    assert legend["UNDECIDABLE"]["band_fill"] == "cross-hatch"
    assert legend["UNDECIDABLE"]["draw_line"] is False
