"""Dependency-free SVG renderers for RFC-0004 chart projections."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from html import escape
from typing import cast

_SVG_WIDTH = 1536.0
_SVG_HEIGHT = 1024.0
_STACK_LEFT = 96.0
_STACK_WIDTH = 1024.0
_SUMMARY_LEFT = 1150.0
_SUMMARY_WIDTH = 342.0
_CYCLE_DEGREES = 720.0
_MAIN_X_MIN = 0.0
_MAIN_X_MAX = 360.0
_OVERLAP_WINDOW_START_DEG = 540.0
_TDC_DISPLAY_DEG = 180.0
_LIFT_TOP = 92.0
_LIFT_HEIGHT = 300.0
_VELOCITY_TOP = 444.0
_ACCELERATION_TOP = 552.0
_JERK_TOP = 660.0
_DERIVATIVE_PANEL_HEIGHT = 86.0
_SECONDARY_TOP = 786.0
_SECONDARY_HEIGHT = 54.0
_FOOTER_BASELINE_Y = 1004.0
_THRESHOLD_LIFTS = (0.001, 0.006, 0.020, 0.050, 0.100, 0.200)
_PROFILE_COLORS = {"intake": "#2563eb", "exhaust": "#dc2626"}
_FALLBACK_COLORS = ("#059669", "#7c3aed", "#0891b2")
_STROKE_DASHARRAY = {
    "solid": "",
    "short-dash": "7 5",
    "dotted": "1 6",
    "none": "",
}
_THRESHOLD_COLORS = {
    0.001: "#9ca3af",
    0.006: "#64748b",
    0.020: "#60a5fa",
    0.050: "#16a34a",
    0.100: "#f97316",
    0.200: "#7c3aed",
}


@dataclass(frozen=True, slots=True)
class _Panel:
    top: float
    height: float


@dataclass(frozen=True, slots=True)
class _Point:
    display_deg: float
    crank_deg: float
    y_value: float
    p50_half_width: float | None = None
    p95_half_width: float | None = None


@dataclass(frozen=True, slots=True)
class _SeriesSegment:
    provenance: str
    points: tuple[_Point, ...]


@dataclass(frozen=True, slots=True)
class _ProfileSeries:
    name: str
    color: str
    segments: tuple[_SeriesSegment, ...]


@dataclass(frozen=True, slots=True)
class _TimingEvent:
    label: str
    display_deg: float
    color: str
    anchor: str


@dataclass(frozen=True, slots=True)
class _OverlapRow:
    lift_in: float
    degrees: float
    estimated: bool


@dataclass(frozen=True, slots=True)
class _ProfileMetrics:
    confidence_score: float
    measured_pct: float
    inferred_pct: float
    extrapolated_pct: float


@dataclass(frozen=True, slots=True)
class _FullCycleEvent:
    code: str
    crank_deg: float
    color: str


def render_valve_lift_svg(
    projection: Mapping[str, object],
    *,
    title: str = "Valve lift overlay",
) -> str:
    """Render the projection as an overlap-centered engineering SVAJ SVG."""

    legend = _mapping_field(projection, "provenance_legend")
    lift_profiles = _profiles_for_query(projection, "lift", centered=True)
    full_lift_profiles = _profiles_for_query(projection, "lift", centered=False)
    y_max = _nice_lift_max(_max_y(full_lift_profiles))
    overlap_rows = _overlap_rows(projection)
    timing_events = _timing_events(projection)
    full_cycle_events = _full_cycle_timing_events(projection)
    profile_metrics = _profile_metrics(projection)
    warnings = _validation_warnings(projection, profile_metrics)

    svg_parts = _svg_header(title)
    svg_parts.extend(_lift_panel_svg(lift_profiles, legend, y_max, timing_events, overlap_rows))
    svg_parts.extend(_derivative_stack_svg(projection, legend))
    svg_parts.extend(_full_cycle_overview_svg(full_lift_profiles, full_cycle_events))
    svg_parts.extend(_summary_panel_svg(projection, overlap_rows, profile_metrics, warnings))
    svg_parts.extend(_legend_svg(legend, str(projection.get("schema", "unknown"))))
    svg_parts.append("</svg>")
    return "\n".join(svg_parts)


def _profiles_for_query(
    projection: Mapping[str, object],
    query: str,
    *,
    centered: bool,
) -> tuple[_ProfileSeries, ...]:
    profiles = []
    for index, raw_profile in enumerate(_sequence_field(projection, "profiles")):
        profile = _as_mapping(raw_profile, "profile")
        name = _string_field(profile, "name")
        series = _mapping_field(_mapping_field(profile, "series"), query)
        color = _PROFILE_COLORS.get(name, _FALLBACK_COLORS[index % len(_FALLBACK_COLORS)])
        profiles.append(
            _ProfileSeries(
                name=name,
                color=color,
                segments=_series_segments(series, centered=centered),
            )
        )
    if not profiles:
        raise ValueError("projection must contain at least one profile")
    return tuple(profiles)


def _series_segments(
    series: Mapping[str, object],
    *,
    centered: bool,
) -> tuple[_SeriesSegment, ...]:
    segments = []
    for raw_segment in _sequence_field(series, "segments"):
        segment = _as_mapping(raw_segment, "series segment")
        if not _bool_field(segment, "draw_line"):
            continue
        points = tuple(_segment_points(segment, centered=centered))
        if points:
            segments.append(
                _SeriesSegment(
                    provenance=_string_field(segment, "provenance"),
                    points=points,
                )
            )
    if not segments:
        raise ValueError("projection lift series contains no drawable segments")
    return tuple(segments)


def _segment_points(
    segment: Mapping[str, object],
    *,
    centered: bool,
) -> tuple[_Point, ...]:
    points = []
    for raw_point in _sequence_field(segment, "points"):
        point = _as_mapping(raw_point, "segment point")
        raw_y = point.get("value")
        if not isinstance(raw_y, int | float):
            continue
        crank_deg = _float_field(point, "crank_deg")
        display_deg = _display_deg(crank_deg)
        if centered and not _in_centered_window(display_deg):
            continue
        points.append(
            _Point(
                display_deg=display_deg if centered else crank_deg,
                crank_deg=crank_deg,
                y_value=float(raw_y),
                p50_half_width=_confidence_half_width(point, "p50_half_width"),
                p95_half_width=_confidence_half_width(point, "p95_half_width"),
            )
        )
    return tuple(sorted(points, key=lambda candidate: candidate.display_deg))


def _svg_header(title: str) -> list[str]:
    safe_title = escape(title)
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_SVG_WIDTH:.0f} {_SVG_HEIGHT:.0f}" '
        'role="img" aria-labelledby="chart-title chart-desc">',
        f'<title id="chart-title">{safe_title}</title>',
        "<desc id=\"chart-desc\">Overlap-centered SVAJ stack with hard cam-card "
        "events, lift thresholds, confidence bands, and source-blind profile quality.</desc>",
        f'<rect x="0" y="0" width="{_SVG_WIDTH:.0f}" height="{_SVG_HEIGHT:.0f}" fill="#ffffff"/>',
        f'<text x="24" y="38" font-family="Arial, sans-serif" font-size="28" '
        f'font-weight="700" fill="#0f172a">{safe_title}</text>',
        '<text x="24" y="64" font-family="Arial, sans-serif" font-size="14" '
        'fill="#475569">Primary engineering view: 0-360 crank-degree overlap window; 180 = TDC overlap</text>',
    ]


def _lift_panel_svg(
    profiles: Sequence[_ProfileSeries],
    legend: Mapping[str, object],
    y_max: float,
    timing_events: Sequence[_TimingEvent],
    overlap_rows: Sequence[_OverlapRow],
) -> list[str]:
    panel = _Panel(_LIFT_TOP, _LIFT_HEIGHT)
    parts = _panel_frame_svg(panel, "Lift (in)")
    parts.extend(_overlap_band_svg(panel, overlap_rows))
    parts.extend(_threshold_lines_svg(panel, y_max))
    parts.extend(_x_grid_svg(panel, major=True))
    parts.extend(_y_ticks_svg(panel, 0.0, y_max, precision=3))
    for profile in profiles:
        parts.extend(_confidence_band_svg(profile, y_max, panel, opacity=0.10, width="p95"))
        parts.extend(_confidence_band_svg(profile, y_max, panel, opacity=0.05, width="p50"))
    for profile in profiles:
        parts.extend(_series_svg(profile, legend, 0.0, y_max, panel, stroke_width=2.8))
    parts.extend(_timing_event_svg(timing_events, panel))
    parts.append(_x_axis_label_svg(panel, "Overlap-centered crank window (deg; 180 = TDC overlap)"))
    return parts


def _derivative_stack_svg(
    projection: Mapping[str, object],
    legend: Mapping[str, object],
) -> list[str]:
    panels = {
        "velocity": _Panel(_VELOCITY_TOP, _DERIVATIVE_PANEL_HEIGHT),
        "acceleration": _Panel(_ACCELERATION_TOP, _DERIVATIVE_PANEL_HEIGHT),
        "jerk": _Panel(_JERK_TOP, _DERIVATIVE_PANEL_HEIGHT),
    }
    parts: list[str] = []
    for query, panel in panels.items():
        profiles = _profiles_for_query(projection, query, centered=True)
        range_profiles = _profiles_for_query(projection, query, centered=False)
        y_min, y_max = _symmetric_range(range_profiles)
        parts.extend(_panel_frame_svg(panel, _series_label(query)))
        parts.extend(_x_grid_svg(panel, major=False))
        parts.extend(_zero_line_svg(panel, y_min, y_max))
        parts.extend(_y_ticks_svg(panel, y_min, y_max, precision=4))
        for profile in profiles:
            parts.extend(_series_svg(profile, legend, y_min, y_max, panel, stroke_width=1.7))
    parts.append(_x_axis_label_svg(_Panel(_JERK_TOP, _DERIVATIVE_PANEL_HEIGHT), ""))
    return parts


def _full_cycle_overview_svg(
    profiles: Sequence[_ProfileSeries],
    events: Sequence[_FullCycleEvent],
) -> list[str]:
    panel = _Panel(_SECONDARY_TOP, _SECONDARY_HEIGHT)
    y_max = _nice_lift_max(_max_y(profiles))
    parts = [
        f'<text x="{_STACK_LEFT:.0f}" y="{panel.top - 10:.0f}" font-family="Arial, sans-serif" '
        'font-size="13" font-weight="700" fill="#0f172a">Secondary 720 deg overview</text>',
        f'<rect x="{_STACK_LEFT:.0f}" y="{panel.top:.0f}" width="{_STACK_WIDTH:.0f}" '
        f'height="{panel.height:.0f}" fill="#f8fafc" stroke="#cbd5e1"/>',
    ]
    for start_deg, end_deg in ((0.0, 180.0), (540.0, 720.0)):
        x_left = _full_x_px(start_deg)
        width = _full_x_px(end_deg) - x_left
        parts.append(
            f'<rect x="{x_left:.2f}" y="{panel.top:.0f}" width="{width:.2f}" '
            f'height="{panel.height:.0f}" fill="#e2e8f0" fill-opacity="0.35"/>'
        )
    for crank_deg in range(0, 721, 180):
        x_pos = _full_x_px(float(crank_deg))
        parts.append(
            f'<line x1="{x_pos:.2f}" y1="{panel.top:.0f}" x2="{x_pos:.2f}" '
            f'y2="{panel.top + panel.height:.0f}" stroke="#e2e8f0"/>'
        )
        parts.append(
            f'<text x="{x_pos:.2f}" y="{panel.top + panel.height + 14:.0f}" '
            f'text-anchor="middle" font-family="Arial, sans-serif" font-size="10" fill="#475569">{crank_deg}</text>'
        )
    for profile in profiles:
        for segment in profile.segments:
            path = _path_data(segment.points, 0.0, y_max, panel, full_cycle=True)
            if path:
                parts.append(
                    f'<path d="{path}" fill="none" stroke="{profile.color}" stroke-width="1.3" '
                    'stroke-opacity="0.70" stroke-linecap="round" stroke-linejoin="round"/>'
                )
    for event in events:
        x_pos = _full_x_px(event.crank_deg)
        parts.append(
            f'<line x1="{x_pos:.2f}" y1="{panel.top:.0f}" x2="{x_pos:.2f}" '
            f'y2="{panel.top + panel.height:.0f}" stroke="{event.color}" stroke-width="1.1" '
            f'stroke-dasharray="4 4" data-event="{event.code}"/>'
        )
        parts.append(
            f'<text x="{x_pos:.2f}" y="{panel.top + 11:.0f}" text-anchor="middle" '
            f'font-family="Arial, sans-serif" font-size="9" font-weight="700" '
            f'fill="{event.color}">{escape(event.code)}</text>'
        )
    return parts


def _summary_panel_svg(
    projection: Mapping[str, object],
    overlap_rows: Sequence[_OverlapRow],
    metrics: _ProfileMetrics,
    warnings: Sequence[str],
) -> list[str]:
    parts = [
        f'<rect x="{_SUMMARY_LEFT:.0f}" y="{_LIFT_TOP:.0f}" width="{_SUMMARY_WIDTH:.0f}" '
        'height="748" rx="6" fill="#f8fafc" stroke="#cbd5e1"/>',
        *_section_title_svg("Timing Summary (@ 0.050 in)", _LIFT_TOP + 28.0),
        *_timing_summary_svg(projection, _LIFT_TOP + 54.0),
        *_section_title_svg("Overlap Summary", _LIFT_TOP + 184.0),
        *_overlap_summary_svg(overlap_rows, _LIFT_TOP + 210.0),
        *_section_title_svg("Duration Summary (deg)", _LIFT_TOP + 314.0),
        *_duration_summary_svg(projection, _LIFT_TOP + 340.0),
        *_section_title_svg("Profile Quality", _LIFT_TOP + 506.0),
        *_quality_summary_svg(metrics, _LIFT_TOP + 532.0),
        *_section_title_svg("Validation", _LIFT_TOP + 620.0),
        *_validation_summary_svg(warnings, _LIFT_TOP + 646.0),
    ]
    return parts


def _legend_svg(legend: Mapping[str, object], schema: str) -> list[str]:
    parts = [
        '<rect x="24" y="856" width="348" height="118" rx="6" fill="#ffffff" stroke="#cbd5e1"/>',
        '<text x="40" y="880" font-family="Arial, sans-serif" font-size="13" font-weight="700" '
        'fill="#0f172a">Cam Card Source</text>',
        '<text x="40" y="904" font-family="Arial, sans-serif" font-size="12" fill="#1e293b">'
        'Web Cam 81-651 / WR250R DOHC 4V</text>',
        '<text x="40" y="924" font-family="Arial, sans-serif" font-size="12" fill="#1e293b">'
        'Peak lift 0.360 in, cold lash 0.006/0.008 in</text>',
        '<text x="40" y="944" font-family="Arial, sans-serif" font-size="12" fill="#1e293b">'
        'Primary view: 0-360, 180 = TDC overlap</text>',
        '<rect x="396" y="856" width="520" height="118" rx="6" fill="#ffffff" stroke="#cbd5e1"/>',
        '<text x="412" y="880" font-family="Arial, sans-serif" font-size="13" font-weight="700" '
        'fill="#0f172a">Legend / Provenance</text>',
        *_provenance_legend_svg(legend),
        '<rect x="940" y="856" width="552" height="118" rx="6" fill="#ffffff" stroke="#cbd5e1"/>',
        '<text x="956" y="880" font-family="Arial, sans-serif" font-size="13" font-weight="700" '
        'fill="#0f172a">How to read</text>',
        *_legend_notes_svg(),
    ]
    safe_schema = escape(schema)
    parts.append(
        f'<text x="{_SVG_WIDTH / 2:.0f}" y="{_FOOTER_BASELINE_Y:.0f}" text-anchor="middle" '
        f'font-family="Arial, sans-serif" font-size="11" fill="#64748b">Projection: {safe_schema}. '
        'Renderer draws only sampled boundary answers and does not recompute source facts.</text>'
    )
    return parts


def _panel_frame_svg(panel: _Panel, label: str) -> list[str]:
    parts = [
        f'<rect x="{_STACK_LEFT:.0f}" y="{panel.top:.0f}" width="{_STACK_WIDTH:.0f}" '
        f'height="{panel.height:.0f}" fill="#ffffff" stroke="#cbd5e1"/>',
        f'<line x1="{_x_px(_TDC_DISPLAY_DEG):.2f}" y1="{panel.top:.0f}" x2="{_x_px(_TDC_DISPLAY_DEG):.2f}" '
        f'y2="{panel.top + panel.height:.0f}" stroke="#64748b" stroke-width="1.2"/>',
        f'<text x="32" y="{panel.top + 20:.0f}" font-family="Arial, sans-serif" '
        f'font-size="13" font-weight="700" fill="#0f172a">{escape(label)}</text>',
    ]
    if panel.top == _LIFT_TOP:
        parts.append(
            f'<text x="{_x_px(_TDC_DISPLAY_DEG):.2f}" y="{panel.top + 18:.0f}" text-anchor="middle" '
            'font-family="Arial, sans-serif" font-size="11" font-weight="700" fill="#334155">180 TDC</text>'
        )
    return parts


def _x_grid_svg(panel: _Panel, *, major: bool) -> list[str]:
    parts = []
    for display_deg in range(int(_MAIN_X_MIN), int(_MAIN_X_MAX) + 1, 45):
        x_pos = _x_px(float(display_deg))
        stroke = "#cbd5e1" if display_deg % 90 == 0 else "#e2e8f0"
        parts.append(
            f'<line x1="{x_pos:.2f}" y1="{panel.top:.0f}" x2="{x_pos:.2f}" '
            f'y2="{panel.top + panel.height:.0f}" stroke="{stroke}"/>'
        )
        if major and display_deg % 45 == 0:
            label = "180 TDC" if display_deg == int(_TDC_DISPLAY_DEG) else f"{display_deg:d}"
            parts.append(
                f'<text x="{x_pos:.2f}" y="{panel.top + panel.height + 20:.0f}" text-anchor="middle" '
                f'font-family="Arial, sans-serif" font-size="11" fill="#334155">{label}</text>'
            )
    return parts


def _y_ticks_svg(panel: _Panel, y_min: float, y_max: float, *, precision: int) -> list[str]:
    parts = []
    for value in _tick_values(y_min, y_max):
        y_pos = _y_px(value, y_min, y_max, panel)
        parts.append(
            f'<line x1="{_STACK_LEFT:.0f}" y1="{y_pos:.2f}" x2="{_STACK_LEFT + _STACK_WIDTH:.0f}" '
            'y2="{:.2f}" stroke="#e2e8f0"/>'.format(y_pos)
        )
        parts.append(
            f'<text x="{_STACK_LEFT - 14:.0f}" y="{y_pos + 4:.2f}" text-anchor="end" '
            f'font-family="Arial, sans-serif" font-size="10" fill="#334155">{value:.{precision}f}</text>'
        )
    return parts


def _threshold_lines_svg(panel: _Panel, y_max: float) -> list[str]:
    parts = []
    baselines = _threshold_label_baselines(panel, y_max)
    label_x = _STACK_LEFT + _STACK_WIDTH - 10.0
    for lift_in in _THRESHOLD_LIFTS:
        if lift_in > y_max:
            continue
        y_pos = _y_px(lift_in, 0.0, y_max, panel)
        color = _THRESHOLD_COLORS[lift_in]
        parts.append(
            f'<line x1="{_STACK_LEFT:.0f}" y1="{y_pos:.2f}" x2="{_STACK_LEFT + _STACK_WIDTH:.0f}" '
            f'y2="{y_pos:.2f}" stroke="{color}" stroke-dasharray="5 4" stroke-opacity="0.62"/>'
        )
        label_y = baselines[lift_in]
        if abs(label_y - (y_pos + 4.0)) > 1.5:
            parts.append(
                f'<line x1="{label_x - 56:.2f}" y1="{y_pos:.2f}" x2="{label_x - 38:.2f}" '
                f'y2="{label_y - 4:.2f}" stroke="{color}" stroke-opacity="0.45"/>'
            )
        parts.append(
            f'<text x="{label_x:.0f}" y="{label_y:.2f}" text-anchor="end" '
            f'font-family="Arial, sans-serif" font-size="11" fill="{color}">{lift_in:.3f}</text>'
        )
    return parts


def _overlap_band_svg(panel: _Panel, overlap_rows: Sequence[_OverlapRow]) -> list[str]:
    overlap_050 = next((row.degrees for row in overlap_rows if abs(row.lift_in - 0.050) < 1e-9), 0.0)
    half_width = max(overlap_050 / 2.0, 0.0)
    x_left = _x_px(_TDC_DISPLAY_DEG - half_width)
    width = _x_px(_TDC_DISPLAY_DEG + half_width) - x_left
    return [
        f'<rect x="{x_left:.2f}" y="{panel.top:.0f}" width="{width:.2f}" height="{panel.height:.0f}" '
        'fill="#e2e8f0" fill-opacity="0.55" stroke="none"/>',
        f'<text x="{_x_px(_TDC_DISPLAY_DEG):.2f}" y="{panel.top + 32:.0f}" text-anchor="middle" '
        'font-family="Arial, sans-serif" font-size="12" font-weight="700" fill="#0f172a">'
        f'OVERLAP @ 0.050 in</text>',
        f'<text x="{_x_px(_TDC_DISPLAY_DEG):.2f}" y="{panel.top + 52:.0f}" text-anchor="middle" '
        'font-family="Arial, sans-serif" font-size="20" font-weight="700" fill="#0f172a">'
        f'{overlap_050:.1f} deg</text>',
    ]


def _timing_event_svg(events: Sequence[_TimingEvent], panel: _Panel) -> list[str]:
    parts = []
    for event in events:
        x_pos = _x_px(event.display_deg)
        parts.append(
            f'<line x1="{x_pos:.2f}" y1="{panel.top:.0f}" x2="{x_pos:.2f}" '
            f'y2="{panel.top + panel.height:.0f}" stroke="{event.color}" stroke-width="1.3" '
            'stroke-dasharray="5 5"/>'
        )
        text_y = panel.top + (88.0 if event.anchor == "top" else panel.height - 18.0)
        parts.append(
            f'<text x="{x_pos + 4:.2f}" y="{text_y:.0f}" font-family="Arial, sans-serif" '
            f'font-size="11" font-weight="700" fill="{event.color}">{escape(event.label)}</text>'
        )
    return parts


def _confidence_band_svg(
    profile: _ProfileSeries,
    y_max: float,
    panel: _Panel,
    *,
    opacity: float,
    width: str,
) -> list[str]:
    parts = []
    for segment in profile.segments:
        path = _band_path_data(segment.points, 0.0, y_max, panel, width=width)
        if path:
            parts.append(
                f'<path d="{path}" fill="{profile.color}" fill-opacity="{opacity:.2f}" '
                f'stroke="none" data-confidence="{width}"/>'
            )
    return parts


def _series_svg(
    profile: _ProfileSeries,
    legend: Mapping[str, object],
    y_min: float,
    y_max: float,
    panel: _Panel,
    *,
    stroke_width: float,
) -> list[str]:
    parts = []
    for segment in profile.segments:
        style = _mapping_field(legend, segment.provenance)
        dasharray = _dasharray(_string_field(style, "stroke"))
        dash_attr = f' stroke-dasharray="{dasharray}"' if dasharray else ""
        path = _path_data(segment.points, y_min, y_max, panel, full_cycle=False)
        if path:
            parts.append(
                f'<path d="{path}" fill="none" stroke="{profile.color}" stroke-width="{stroke_width:.1f}" '
                f'stroke-opacity="{_float_field(style, "opacity"):.2f}"{dash_attr} '
                'stroke-linecap="round" stroke-linejoin="round"/>'
            )
    return parts


def _zero_line_svg(panel: _Panel, y_min: float, y_max: float) -> list[str]:
    y_pos = _y_px(0.0, y_min, y_max, panel)
    return [
        f'<line x1="{_STACK_LEFT:.0f}" y1="{y_pos:.2f}" x2="{_STACK_LEFT + _STACK_WIDTH:.0f}" '
        f'y2="{y_pos:.2f}" stroke="#94a3b8"/>'
    ]


def _x_axis_label_svg(panel: _Panel, label: str) -> str:
    if not label:
        return ""
    return (
        f'<text x="{_STACK_LEFT + _STACK_WIDTH / 2:.0f}" y="{panel.top + panel.height + 42:.0f}" '
        'text-anchor="middle" font-family="Arial, sans-serif" font-size="13" '
        f'fill="#0f172a">{escape(label)}</text>'
    )


def _section_title_svg(title: str, y_pos: float) -> list[str]:
    return [
        f'<text x="{_SUMMARY_LEFT + 14:.0f}" y="{y_pos:.0f}" font-family="Arial, sans-serif" '
        f'font-size="14" font-weight="700" fill="#0f172a">{escape(title)}</text>'
    ]


def _timing_summary_svg(projection: Mapping[str, object], top: float) -> list[str]:
    timing = _timing_summary(projection)
    rows = (
        ("IO", f'{timing["io"]:.1f} BTDC', "#2563eb"),
        ("IC", f'{timing["ic"]:.1f} ABDC', "#2563eb"),
        ("EO", f'{timing["eo"]:.1f} BBDC', "#dc2626"),
        ("EC", f'{timing["ec"]:.1f} ATDC', "#dc2626"),
        ("LSA", f'{timing["lsa"]:.1f}', "#0f172a"),
        ("Intake CL", f'{timing["intake_centerline"]:.1f} ATDC', "#2563eb"),
        ("Exhaust CL", f'{timing["exhaust_centerline"]:.1f} BTDC', "#dc2626"),
    )
    return _key_value_rows(rows, top, row_gap=18.0)


def _overlap_summary_svg(rows: Sequence[_OverlapRow], top: float) -> list[str]:
    rendered_rows = tuple(
        (
            f'@ {row.lift_in:.3f} in',
            f'{row.degrees:.1f} deg{" est." if row.estimated else ""}',
            "#0f172a",
        )
        for row in rows
        if row.lift_in in (0.050, 0.020, 0.006)
    )
    return _key_value_rows(rendered_rows, top, row_gap=20.0)


def _duration_summary_svg(projection: Mapping[str, object], top: float) -> list[str]:
    intake = _profile_by_name(projection, "intake")
    exhaust = _profile_by_name(projection, "exhaust")
    rows = []
    for intake_row, exhaust_row in zip(
        _sequence_field(intake, "threshold_durations"),
        _sequence_field(exhaust, "threshold_durations"),
    ):
        intake_duration = _angle_degrees(_as_mapping(intake_row, "intake threshold row"), "duration")
        exhaust_duration = _angle_degrees(_as_mapping(exhaust_row, "exhaust threshold row"), "duration")
        threshold = _quantity_value(_as_mapping(intake_row, "threshold row"), "threshold")
        rows.append(
            (
                f'@ {threshold:.3f} in',
                f'I {intake_duration:.1f} / E {exhaust_duration:.1f}',
                "#0f172a",
            )
        )
    return _key_value_rows(tuple(rows), top, row_gap=18.0)


def _quality_summary_svg(metrics: _ProfileMetrics, top: float) -> list[str]:
    rows = (
        ("Confidence", f"{metrics.confidence_score:.0f}/100", "#0f172a"),
        ("Measured", f"{metrics.measured_pct:.0f}%", "#0f172a"),
        ("Inferred", f"{metrics.inferred_pct:.0f}%", "#0f172a"),
        ("Extrapolated", f"{metrics.extrapolated_pct:.0f}%", "#0f172a"),
    )
    return _key_value_rows(rows, top, row_gap=18.0)


def _validation_summary_svg(warnings: Sequence[str], top: float) -> list[str]:
    parts = []
    line_index = 0
    max_lines = 6
    truncated = False
    for warning_index, warning in enumerate(warnings):
        wrapped_lines = _wrap_text(warning, max_chars=47)
        for wrapped_index, line in enumerate(wrapped_lines):
            if line_index >= max_lines:
                truncated = True
                break
            y_pos = top + line_index * 14.0
            prefix = "- " if wrapped_index == 0 else "  "
            parts.append(
                f'<text x="{_SUMMARY_LEFT + 18:.0f}" y="{y_pos:.0f}" font-family="Arial, sans-serif" '
                f'font-size="11" fill="#7f1d1d">{prefix}{escape(line)}</text>'
            )
            line_index += 1
        if truncated:
            break
        if warning_index < len(warnings) - 1 and line_index >= max_lines:
            truncated = True
            break
    if truncated:
        y_pos = top + line_index * 14.0
        parts.append(
            f'<text x="{_SUMMARY_LEFT + 18:.0f}" y="{y_pos:.0f}" font-family="Arial, sans-serif" '
            'font-size="11" fill="#7f1d1d">- More warnings in JSON projection</text>'
        )
    if not warnings:
        parts.append(
            f'<text x="{_SUMMARY_LEFT + 18:.0f}" y="{top:.0f}" font-family="Arial, sans-serif" '
            'font-size="11" fill="#166534">- Timing constraints satisfied</text>'
        )
    return parts


def _key_value_rows(
    rows: Sequence[tuple[str, str, str]],
    top: float,
    *,
    row_gap: float,
) -> list[str]:
    parts = []
    for index, (label, value, color) in enumerate(rows):
        y_pos = top + index * row_gap
        parts.append(
            f'<text x="{_SUMMARY_LEFT + 18:.0f}" y="{y_pos:.0f}" font-family="Arial, sans-serif" '
            f'font-size="12" fill="#334155">{escape(label)}</text>'
        )
        parts.append(
            f'<text x="{_SUMMARY_LEFT + _SUMMARY_WIDTH - 18:.0f}" y="{y_pos:.0f}" text-anchor="end" '
            f'font-family="Arial, sans-serif" font-size="12" font-weight="700" fill="{color}">{escape(value)}</text>'
        )
    return parts


def _provenance_legend_svg(legend: Mapping[str, object]) -> list[str]:
    parts = []
    labels = (
        ("MEASURED", "MEASURED"),
        ("INFERRED", "INFERRED"),
        ("EXTRAPOLATED", "EXTRAPOLATED"),
        ("UNDECIDABLE", "UNDECIDABLE"),
    )
    for index, (key, label) in enumerate(labels):
        y_pos = 906.0 + index * 20.0
        style = _mapping_field(legend, key)
        if _bool_field(style, "draw_line"):
            dasharray = _dasharray(_string_field(style, "stroke"))
            dash_attr = f' stroke-dasharray="{dasharray}"' if dasharray else ""
            parts.append(
                f'<line x1="420" y1="{y_pos:.0f}" x2="464" y2="{y_pos:.0f}" stroke="#0f172a" '
                f'stroke-width="2.5" stroke-opacity="{_float_field(style, "opacity"):.2f}"{dash_attr} '
                'stroke-linecap="round"/>'
            )
        else:
            parts.append(
                f'<rect x="420" y="{y_pos - 8:.0f}" width="44" height="12" fill="none" stroke="#0f172a"/>'
            )
        parts.append(
            f'<text x="478" y="{y_pos + 4:.0f}" font-family="Arial, sans-serif" font-size="12" '
            f'fill="#1e293b">{label}</text>'
        )
    parts.append('<rect x="710" y="892" width="30" height="12" fill="#2563eb" fill-opacity="0.10"/>')
    parts.append('<text x="750" y="903" font-family="Arial, sans-serif" font-size="12" fill="#1e293b">95% band</text>')
    parts.append('<rect x="710" y="916" width="30" height="12" fill="#2563eb" fill-opacity="0.05"/>')
    parts.append('<text x="750" y="927" font-family="Arial, sans-serif" font-size="12" fill="#1e293b">50% band</text>')
    return parts


def _legend_notes_svg() -> list[str]:
    notes = (
        "0-360 view; 180 = TDC overlap",
        "Solid/dashed/dotted = measured/inferred/extrapolated",
        "Bands show 95% and 50% confidence",
        "Dashed markers are hard @0.050 in crossings",
        "720 overview carries off-window events",
    )
    return [
        f'<text x="956" y="{902 + index * 15:.0f}" font-family="Arial, sans-serif" '
        f'font-size="11" fill="#1e293b">- {escape(note)}</text>'
        for index, note in enumerate(notes)
    ]


def _timing_events(projection: Mapping[str, object]) -> tuple[_TimingEvent, ...]:
    events = _hard_timing_event_degrees(projection)
    return (
        _TimingEvent(
            f'IO @ 0.050 in {_display_deg(events["IO"]):.1f} deg',
            _display_deg(events["IO"]),
            "#2563eb",
            "top",
        ),
        _TimingEvent(
            f'EC @ 0.050 in {_display_deg(events["EC"]):.1f} deg',
            _display_deg(events["EC"]),
            "#dc2626",
            "bottom",
        ),
    )


def _full_cycle_timing_events(projection: Mapping[str, object]) -> tuple[_FullCycleEvent, ...]:
    events = _hard_timing_event_degrees(projection)
    return (
        _FullCycleEvent("IO", events["IO"], "#2563eb"),
        _FullCycleEvent("IC", events["IC"], "#2563eb"),
        _FullCycleEvent("EO", events["EO"], "#dc2626"),
        _FullCycleEvent("EC", events["EC"], "#dc2626"),
    )


def _timing_summary(projection: Mapping[str, object]) -> dict[str, float]:
    events = _hard_timing_event_degrees(projection)
    intake_open = events["IO"]
    intake_close = events["IC"]
    exhaust_open = events["EO"]
    exhaust_close = events["EC"]
    intake_centerline = _arc_midpoint(intake_open, intake_close)
    exhaust_centerline = _arc_midpoint(exhaust_open, exhaust_close)
    exhaust_centerline_btdc = 720.0 - exhaust_centerline
    return {
        "io": 720.0 - intake_open,
        "ic": intake_close - 180.0,
        "eo": 540.0 - exhaust_open,
        "ec": exhaust_close,
        "intake_centerline": intake_centerline,
        "exhaust_centerline": exhaust_centerline_btdc,
        "lsa": (intake_centerline + exhaust_centerline_btdc) / 2.0,
    }


def _hard_timing_event_degrees(projection: Mapping[str, object]) -> dict[str, float]:
    intake = _profile_by_name(projection, "intake")
    exhaust = _profile_by_name(projection, "exhaust")
    intake_events = _events_for_threshold(intake, 0.050)
    exhaust_events = _events_for_threshold(exhaust, 0.050)
    return {
        "IO": _event_before_tdc(intake_events),
        "IC": _event_after_bdc(intake_events),
        "EO": _event_before_bdc(exhaust_events),
        "EC": _event_after_tdc(exhaust_events),
    }


def _overlap_rows(projection: Mapping[str, object]) -> tuple[_OverlapRow, ...]:
    intake = _profile_by_name(projection, "intake")
    exhaust = _profile_by_name(projection, "exhaust")
    rows = []
    for lift_in in (0.050, 0.020, 0.006):
        intake_events = _events_for_threshold(intake, lift_in)
        exhaust_events = _events_for_threshold(exhaust, lift_in)
        intake_open_btdc = 720.0 - _event_before_tdc(intake_events)
        exhaust_close_atdc = _event_after_tdc(exhaust_events)
        rows.append(
            _OverlapRow(
                lift_in=lift_in,
                degrees=intake_open_btdc + exhaust_close_atdc,
                estimated=lift_in != 0.050,
            )
        )
    return tuple(rows)


def _profile_metrics(projection: Mapping[str, object]) -> _ProfileMetrics:
    totals = {"MEASURED": 0.0, "INFERRED": 0.0, "EXTRAPOLATED": 0.0}
    for raw_profile in _sequence_field(projection, "profiles"):
        profile = _as_mapping(raw_profile, "profile")
        lift_series = _mapping_field(_mapping_field(profile, "series"), "lift")
        for raw_segment in _sequence_field(lift_series, "segments"):
            segment = _as_mapping(raw_segment, "lift segment")
            provenance = segment.get("provenance")
            if provenance not in totals:
                continue
            totals[provenance] += max(
                _float_field(segment, "end_deg") - _float_field(segment, "start_deg"),
                0.0,
            )
    total_degrees = max(sum(totals.values()), 1e-9)
    measured_pct = totals["MEASURED"] / total_degrees * 100.0
    inferred_pct = totals["INFERRED"] / total_degrees * 100.0
    extrapolated_pct = totals["EXTRAPOLATED"] / total_degrees * 100.0
    confidence_score = measured_pct + inferred_pct * 0.55 + extrapolated_pct * 0.15
    return _ProfileMetrics(confidence_score, measured_pct, inferred_pct, extrapolated_pct)


def _validation_warnings(
    projection: Mapping[str, object],
    metrics: _ProfileMetrics,
) -> tuple[str, ...]:
    warnings = []
    if metrics.confidence_score < 45.0:
        warnings.append("Profile confidence is low")
    for raw_profile in _sequence_field(projection, "profiles"):
        profile = _as_mapping(raw_profile, "profile")
        profile_name = _string_field(profile, "name").title()
        for raw_warning in _sequence_field(profile, "quality_warnings"):
            warning = _as_mapping(raw_warning, "quality warning")
            severity = warning.get("severity")
            if severity == "info":
                continue
            message = _string_field(warning, "message")
            warnings.append(f"{profile_name}: {message}")
    return tuple(warnings)


def _profile_by_name(projection: Mapping[str, object], name: str) -> Mapping[str, object]:
    for raw_profile in _sequence_field(projection, "profiles"):
        profile = _as_mapping(raw_profile, "profile")
        if _string_field(profile, "name") == name:
            return profile
    raise ValueError(f"projection missing {name!r} profile")


def _events_for_threshold(profile: Mapping[str, object], threshold_in: float) -> tuple[float, ...]:
    for raw_row in _sequence_field(profile, "threshold_durations"):
        row = _as_mapping(raw_row, "threshold row")
        threshold = _quantity_value(row, "threshold")
        if abs(threshold - threshold_in) <= 1e-9:
            return tuple(
                _float_field(_as_mapping(raw_event, "threshold event"), "degrees")
                for raw_event in _sequence_field(row, "events")
            )
    raise ValueError(f"profile missing threshold duration for {threshold_in:.3f} in")


def _event_before_tdc(events: Sequence[float]) -> float:
    return max(events, key=lambda degrees: degrees if degrees > 540.0 else -math.inf)


def _event_after_tdc(events: Sequence[float]) -> float:
    return min(events, key=lambda degrees: degrees if degrees < 180.0 else math.inf)


def _event_before_bdc(events: Sequence[float]) -> float:
    return max((degrees for degrees in events if 360.0 <= degrees <= 540.0), default=events[0])


def _event_after_bdc(events: Sequence[float]) -> float:
    return min((degrees for degrees in events if 180.0 <= degrees <= 360.0), default=events[0])


def _arc_midpoint(start_deg: float, end_deg: float) -> float:
    if end_deg < start_deg:
        end_deg += _CYCLE_DEGREES
    return ((start_deg + end_deg) / 2.0) % _CYCLE_DEGREES


def _angle_degrees(row: Mapping[str, object], key: str) -> float:
    return _float_field(_mapping_field(row, key), "degrees")


def _quantity_value(row: Mapping[str, object], key: str) -> float:
    return _float_field(_mapping_field(row, key), "value")


def _path_data(
    points: Sequence[_Point],
    y_min: float,
    y_max: float,
    panel: _Panel,
    *,
    full_cycle: bool,
) -> str:
    commands = [
        f"{'M' if index == 0 else 'L'} "
        f"{(_full_x_px(point.display_deg) if full_cycle else _x_px(point.display_deg)):.2f} "
        f"{_y_px(point.y_value, y_min, y_max, panel):.2f}"
        for index, point in enumerate(points)
    ]
    return " ".join(commands)


def _band_path_data(
    points: Sequence[_Point],
    y_min: float,
    y_max: float,
    panel: _Panel,
    *,
    width: str,
) -> str:
    band_points = []
    for point in points:
        half_width = point.p95_half_width if width == "p95" else point.p50_half_width
        if half_width is not None:
            band_points.append((point, half_width))
    if len(band_points) < 2:
        return ""
    upper = [
        f"{'M' if index == 0 else 'L'} {_x_px(point.display_deg):.2f} "
        f"{_y_px(point.y_value + half_width, y_min, y_max, panel):.2f}"
        for index, (point, half_width) in enumerate(band_points)
    ]
    lower = [
        f"L {_x_px(point.display_deg):.2f} "
        f"{_y_px(point.y_value - half_width, y_min, y_max, panel):.2f}"
        for point, half_width in reversed(band_points)
    ]
    return " ".join((*upper, *lower, "Z"))


def _display_deg(crank_deg: float) -> float:
    normalized = crank_deg % _CYCLE_DEGREES
    if normalized >= _OVERLAP_WINDOW_START_DEG:
        return normalized - _OVERLAP_WINDOW_START_DEG
    return normalized + (_CYCLE_DEGREES - _OVERLAP_WINDOW_START_DEG)


def _in_centered_window(display_deg: float) -> bool:
    return _MAIN_X_MIN <= display_deg <= _MAIN_X_MAX


def _x_px(display_deg: float) -> float:
    ratio = (display_deg - _MAIN_X_MIN) / (_MAIN_X_MAX - _MAIN_X_MIN)
    return _STACK_LEFT + min(max(ratio, 0.0), 1.0) * _STACK_WIDTH


def _threshold_label_baselines(panel: _Panel, y_max: float) -> dict[float, float]:
    label_rows = [
        (lift_in, _y_px(lift_in, 0.0, y_max, panel) + 4.0)
        for lift_in in _THRESHOLD_LIFTS
        if lift_in <= y_max
    ]
    sorted_rows = sorted(label_rows, key=lambda row: row[1])
    min_gap = 14.0
    min_y = panel.top + 14.0
    max_y = panel.top + panel.height - 8.0
    placed: list[tuple[float, float]] = []
    previous = min_y - min_gap
    for lift_in, desired in sorted_rows:
        y_pos = min(max(desired, previous + min_gap), max_y)
        placed.append((lift_in, y_pos))
        previous = y_pos
    if placed and placed[-1][1] > max_y:
        overflow = placed[-1][1] - max_y
        placed = [(lift_in, y_pos - overflow) for lift_in, y_pos in placed]
    for index in range(len(placed) - 2, -1, -1):
        current_lift, current_y = placed[index]
        next_y = placed[index + 1][1]
        placed[index] = (current_lift, min(current_y, next_y - min_gap))
    return dict(placed)


def _full_x_px(crank_deg: float) -> float:
    return _STACK_LEFT + (crank_deg / _CYCLE_DEGREES) * _STACK_WIDTH


def _y_px(value: float, y_min: float, y_max: float, panel: _Panel) -> float:
    ratio = (y_max - value) / (y_max - y_min)
    return panel.top + min(max(ratio, 0.0), 1.0) * panel.height


def _tick_values(y_min: float, y_max: float) -> tuple[float, ...]:
    if y_min < 0.0:
        return (y_min, 0.0, y_max)
    return (0.0, y_max / 2.0, y_max)


def _max_y(profiles: Sequence[_ProfileSeries]) -> float:
    return max(
        (
            point.y_value
            for profile in profiles
            for segment in profile.segments
            for point in segment.points
        ),
        default=0.0,
    )


def _nice_lift_max(max_lift: float) -> float:
    if max_lift <= 0.0:
        return 0.1
    return max(0.1, math.ceil(max_lift * 10.0) / 10.0)


def _symmetric_range(profiles: Sequence[_ProfileSeries]) -> tuple[float, float]:
    max_abs = max(
        (
            abs(point.y_value)
            for profile in profiles
            for segment in profile.segments
            for point in segment.points
        ),
        default=0.0,
    )
    if max_abs <= 0.0:
        max_abs = 1e-6
    return -max_abs, max_abs


def _wrap_text(text: str, *, max_chars: int) -> tuple[str, ...]:
    words = text.split()
    if not words:
        return ("",)
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if len(candidate) > max_chars:
            lines.append(current)
            current = word
        else:
            current = candidate
    lines.append(current)
    return tuple(lines)


def _series_label(query: str) -> str:
    labels = {
        "velocity": "Velocity (in/deg)",
        "acceleration": "Acceleration (in/deg^2)",
        "jerk": "Jerk (in/deg^3)",
    }
    return labels[query]


def _confidence_half_width(point: Mapping[str, object], key: str) -> float | None:
    confidence = point.get("confidence")
    if not isinstance(confidence, Mapping):
        return None
    half_width = confidence.get(key)
    if isinstance(half_width, int | float):
        return float(half_width)
    return None


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
