"""Dependency-free SVG renderers for RFC-0004 chart projections."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from html import escape
from typing import cast

_SVG_WIDTH = 1040.0
_SVG_HEIGHT = 680.0
_PLOT_LEFT = 78.0
_PLOT_TOP = 82.0
_PLOT_WIDTH = 888.0
_PLOT_HEIGHT = 372.0
_CYCLE_DEGREES = 720.0
_LEGEND_TITLE_Y = 540.0
_PROFILE_LEGEND_START_Y = 562.0
_PROFILE_LEGEND_ROW_GAP = 20.0
_PROVENANCE_LEGEND_START_Y = 562.0
_PROVENANCE_LEGEND_ROW_GAP = 18.0
_FOOTER_BASELINE_Y = 654.0
_PROFILE_COLORS = ("#2563eb", "#dc2626", "#059669", "#7c3aed")
_STROKE_DASHARRAY = {
    "solid": "",
    "short-dash": "6 4",
    "long-dash": "12 7",
    "none": "",
}


@dataclass(frozen=True, slots=True)
class _Point:
    crank_deg: float
    lift_in: float


@dataclass(frozen=True, slots=True)
class _LiftSegment:
    provenance: str
    points: tuple[_Point, ...]


@dataclass(frozen=True, slots=True)
class _LiftProfile:
    name: str
    color: str
    segments: tuple[_LiftSegment, ...]


def render_valve_lift_svg(
    projection: Mapping[str, object],
    *,
    title: str = "Valve lift overlay",
) -> str:
    """Render the projection's lift series as a static provenance-styled SVG."""

    profiles = _lift_profiles(projection)
    y_max = _nice_lift_max(_max_lift(profiles))
    legend = _mapping_field(projection, "provenance_legend")
    svg_parts = _svg_header(title)
    svg_parts.extend(_grid_svg(y_max))
    for profile in profiles:
        svg_parts.extend(_profile_svg(profile, legend, y_max))
    svg_parts.extend(_legend_svg(profiles, legend, str(projection.get("schema", "unknown"))))
    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def _lift_profiles(projection: Mapping[str, object]) -> tuple[_LiftProfile, ...]:
    profiles = []
    for index, raw_profile in enumerate(_sequence_field(projection, "profiles")):
        profile = _as_mapping(raw_profile, "profile")
        name = _string_field(profile, "name")
        series = _mapping_field(profile, "series")
        lift = _mapping_field(series, "lift")
        profiles.append(
            _LiftProfile(
                name=name,
                color=_PROFILE_COLORS[index % len(_PROFILE_COLORS)],
                segments=_lift_segments(lift),
            )
        )
    if not profiles:
        raise ValueError("projection must contain at least one profile")
    return tuple(profiles)


def _lift_segments(lift_series: Mapping[str, object]) -> tuple[_LiftSegment, ...]:
    segments = []
    for raw_segment in _sequence_field(lift_series, "segments"):
        segment = _as_mapping(raw_segment, "lift segment")
        if not _bool_field(segment, "draw_line"):
            continue
        provenance = _string_field(segment, "provenance")
        points = tuple(_segment_points(segment))
        if points:
            segments.append(_LiftSegment(provenance=provenance, points=points))
    if not segments:
        raise ValueError("projection lift series contains no drawable segments")
    return tuple(segments)


def _segment_points(segment: Mapping[str, object]) -> tuple[_Point, ...]:
    points = []
    for raw_point in _sequence_field(segment, "points"):
        point = _as_mapping(raw_point, "segment point")
        raw_lift = point.get("value")
        if isinstance(raw_lift, int | float):
            points.append(
                _Point(
                    crank_deg=_float_field(point, "crank_deg"),
                    lift_in=float(raw_lift),
                )
            )
    return tuple(points)


def _max_lift(profiles: Sequence[_LiftProfile]) -> float:
    lifts = [
        point.lift_in
        for profile in profiles
        for segment in profile.segments
        for point in segment.points
    ]
    return max(lifts, default=0.0)


def _nice_lift_max(max_lift: float) -> float:
    if max_lift <= 0.0:
        return 0.1
    return max(0.1, math.ceil(max_lift * 10.0) / 10.0)


