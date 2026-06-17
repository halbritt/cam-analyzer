from __future__ import annotations

import json

import pytest

from cam_analyzer.cli import render_chart_projection_from_card_data
from cam_analyzer.visualization.svg import render_valve_lift_svg


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
