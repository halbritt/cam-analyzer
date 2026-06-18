from __future__ import annotations

import json
from xml.etree import ElementTree as ET

import pytest

from cam_analyzer.cli import render_chart_projection_from_card_data, render_svg_chart_from_card_data
from cam_analyzer.quantity import Angle, Inch, inferred
from cam_analyzer.sources.cam_card import CamCard, profiles_from_cam_card
from cam_analyzer.visualization import (
    canonical_to_overlap_display,
    is_primary_overlap_display_angle,
    overlap_display_to_canonical,
)

_SVG_NAMESPACE = "{http://www.w3.org/2000/svg}"
_CHECKING_LIFT_IN = 0.050
_REFERENCE_CARD = {
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
}


def test_event_canonical_coordinates() -> None:
    events = _known_event_coordinates()

    assert events["IO"] == pytest.approx(710.5)
    assert events["IC"] == pytest.approx(228.5)
    assert events["EO"] == pytest.approx(492.5)
    assert events["EC"] == pytest.approx(18.5)


def test_overlap_centered_projection() -> None:
    events = _known_event_coordinates()
    display_events = {
        event: canonical_to_overlap_display(canonical_angle)
        for event, canonical_angle in events.items()
    }

    assert display_events["IO"] == pytest.approx(-9.5)
    assert display_events["EC"] == pytest.approx(18.5)
    assert is_primary_overlap_display_angle(display_events["IO"])
    assert is_primary_overlap_display_angle(display_events["EC"])
    assert display_events["IC"] == pytest.approx(228.5)
    assert display_events["EO"] == pytest.approx(-227.5)
    assert not is_primary_overlap_display_angle(display_events["IC"])
    assert not is_primary_overlap_display_angle(display_events["EO"])


def test_overlap_duration_050() -> None:
    events = _known_event_coordinates()
    overlap_start = canonical_to_overlap_display(events["IO"])
    overlap_end = canonical_to_overlap_display(events["EC"])

    assert overlap_start == pytest.approx(-9.5)
    assert overlap_end == pytest.approx(18.5)
    assert overlap_end - overlap_start == pytest.approx(28.0)


def test_primary_view_contains_overlap_events() -> None:
    root = _svg_root()
    primary_events = _primary_event_elements(root)
    overlap_band = _overlap_band_element(root)

    assert primary_events["IO"].attrib["data-display-angle-deg"] == "-9.5"
    assert primary_events["IO"].attrib["data-canonical-angle-deg"] == "710.5"
    assert primary_events["EC"].attrib["data-display-angle-deg"] == "18.5"
    assert primary_events["EC"].attrib["data-canonical-angle-deg"] == "18.5"
    assert float(overlap_band.attrib["data-display-start-deg"]) == pytest.approx(-9.5)
    assert float(overlap_band.attrib["data-display-end-deg"]) == pytest.approx(18.5)
    assert float(overlap_band.attrib["data-display-start-deg"]) < 0.0
    assert float(overlap_band.attrib["data-display-end-deg"]) > 0.0


def test_primary_view_excludes_non_overlap_events() -> None:
    svg = _svg_text()
    primary_events = _primary_event_elements(ET.fromstring(svg))

    assert set(primary_events) == {"IO", "EC"}
    assert "IC @ 0.050 in +48.5" not in svg
    assert "EO @ 0.050 in -47.5" not in svg


def test_no_shifted_coordinates_in_labels() -> None:
    svg = _svg_text()

    assert "IO @ 0.050 in 170.5" not in svg
    assert "EC @ 0.050 in 198.5" not in svg


def test_lift_crossings_at_050() -> None:
    profiles = profiles_from_cam_card(CamCard.wr250r_reference())
    checking_lift = inferred(_CHECKING_LIFT_IN, Inch, "valve_side")
    intake_events = [event.degrees for event in profiles.intake.events_at_lift(checking_lift)]
    exhaust_events = [event.degrees for event in profiles.exhaust.events_at_lift(checking_lift)]
    intake_open = max(degrees for degrees in intake_events if degrees > 540.0)
    exhaust_close = min(degrees for degrees in exhaust_events if degrees < 180.0)

    assert canonical_to_overlap_display(intake_open) == pytest.approx(-9.5, abs=0.001)
    assert float(profiles.intake.lift_at(Angle.crank(intake_open))) == pytest.approx(
        _CHECKING_LIFT_IN,
        abs=0.001,
    )
    assert canonical_to_overlap_display(exhaust_close) == pytest.approx(18.5, abs=0.001)
    assert float(profiles.exhaust.lift_at(Angle.crank(exhaust_close))) == pytest.approx(
        _CHECKING_LIFT_IN,
        abs=0.001,
    )