def _svg_header(title: str) -> list[str]:
    safe_title = escape(title)
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_SVG_WIDTH:.0f} {_SVG_HEIGHT:.0f}" '
        'role="img" aria-labelledby="chart-title chart-desc">',
        f"<title id=\"chart-title\">{safe_title}</title>",
        "<desc id=\"chart-desc\">Valve-lift overlay rendered from a source-blind "
        "cam-analyzer visualization projection.</desc>",
        f'<rect x="0" y="0" width="{_SVG_WIDTH:.0f}" height="{_SVG_HEIGHT:.0f}" fill="#ffffff"/>',
        f'<text x="{_PLOT_LEFT:.0f}" y="42" font-family="Arial, sans-serif" '
        f'font-size="24" font-weight="700" fill="#111827">{safe_title}</text>',
        f'<text x="{_PLOT_LEFT:.0f}" y="66" font-family="Arial, sans-serif" '
        'font-size="13" fill="#4b5563">Valve lift overlay, sampled over 720 crank degrees</text>',
    ]


def _grid_svg(y_max: float) -> list[str]:
    parts = [
        f'<rect x="{_PLOT_LEFT:.0f}" y="{_PLOT_TOP:.0f}" width="{_PLOT_WIDTH:.0f}" '
        f'height="{_PLOT_HEIGHT:.0f}" fill="#f9fafb" stroke="#d1d5db"/>'
    ]
    parts.extend(_x_ticks_svg())
    parts.extend(_y_ticks_svg(y_max))
    parts.append(_axis_label_svg())
    return parts


def _x_ticks_svg() -> list[str]:
    parts = []
    for crank_deg in range(0, int(_CYCLE_DEGREES) + 1, 90):
        x = _x_px(float(crank_deg))
        parts.append(
            f'<line x1="{x:.2f}" y1="{_PLOT_TOP:.0f}" x2="{x:.2f}" '
            f'y2="{_PLOT_TOP + _PLOT_HEIGHT:.0f}" stroke="#e5e7eb"/>'
        )
        parts.append(
            f'<text x="{x:.2f}" y="{_PLOT_TOP + _PLOT_HEIGHT + 24:.0f}" '
            f'text-anchor="middle" font-family="Arial, sans-serif" font-size="11" '
            f'fill="#374151">{crank_deg}</text>'
        )
    return parts


def _y_ticks_svg(y_max: float) -> list[str]:
    parts = []
    for index in range(5):
        lift = y_max * index / 4.0
        y = _y_px(lift, y_max)
        parts.append(
            f'<line x1="{_PLOT_LEFT:.0f}" y1="{y:.2f}" x2="{_PLOT_LEFT + _PLOT_WIDTH:.0f}" '
            f'y2="{y:.2f}" stroke="#e5e7eb"/>'
        )
        parts.append(
            f'<text x="{_PLOT_LEFT - 12:.0f}" y="{y + 4:.2f}" text-anchor="end" '
            f'font-family="Arial, sans-serif" font-size="11" fill="#374151">{lift:.3f}</text>'
        )
    return parts


def _axis_label_svg() -> str:
    return (
        f'<text x="{_PLOT_LEFT + _PLOT_WIDTH / 2:.0f}" y="{_PLOT_TOP + _PLOT_HEIGHT + 52:.0f}" '
        'text-anchor="middle" font-family="Arial, sans-serif" font-size="13" '
        'fill="#111827">Crank angle (deg)</text>'
        f'<text x="22" y="{_PLOT_TOP + _PLOT_HEIGHT / 2:.0f}" transform="rotate(-90 22 '
        f'{_PLOT_TOP + _PLOT_HEIGHT / 2:.0f})" text-anchor="middle" '
        'font-family="Arial, sans-serif" font-size="13" fill="#111827">Valve lift (in)</text>'
    )


def _profile_svg(
    profile: _LiftProfile,
    legend: Mapping[str, object],
    y_max: float,
) -> list[str]:
    parts = []
    for segment in profile.segments:
        style = _mapping_field(legend, segment.provenance)
        stroke_dasharray = _dasharray(_string_field(style, "stroke"))
        dash_attr = f' stroke-dasharray="{stroke_dasharray}"' if stroke_dasharray else ""
        parts.append(
            f'<path d="{_path_data(segment.points, y_max)}" fill="none" '
            f'stroke="{profile.color}" stroke-width="2.5" stroke-opacity="{_float_field(style, "opacity"):.2f}"'
            f'{dash_attr} stroke-linecap="round" stroke-linejoin="round"/>'
        )
    return parts


def _legend_svg(
    profiles: Sequence[_LiftProfile],
    legend: Mapping[str, object],
    schema: str,
) -> list[str]:
    parts = [
        f'<text x="{_PLOT_LEFT:.0f}" y="{_LEGEND_TITLE_Y:.0f}" font-family="Arial, sans-serif" '
        'font-size="13" font-weight="700" fill="#111827">Profiles</text>'
    ]
    parts.extend(_profile_legend_svg(profiles))
    parts.extend(_provenance_legend_svg(legend))
    safe_schema = escape(schema)
    parts.append(
        f'<text x="{_PLOT_LEFT:.0f}" y="{_FOOTER_BASELINE_Y:.0f}" font-family="Arial, sans-serif" '
        f'font-size="11" fill="#4b5563">Projection: {safe_schema}. Renderer draws only sampled '
        "boundary answers and does not recompute source facts.</text>"
    )
    return parts


