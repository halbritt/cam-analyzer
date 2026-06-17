from __future__ import annotations

from cam_analyzer.analysis.profile_quality import (
    DEFAULT_THRESHOLD_LIFTS_IN,
    profile_quality_warnings,
    threshold_duration_table,
)
from cam_analyzer.sources.cam_card import CamCard, profiles_from_cam_card


def test_threshold_duration_table_reports_standard_cam_lifts() -> None:
    intake = profiles_from_cam_card(CamCard.wr250r_reference()).intake

    rows = threshold_duration_table(intake)

    assert [float(row.threshold) for row in rows] == list(DEFAULT_THRESHOLD_LIFTS_IN)
    durations = {float(row.threshold): row.duration.degrees for row in rows}
    assert durations[0.050] == 238.0
    assert durations[0.200] < durations[0.100] < durations[0.050]


def test_profile_quality_warnings_call_out_underconstrained_motion_law() -> None:
    intake = profiles_from_cam_card(CamCard.wr250r_reference()).intake

    warnings = profile_quality_warnings(intake)

    codes = {warning.code for warning in warnings}
    assert "underconstrained_reconstruction" in codes
    assert "implausibly_symmetric_lobe" in codes
    assert "model_derived_derivatives" in codes
