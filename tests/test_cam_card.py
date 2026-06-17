"""Validation tests for ``CamLobeSpec`` / ``CamCard`` (GitHub issue #4).

``CamLobeSpec.__post_init__`` must reject physically-impossible cam cards so the
downstream half-sine operator can never be built from nonsensical numbers. These
tests pin both the happy path (the Web Cam 81-651 reference card) and each
rejection clause.
"""

from __future__ import annotations

import pytest

from cam_analyzer.sources.cam_card import CamCard, CamLobeSpec


# (a) The reference card constructs and carries the expected per-side values.
def test_wr250r_reference_constructs_with_expected_values() -> None:
    card = CamCard.wr250r_reference()

    assert card.intake == CamLobeSpec(0.360, 262.0, 238.0, 109.5, 0.006)
    assert card.exhaust == CamLobeSpec(0.360, 270.0, 246.0, 104.5, 0.008)

    assert card.intake.valve_lift_in == pytest.approx(0.360)
    assert card.intake.advertised_duration_deg == pytest.approx(262.0)
    assert card.intake.duration_050_deg == pytest.approx(238.0)
    assert card.intake.lobe_center_deg == pytest.approx(109.5)
    assert card.intake.lash_in == pytest.approx(0.006)

    assert card.exhaust.valve_lift_in == pytest.approx(0.360)
    assert card.exhaust.advertised_duration_deg == pytest.approx(270.0)
    assert card.exhaust.duration_050_deg == pytest.approx(246.0)
    assert card.exhaust.lobe_center_deg == pytest.approx(104.5)
    assert card.exhaust.lash_in == pytest.approx(0.008)


# (b) Non-positive valve lift is rejected.
@pytest.mark.parametrize("bad_lift", [-0.360, 0.0])
def test_non_positive_valve_lift_raises(bad_lift: float) -> None:
    with pytest.raises(ValueError, match="valve_lift_in must be positive"):
        CamLobeSpec(bad_lift, 262.0, 238.0, 109.5, 0.006)


# (c) Zero/negative durations are rejected (both advertised and @0.050").
@pytest.mark.parametrize("bad_advertised", [0.0, -262.0])
def test_non_positive_advertised_duration_raises(bad_advertised: float) -> None:
    with pytest.raises(ValueError, match="advertised_duration_deg must be positive"):
        CamLobeSpec(0.360, bad_advertised, 238.0, 109.5, 0.006)


@pytest.mark.parametrize("bad_050", [0.0, -238.0])
def test_non_positive_duration_050_raises(bad_050: float) -> None:
    with pytest.raises(ValueError, match="duration_050_deg must be positive"):
        CamLobeSpec(0.360, 262.0, bad_050, 109.5, 0.006)


# (d) Negative lash is rejected; zero lash is allowed (a solid-lifter cam can be
# zero-lash, so the bound is non-negative rather than strictly positive).
def test_negative_lash_raises() -> None:
    with pytest.raises(ValueError, match="lash_in must be non-negative"):
        CamLobeSpec(0.360, 262.0, 238.0, 109.5, -0.001)


def test_zero_lash_is_allowed() -> None:
    spec = CamLobeSpec(0.360, 262.0, 238.0, 109.5, 0.0)
    assert spec.lash_in == 0.0


# (e) Existing invariant preserved: advertised duration cannot be tighter than
# duration @ 0.050" (the ``advertised_lt_050`` trap).
def test_advertised_narrower_than_duration_050_raises() -> None:
    with pytest.raises(ValueError, match=r"advertised_duration < duration@0.050"):
        CamLobeSpec(0.360, 238.0, 262.0, 109.5, 0.006)