def _profile_legend_svg(profiles: Sequence[_LiftProfile]) -> list[str]:
    parts = []
    for index, profile in enumerate(profiles):
        y = _PROFILE_LEGEND_START_Y + index * _PROFILE_LEGEND_ROW_GAP
        parts.append(
            f'<line x1="{_PLOT_LEFT:.0f}" y1="{y:.0f}" x2="{_PLOT_LEFT + 28:.0f}" y2="{y:.0f}" '
            f'stroke="{profile.color}" stroke-width="3"/>'
        )
        parts.append(
            f'<text x="{_PLOT_LEFT + 38:.0f}" y="{y + 4:.0f}" font-family="Arial, sans-serif" '
            f'font-size="12" fill="#111827">{escape(profile.name.title())}</text>'
        )
    return parts


def _provenance_legend_svg(legend: Mapping[str, object]) -> list[str]:
    parts = [
        f'<text x="398" y="{_LEGEND_TITLE_Y:.0f}" font-family="Arial, sans-serif" font-size="13" '
        'font-weight="700" fill="#111827">Provenance</text>'
    ]
    for index, provenance in enumerate(("MEASURED", "INFERRED", "EXTRAPOLATED", "UNDECIDABLE")):
        style = _mapping_field(legend, provenance)
        y = _PROVENANCE_LEGEND_START_Y + index * _PROVENANCE_LEGEND_ROW_GAP
        if _bool_field(style, "draw_line"):
            dash_attr = f' stroke-dasharray="{_dasharray(_string_field(style, "stroke"))}"'
            parts.append(
                f'<line x1="398" y1="{y:.0f}" x2="434" y2="{y:.0f}" stroke="#111827" '
                f'stroke-width="2.5" stroke-opacity="{_float_field(style, "opacity"):.2f}"{dash_attr}/>'
            )
        else:
            parts.append('<rect x="398" y="{:.0f}" width="36" height="10" fill="none" stroke="#111827"/>'.format(y - 7))
        parts.append(
            f'<text x="446" y="{y + 4:.0f}" font-family="Arial, sans-serif" font-size="12" '
            f'fill="#111827">{provenance}</text>'
        )
    return parts


def _path_data(points: Sequence[_Point], y_max: float) -> str:
    commands = [
        f"{'M' if index == 0 else 'L'} {_x_px(point.crank_deg):.2f} {_y_px(point.lift_in, y_max):.2f}"
        for index, point in enumerate(points)
    ]
    return " ".join(commands)


def _x_px(crank_deg: float) -> float:
    return _PLOT_LEFT + (crank_deg / _CYCLE_DEGREES) * _PLOT_WIDTH


def _y_px(lift_in: float, y_max: float) -> float:
    return _PLOT_TOP + ((y_max - lift_in) / y_max) * _PLOT_HEIGHT


def _dasharray(stroke: str) -> str:
    if stroke not in _STROKE_DASHARRAY:
        raise ValueError(f"unknown projection stroke: {stroke}")
    return _STROKE_DASHARRAY[stroke]


def _as_mapping(raw: object, label: str) -> Mapping[str, object]:
    if not isinstance(raw, Mapping):
        raise ValueError(f"{label} must be an object")
    return cast(Mapping[str, object], raw)


def _mapping_field(row: Mapping[str, object], key: str) -> Mapping[str, object]:
    return _as_mapping(row.get(key), key)


def _sequence_field(row: Mapping[str, object], key: str) -> Sequence[object]:
    raw = row.get(key)
    if isinstance(raw, str) or not isinstance(raw, Sequence):
        raise ValueError(f"{key} must be an array")
    return raw


def _string_field(row: Mapping[str, object], key: str) -> str:
    raw = row.get(key)
    if not isinstance(raw, str):
        raise ValueError(f"{key} must be a string")
    return raw


def _float_field(row: Mapping[str, object], key: str) -> float:
    raw = row.get(key)
    if not isinstance(raw, int | float):
        raise ValueError(f"{key} must be a number")
    return float(raw)


def _bool_field(row: Mapping[str, object], key: str) -> bool:
    raw = row.get(key)
    if not isinstance(raw, bool):
        raise ValueError(f"{key} must be a boolean")
    return raw


__all__ = ["render_valve_lift_svg"]
