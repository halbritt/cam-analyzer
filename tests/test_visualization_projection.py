from __future__ import annotations

import json

import pytest

from cam_analyzer.analysis.projection import (
    ProfileProjectionInput,
    project_cam_profiles,
    projection_to_json,
)
from cam_analyzer.quantity import Inch, inferred
from cam_analyzer.sources.cam_card import CamCard, profiles_from_cam_card


def test_projection_samples_multiple_profiles_with_stamped_quantities() -> None:
    profiles = profiles_from_cam_card(CamCard.wr250r_reference())

    projection = project_cam_profiles(
        {"intake": profiles.intake, "exhaust": profiles.exhaust},
        sample_degrees=(0.0, 60.0, 109.5, 720.0),
    )

    assert projection["schema"] == "cam_analyzer.visualization_projection.v1"
    assert projection["cycle_degrees"] == 720.0
    assert projection["sample_degrees"] == [0.0, 60.0, 109.5, 720.0]
    assert [profile["name"] for profile in projection["profiles"]] == ["intake", "exhaust"]
    assert projection["provenance_legend"]["EXTRAPOLATED"]["line"] == "long_dash"

    intake = projection["profiles"][0]
    assert intake["summary"]["max_lift"]["kind"] == "quantity"
    assert intake["summary"]["max_lift"]["unit"] == "inch"
    assert intake["summary"]["max_lift"]["frame"] == "valve_side"

    lift_samples = intake["series"]["lift"]["samples"]
    nose_answer = lift_samples[2]["answer"]
    assert nose_answer["kind"] == "quantity"
    assert nose_answer["unit"] == "inch"
    assert nose_answer["frame"] == "valve_side"
    assert nose_answer["provenance"] == "EXTRAPOLATED"
    assert nose_answer["provenance_rank"] == 0


def test_refused_samples_become_no_line_segments_without_interpolation() -> None:
    intake = profiles_from_cam_card(CamCard.wr250r_reference()).intake

    projection = project_cam_profiles(
        {"intake": intake},
        sample_degrees=(60.0, 109.5, 120.0),
    )

    velocity = projection["profiles"][0]["series"]["velocity"]
    samples = velocity["samples"]
    refused_answer = samples[1]["answer"]
    assert refused_answer["kind"] == "refusal"
    assert refused_answer["requested"] == "derivative order 1 at 109.500 deg"
    assert "supports derivative order 0" in refused_answer["reason"]
    assert refused_answer["provenance"] == "EXTRAPOLATED"

    segments = velocity["segments"]
    assert [segment["kind"] for segment in segments] == ["quantity", "refusal", "quantity"]
    refused_segment = segments[1]
    assert refused_segment["draw_line"] is False
    assert refused_segment["style"]["line"] == "none"
    assert refused_segment["style"]["band_fill"] == "cross_hatch"
    assert refused_segment["points"] == [
        {
            "sample_index": 1,
            "crank_deg": 109.5,
            "value": None,
            "answer_kind": "refusal",
        }
    ]


def test_projection_includes_events_and_duration_when_threshold_lifts_are_supplied() -> None:
    intake = profiles_from_cam_card(CamCard.wr250r_reference()).intake
    checking_lift = inferred(0.050, Inch, "valve_side")

    projection = project_cam_profiles(
        (ProfileProjectionInput("intake", intake, role="intake"),),
        sample_degrees=(0.0, 720.0),
        event_lifts=(checking_lift,),
    )

    intake_projection = projection["profiles"][0]
    assert intake_projection["role"] == "intake"
    event_projection = intake_projection["events_at_lift"][0]
    assert event_projection["threshold"]["value"] == 0.050
    assert event_projection["threshold"]["provenance"] == "INFERRED"
    assert [event["degrees"] for event in event_projection["events"]] == pytest.approx(
        [228.5, 710.5],
        abs=0.001,
    )
    assert event_projection["duration"]["degrees"] == pytest.approx(238.0, abs=0.001)


def test_projection_to_json_is_deterministic_and_strict_json() -> None:
    intake = profiles_from_cam_card(CamCard.wr250r_reference()).intake

    first = project_cam_profiles({"intake": intake}, sample_degrees=(0.0, 60.0, 720.0))
    second = project_cam_profiles({"intake": intake}, sample_degrees=(0.0, 60.0, 720.0))

    first_json = projection_to_json(first)
    assert first_json == projection_to_json(second)
    assert json.loads(first_json) == first


def test_projection_validates_inputs() -> None:
    intake = profiles_from_cam_card(CamCard.wr250r_reference()).intake

    with pytest.raises(ValueError, match="at least one profile"):
        project_cam_profiles([])

    with pytest.raises(ValueError, match="duplicate profile name"):
        project_cam_profiles(
            (
                ProfileProjectionInput("intake", intake),
                ProfileProjectionInput("intake", intake),
            )
        )

    with pytest.raises(ValueError, match="strictly increasing"):
        project_cam_profiles({"intake": intake}, sample_degrees=(0.0, 0.0))
