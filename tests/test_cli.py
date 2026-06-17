"""Tests for the ``cam-analyze`` CLI (source → profile → report wiring)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cam_analyzer.cli import (
    main,
    render_chart_projection_from_card_data,
    render_report_from_card_data,
    render_svg_chart_from_card_data,
)

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
    "engine": {
        "bore_mm": 77.0,
        "stroke_mm": 53.6,
        "rod_length_mm": 96.9,
        "static_compression_ratio": 12.8,
    },
}


def test_render_report_from_card_data_contains_the_expected_sections() -> None:
    report = render_report_from_card_data(_REFERENCE_CARD, approximate_derivatives=False)

    assert "# Test card" in report
    assert "## Timing" in report
    assert "Lobe separation angle:" in report
    assert "## Dynamic compression" in report
    assert "## Piston-to-valve" in report
    assert "## Spring safety" in report
    # Cam-card evidence can't justify cliff verdicts — the report says so, loudly.
    assert "UNDECIDABLE FROM CAM CARD" in report


def test_render_report_without_engine_omits_dynamic_compression() -> None:
    card = {k: v for k, v in _REFERENCE_CARD.items() if k != "engine"}

    report = render_report_from_card_data(card, approximate_derivatives=False)

    assert "## Dynamic compression" not in report
    assert "## Timing" in report


def test_render_chart_projection_from_card_data_contains_stamped_samples() -> None:
    projection_json = render_chart_projection_from_card_data(
        _REFERENCE_CARD,
        approximate_derivatives=False,
        chart_step_deg=20.0,
    )
    projection = json.loads(projection_json)

    assert projection["schema"] == "cam_analyzer.visualization_projection.v1"
    assert [profile["name"] for profile in projection["profiles"]] == ["intake", "exhaust"]
    assert projection["implemented_subset"] == [
        "static_json_projection",
        "provenance_rendering_grammar",
        "sampled_c5_series",
        "refusal_segments",
        "static_svaj_svg",
        "threshold_duration_table",
        "confidence_bands",
        "profile_quality_warnings",
        "svaj_stack_svg",
    ]
    assert "echarts_ssr_adapter" in projection["deferred"]
    assert "chart_suite_svg_export" in projection["deferred"]
    assert projection["provenance_legend"]["INFERRED"]["stroke"] == "short-dash"
    assert projection["provenance_legend"]["EXTRAPOLATED"]["stroke"] == "dotted"
    assert projection["provenance_legend"]["UNDECIDABLE"]["draw_line"] is False

    intake = projection["profiles"][0]
    assert intake["summary"]["max_lift"]["provenance"] == "EXTRAPOLATED"
    assert intake["events_at_lift"][0]["duration"]["degrees"] == pytest.approx(238.0)

    intake_lift = intake["series"]["lift"]
    assert intake_lift["query"] == "lift"
    assert intake_lift["samples"][0]["answer"]["kind"] == "quantity"
    assert intake_lift["samples"][0]["answer"]["unit"] == "inch"
    assert "provenance" in intake_lift["samples"][0]["answer"]
    assert {segment["provenance"] for segment in intake_lift["segments"]} >= {
        "INFERRED",
        "EXTRAPOLATED",
    }
    acceleration_samples = intake["series"]["acceleration"]["samples"]
    assert all(sample["answer"]["kind"] == "quantity" for sample in acceleration_samples)
    assert all(sample["answer"]["provenance"] == "EXTRAPOLATED" for sample in acceleration_samples)


def test_render_svg_chart_from_card_data_draws_the_test_cam_lift_overlay() -> None:
    svg = render_svg_chart_from_card_data(
        _REFERENCE_CARD,
        approximate_derivatives=False,
        chart_step_deg=20.0,
    )

    assert svg.startswith("<svg ")
    assert "Test card" in svg
    assert "Intake" in svg
    assert "Exhaust" in svg
    assert "INFERRED" in svg
    assert "EXTRAPOLATED" in svg
    assert "Timing Summary (@ 0.050 in)" in svg
    assert "Overlap Summary" in svg
    assert "IO @ 0.050 in -9.5" in svg
    assert 'stroke-dasharray="7 5"' in svg
    assert 'stroke-dasharray="1 6"' in svg
    assert "Renderer draws only sampled boundary answers" in svg


def test_main_with_reference_flag_prints_report(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["--reference"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "WR250R reference" in captured.out
    assert "Dynamic compression ratio:" in captured.out


def test_main_with_reference_flag_can_print_chart_projection(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["--reference", "--charts", "json", "--chart-step-deg", "360"])

    captured = capsys.readouterr()
    assert exit_code == 0
    projection = json.loads(captured.out)
    assert projection["schema"] == "cam_analyzer.visualization_projection.v1"
    assert "Dynamic compression ratio:" not in captured.out


def test_main_with_reference_flag_can_print_svg_chart(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["--reference", "--charts", "svg", "--chart-step-deg", "360"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.startswith("<svg ")
    assert "WR250R reference" in captured.out
    assert "Dynamic compression ratio:" not in captured.out


def test_main_charts_json_rejects_non_positive_step(
    capsys: pytest.CaptureFixture[str],
) -> None:
    exit_code = main(["--reference", "--charts", "json", "--chart-step-deg", "0"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "--chart-step-deg must be positive" in captured.err


def test_main_with_card_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    card_path = tmp_path / "card.json"
    card_path.write_text(json.dumps(_REFERENCE_CARD))

    exit_code = main([str(card_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "# Test card" in captured.out


def test_main_missing_file_reports_error(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["/nonexistent/card.json"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "not found" in captured.err


def test_main_invalid_card_reports_error(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    card_path = tmp_path / "bad.json"
    card_path.write_text(json.dumps({"intake": {"valve_lift_in": 0.360}}))  # missing fields/exhaust

    exit_code = main([str(card_path)])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "invalid cam card" in captured.err


def test_main_incoherent_card_is_refused(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # advertised < duration@0.050" is the advertised_lt_050 trap — the source layer
    # refuses to construct, and the CLI surfaces that as a clean error, not a crash.
    incoherent = json.loads(json.dumps(_REFERENCE_CARD))
    incoherent["intake"]["advertised_duration_deg"] = 230.0  # < duration_050_deg 238.0

    card_path = tmp_path / "incoherent.json"
    card_path.write_text(json.dumps(incoherent))

    exit_code = main([str(card_path)])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "invalid cam card" in captured.err