def test_720_overview_event_positions() -> None:
    overview_events = _overview_event_elements(_svg_root())

    assert overview_events["IO"].attrib["data-canonical-angle-deg"] == "710.5"
    assert overview_events["EC"].attrib["data-canonical-angle-deg"] == "18.5"
    assert overview_events["IC"].attrib["data-canonical-angle-deg"] == "228.5"
    assert overview_events["EO"].attrib["data-canonical-angle-deg"] == "492.5"
    for event, element in overview_events.items():
        expected_x = 96.0 + _known_event_coordinates()[event] / 720.0 * 1024.0
        assert float(element.attrib["x1"]) == pytest.approx(expected_x, abs=0.01)


def test_axis_label_semantics() -> None:
    svg = _svg_text()

    assert "Crank angle relative to TDC overlap (deg)" in svg
    assert "Overlap-centered crank window (deg; 180 = TDC overlap)" not in svg
    assert "Primary engineering view: 0-360" not in svg


def test_projection_round_trip() -> None:
    for canonical_angle in _known_event_coordinates().values():
        display_angle = canonical_to_overlap_display(canonical_angle)

        assert overlap_display_to_canonical(display_angle) == pytest.approx(canonical_angle % 720.0)


def _known_event_coordinates() -> dict[str, float]:
    projection = _projection()
    intake_events = _threshold_events(_profile_by_name(projection, "intake"))
    exhaust_events = _threshold_events(_profile_by_name(projection, "exhaust"))
    return {
        "IO": max(degrees for degrees in intake_events if degrees > 540.0),
        "IC": min(degrees for degrees in intake_events if 180.0 <= degrees <= 360.0),
        "EO": max(degrees for degrees in exhaust_events if 360.0 <= degrees <= 540.0),
        "EC": min(degrees for degrees in exhaust_events if degrees < 180.0),
    }


def _projection() -> dict[str, object]:
    return json.loads(
        render_chart_projection_from_card_data(
            _REFERENCE_CARD,
            approximate_derivatives=False,
            chart_step_deg=20.0,
        )
    )


def _profile_by_name(projection: dict[str, object], name: str) -> dict[str, object]:
    profiles = projection["profiles"]
    assert isinstance(profiles, list)
    for profile in profiles:
        assert isinstance(profile, dict)
        if profile["name"] == name:
            return profile
    raise AssertionError(f"missing profile {name}")


def _threshold_events(profile: dict[str, object]) -> tuple[float, ...]:
    threshold_rows = profile["threshold_durations"]
    assert isinstance(threshold_rows, list)
    for row in threshold_rows:
        assert isinstance(row, dict)
        threshold = row["threshold"]
        assert isinstance(threshold, dict)
        if threshold["value"] == _CHECKING_LIFT_IN:
            events = row["events"]
            assert isinstance(events, list)
            return tuple(float(event["degrees"]) for event in events if isinstance(event, dict))
    raise AssertionError("missing 0.050 threshold row")


def _svg_text() -> str:
    return render_svg_chart_from_card_data(
        _REFERENCE_CARD,
        approximate_derivatives=False,
        chart_step_deg=20.0,
    )


def _svg_root() -> ET.Element:
    return ET.fromstring(_svg_text())


def _primary_event_elements(root: ET.Element) -> dict[str, ET.Element]:
    return {
        element.attrib["data-primary-event"]: element
        for element in root.iter(f"{_SVG_NAMESPACE}line")
        if "data-primary-event" in element.attrib
    }


def _overview_event_elements(root: ET.Element) -> dict[str, ET.Element]:
    return {
        element.attrib["data-event"]: element
        for element in root.iter(f"{_SVG_NAMESPACE}line")
        if "data-event" in element.attrib
    }


def _overlap_band_element(root: ET.Element) -> ET.Element:
    for element in root.iter(f"{_SVG_NAMESPACE}rect"):
        if element.attrib.get("data-overlap-threshold") == "0.050":
            return element
    raise AssertionError("missing overlap band")
