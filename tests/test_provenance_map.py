"""Tests for ProvenanceMap.__init__ validation and at() resolution (issue #2)."""

import pytest

from cam_analyzer.profile.provenance_map import ProvenanceMap
from cam_analyzer.quantity import Provenance


# Docstring example: three contiguous half-open intervals tiling [0, 720).
#   [0, 15)    -> MEASURED
#   [15, 345)  -> EXTRAPOLATED
#   [345, 720) -> MEASURED
EXAMPLE = [
    (0.0, Provenance.MEASURED),
    (15.0, Provenance.EXTRAPOLATED),
    (345.0, Provenance.MEASURED),
]


def test_at_resolves_across_boundaries():
    pm = ProvenanceMap(EXAMPLE)

    # Interval starts are inclusive (half-open [start, next_start)).
    assert pm.at(0) == Provenance.MEASURED
    assert pm.at(15) == Provenance.EXTRAPOLATED
    assert pm.at(345) == Provenance.MEASURED

    # Interior points.
    assert pm.at(14.999) == Provenance.MEASURED
    assert pm.at(100) == Provenance.EXTRAPOLATED
    assert pm.at(344.999) == Provenance.EXTRAPOLATED
    assert pm.at(719) == Provenance.MEASURED


def test_at_is_periodic_with_720_wrap():
    pm = ProvenanceMap(EXAMPLE)

    # 720 wraps to 0.
    assert pm.at(720) == pm.at(0) == Provenance.MEASURED
    # 800 wraps to 80, which lands in the [15, 345) EXTRAPOLATED interval.
    assert pm.at(800) == pm.at(80) == Provenance.EXTRAPOLATED
    # A negative crank angle wraps too: -1 -> 719.
    assert pm.at(-1) == pm.at(719) == Provenance.MEASURED


def test_start_at_or_above_720_raises():
    with pytest.raises(ValueError):
        ProvenanceMap([(0.0, Provenance.MEASURED), (720.0, Provenance.EXTRAPOLATED)])


def test_negative_start_raises():
    with pytest.raises(ValueError):
        ProvenanceMap([(0.0, Provenance.MEASURED), (-10.0, Provenance.EXTRAPOLATED)])


def test_first_start_not_zero_raises():
    with pytest.raises(ValueError):
        ProvenanceMap([(15.0, Provenance.MEASURED), (345.0, Provenance.EXTRAPOLATED)])


def test_duplicate_starts_raise():
    with pytest.raises(ValueError):
        ProvenanceMap(
            [
                (0.0, Provenance.MEASURED),
                (15.0, Provenance.EXTRAPOLATED),
                (15.0, Provenance.MEASURED),
            ]
        )


def test_non_increasing_starts_raise():
    # Pre-sorting in __init__ means this collapses to the duplicate/ordering
    # check; supply an out-of-order pair that is also non-strictly-increasing.
    with pytest.raises(ValueError):
        ProvenanceMap([(0.0, Provenance.MEASURED), (10.0, Provenance.EXTRAPOLATED),
                       (10.0, Provenance.INFERRED)])


def test_empty_map_raises():
    with pytest.raises(ValueError):
        ProvenanceMap([])


def test_first_start_accepts_tiny_float_dust():
    # A first start within the zero tolerance is accepted as crank angle 0.
    pm = ProvenanceMap([(1e-12, Provenance.MEASURED), (15.0, Provenance.EXTRAPOLATED)])
    assert pm.at(0) == Provenance.MEASURED
