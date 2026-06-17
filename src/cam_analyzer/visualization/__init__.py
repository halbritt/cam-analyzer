"""Renderer-agnostic visualization primitives."""

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
    "render_valve_lift_svg",
    "split_series",
    "style_legend_for_json",
]
