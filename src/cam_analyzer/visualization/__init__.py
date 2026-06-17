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

__all__ = [
    "STYLE_TABLE",
    "ProvenanceStyle",
    "RenderingTag",
    "SegmentTag",
    "SeriesSample",
    "StyledSample",
    "StyledSegment",
    "split_series",
    "style_legend_for_json",
]
