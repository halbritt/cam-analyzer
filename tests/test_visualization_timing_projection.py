from __future__ import annotations

import json
from xml.etree import ElementTree as ET

import pytest

from cam_analyzer.cli import render_chart_projection_from_card_data, render_svg_chart_from_card_data
from cam_analyzer.quantity import Angle, Inch, inferred
from cam_analyzer.sources.cam_card import CamCard, profiles_from_cam_card
from cam_analyzer.visualization import (
    PRIMARY_OVERLAP_RELATIVE_MAX_DEG,
    PRIMARY_OVERLAP_RELATIVE_MIN_DEG,
    canonical_to_overlap_relative,
    is_primary_overlap_relative_angle,
    overlap_relative_to_canonical,
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
    relative_events = {
        event: canonical_to_overlap_relative(canonical_angle)
        for event, canonical_angle in events.items()
    }

    assert relative_events["EO"] == pytest.approx(-227.5)
    assert relative_events["IO"] == pytest.approx(-9.5)
    assert relative_events["EC"] == pytest.approx(18.5)
    assert relative_events["IC"] == pytest.approx(228.5)
    assert all(is_primary_overlap_relative_angle(angle) for angle in relative_events.values())


def test_primary_view_is_full_cycle_overlap_relative() -> None:
    projection = _projection()
    sample_degrees = tuple(float(degrees) for degrees in projection["sample_degrees"])
    relative_degrees = tuple(canonical_to_overlap_relative(degrees) for degrees in sample_degrees)

    assert PRIMARY_OVERLAP_RELATIVE_MIN_DEG == pytest.approx(-360.0)
    assert PRIMARY_OVERLAP_RELATIVE_MAX_DEG == pytest.approx(360.0)
    assert PRIMARY_OVERLAP_RELATIVE_MAX_DEG - PRIMARY_OVERLAP_RELATIVE_MIN_DEG == pytest.approx(720.0)
    assert min(sample_degrees) == pytest.approx(0.0)
    assert max(sample_degrees) == pytest.approx(720.0)
    assert len(relative_degrees) == len(sample_degrees)


def test_overlap_duration_050() -> None:
    events = _known_event_coordinates()
    overlap_start = canonical_to_overlap_relative(events["IO"])
    overlap_end = canonical_to_overlap_relative(events["EC"])

    assert overlap_start == pytest.approx(-9.5)
    assert overlap_end == pytest.approx(18.5)
    assert overlap_end - overlap_start == pytest.approx(28.0)


def test_primary_view_contains_overlap_events() -> None:
    root = _svg_root()
    primary_events = _primary_event_elements(root)
    overlap_band = _overlap_band_element(root)

    assert set(primary_events) == {"EO", "IO", "EC", "IC"}
    assert primary_events["EO"].attrib["data-overlap-relative-angle-deg"] == "-227.5"
    assert primary_events["EO"].attrib["data-canonical-angle-deg"] == "492.5"
    assert primary_events["IO"].attrib["data-overlap-relative-angle-deg"] == "-9.5"
    assert primary_events["IO"].attrib["data-canonical-angle-deg"] == "710.5"
    assert primary_events["EC"].attrib["data-overlap-relative-angle-deg"] == "18.5"
    assert primary_events["EC"].attrib["data-canonical-angle-deg"] == "18.5"
    assert primary_events["IC"].attrib["data-overlap-relative-angle-deg"] == "228.5"
    assert primary_events["IC"].attrib["data-canonical-angle-deg"] == "228.5"
    assert float(overlap_band.attrib["data-overlap-start-deg"]) == pytest.approx(-9.5)
    assert float(overlap_band.attrib["data-overlap-end-deg"]) == pytest.approx(18.5)
    assert float(overlap_band.attrib["data-overlap-start-deg"]) < 0.0
    assert float(overlap_band.attrib["data-overlap-end-deg"]) > 0.0


def test_primary_view_does_not_label_card_offsets_as_relative_angles() -> None:
    svg = _svg_text()
    primary_events = _primary_event_elements(ET.fromstring(svg))

    assert "IC @ 0.050 in +48.5" not in svg
    assert "EO @ 0.050 in -47.5" not in svg
    assert primary_events["IC"].attrib["data-overlap-relative-angle-deg"] == "228.5"
    assert primary_events["EO"].attrib["data-overlap-relative-angle-deg"] == "-227.5"


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

    assert canonical_to_overlap_relative(intake_open) == pytest.approx(-9.5, abs=0.001)
    assert float(profiles.intake.lift_at(Angle.crank(intake_open))) == pytest.approx(
        _CHECKING_LIFT_IN,
        abs=0.001,
    )
    assert canonical_to_overlap_relative(exhaust_close) == pytest.approx(18.5, abs=0.001)
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
    assert "Primary engineering view: -180 to +180" not in svg
    assert "Primary engineering view: -360 to +360 crank degrees" in svg


def test_projection_round_trip() -> None:
    for canonical_angle in _known_event_coordinates().values():
        relative_angle = canonical_to_overlap_relative(canonical_angle)

        assert overlap_relative_to_canonical(relative_angle) == pytest.approx(canonical_angle % 720.0)


def test_primary_and_secondary_use_equivalent_lift_samples() -> None:
    projection = _projection()
    for profile in projection["profiles"]:
        assert isinstance(profile, dict)
        lift_series = profile["series"]["lift"]
        assert isinstance(lift_series, dict)
        samples = lift_series["samples"]
        assert isinstance(samples, list)
        secondary_values = {
            float(sample["crank_deg"]): sample["answer"]["value"]
            for sample in samples
            if isinstance(sample, dict) and isinstance(sample.get("answer"), dict)
        }
        primary_values = {
            (canonical_to_overlap_relative(canonical_angle), canonical_angle): value
            for canonical_angle, value in secondary_values.items()
        }

        assert len(primary_values) == len(secondary_values)
        for (relative_angle, canonical_angle), primary_value in primary_values.items():
            assert is_primary_overlap_relative_angle(relative_angle)
            assert primary_value == secondary_values[canonical_angle]


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
