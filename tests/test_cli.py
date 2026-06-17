"""Tests for the ``cam-analyze`` CLI (source → profile → report wiring)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cam_analyzer.cli import main, render_report_from_card_data

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


def test_main_with_reference_flag_prints_report(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["--reference"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "WR250R reference" in captured.out
    assert "Dynamic compression ratio:" in captured.out


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
