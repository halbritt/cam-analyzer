"""Renderer-agnostic visualization primitives."""

from cam_analyzer.visualization.coordinates import (
    PRIMARY_OVERLAP_RELATIVE_MAX_DEG,
    PRIMARY_OVERLAP_RELATIVE_MIN_DEG,
    canonical_to_overlap_display,
    canonical_to_overlap_relative,
    is_primary_overlap_display_angle,
    is_primary_overlap_relative_angle,
    overlap_display_to_canonical,
    overlap_relative_to_canonical,
)
from cam_analyzer.visualization.grammar import (
    STYLE_TABLE,
    ProvenanceStyle,
    RenderingTag,
    SegmentTag,
    SeriesSample,
    StyledSample,
    StyledSegment,
    split_series,
    style_legend_for_json,
)
from cam_analyzer.visualization.svg import render_valve_lift_svg

__all__ = [
    "STYLE_TABLE",
    "ProvenanceStyle",
    "RenderingTag",
    "SegmentTag",
    "SeriesSample",
    "StyledSample",
    "StyledSegment",
    "PRIMARY_OVERLAP_RELATIVE_MAX_DEG",
    "PRIMARY_OVERLAP_RELATIVE_MIN_DEG",
    "canonical_to_overlap_display",
    "canonical_to_overlap_relative",
    "is_primary_overlap_display_angle",
    "is_primary_overlap_relative_angle",
    "overlap_display_to_canonical",
    "overlap_relative_to_canonical",
    "render_valve_lift_svg",
    "split_series",
    "style_legend_for_json",
]
