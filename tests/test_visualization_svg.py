from __future__ import annotations

import json
from xml.etree import ElementTree as ET

import pytest

from cam_analyzer.cli import render_chart_projection_from_card_data
from cam_analyzer.visualization.svg import render_valve_lift_svg

_SVG_NAMESPACE = "{http://www.w3.org/2000/svg}"


def test_valve_lift_svg_uses_projection_provenance_styles() -> None:
    projection = json.loads(
        render_chart_projection_from_card_data(
            {
                "title": "Test card",
                "intake": {
                    "valve_lift_in": 0.360,
                    "advertised_duration_deg": 262.0,
                    "duration_050_deg": 238.0,
                    "lobe_center_deg": 109.5,
                    "lash_in": 0.006,
                },
                "exhaust": {
                    "valve_lift_in": 0.360,
                    "advertised_duration_deg": 270.0,
                    "duration_050_deg": 246.0,
                    "lobe_center_deg": 104.5,
                    "lash_in": 0.008,
                },
            },
            approximate_derivatives=False,
            chart_step_deg=30.0,
        )
    )

    svg = render_valve_lift_svg(projection, title="Test cam")

    assert '<title id="chart-title">Test cam</title>' in svg
    assert 'stroke="#2563eb"' in svg
    assert 'stroke="#dc2626"' in svg
    assert 'stroke-dasharray="6 4"' in svg
    assert 'stroke-dasharray="12 7"' in svg
    assert "cam_analyzer.visualization_projection.v1" in svg
    assert "Velocity (in/deg)" in svg
    assert "Acceleration (in/deg^2)" in svg
    assert "Jerk (in/deg^3)" in svg
    assert 'data-confidence="95"' in svg


def test_valve_lift_svg_footer_does_not_overlap_provenance_legend() -> None:
    projection = json.loads(
        render_chart_projection_from_card_data(
            {
                "title": "Test card",
                "intake": {
                    "valve_lift_in": 0.360,
                    "advertised_duration_deg": 262.0,
                    "duration_050_deg": 238.0,
                    "lobe_center_deg": 109.5,
                    "lash_in": 0.006,
                },
                "exhaust": {
                    "valve_lift_in": 0.360,
                    "advertised_duration_deg": 270.0,
                    "duration_050_deg": 246.0,
                    "lobe_center_deg": 104.5,
                    "lash_in": 0.008,
                },
            },
            approximate_derivatives=False,
            chart_step_deg=30.0,
        )
    )

    svg = render_valve_lift_svg(projection, title="Test cam")

    undecidable_y = _text_baseline(svg, "UNDECIDABLE")
    footer_y = _text_baseline(svg, "Projection:")
    assert footer_y >= undecidable_y + 24.0


def test_valve_lift_svg_refuses_projection_without_drawable_lift_segments() -> None:
    with pytest.raises(ValueError, match="no drawable segments"):
        render_valve_lift_svg(
            {
                "schema": "test",
                "provenance_legend": {},
                "profiles": [
                    {
                        "name": "intake",
                        "series": {
                            "lift": {
                                "segments": [
                                    {
                                        "draw_line": False,
                                        "provenance": None,
                                        "points": [],
                                    }
                                ]
                            }
                        },
                    }
                ],
            }
        )


def _text_baseline(svg: str, text_prefix: str) -> float:
    root = ET.fromstring(svg)
    for text_element in root.iter(f"{_SVG_NAMESPACE}text"):
        if "".join(text_element.itertext()).startswith(text_prefix):
            return float(text_element.attrib["y"])
    raise AssertionError(f"missing SVG text starting with {text_prefix!r}")
