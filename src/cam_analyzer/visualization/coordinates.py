"""Crank-angle projection helpers for visualization coordinates."""

from __future__ import annotations

CYCLE_DEGREES = 720.0
PRIMARY_OVERLAP_RELATIVE_MIN_DEG = -360.0
PRIMARY_OVERLAP_RELATIVE_MAX_DEG = 360.0


def canonical_to_overlap_relative(canonical_angle_deg: float) -> float:
    """Project canonical 0-720 crank degrees into full-cycle overlap-relative degrees."""

    normalized = canonical_angle_deg % CYCLE_DEGREES
    if normalized > CYCLE_DEGREES / 2.0:
        return normalized - CYCLE_DEGREES
    return normalized


def overlap_relative_to_canonical(overlap_relative_angle_deg: float) -> float:
    """Return the canonical 0-720 equivalent for an overlap-relative angle."""

    return overlap_relative_angle_deg % CYCLE_DEGREES


def is_primary_overlap_relative_angle(overlap_relative_angle_deg: float) -> bool:
    """Whether an overlap-relative angle belongs in the primary -360 to +360 view."""

    return (
        PRIMARY_OVERLAP_RELATIVE_MIN_DEG
        <= overlap_relative_angle_deg
        <= PRIMARY_OVERLAP_RELATIVE_MAX_DEG
    )


# Backward-compatible aliases for older visualization callers. New code should use
# the explicit overlap-relative names so plotting coordinates cannot be confused
# with canonical crank coordinates.
PRIMARY_DISPLAY_MIN_DEG = PRIMARY_OVERLAP_RELATIVE_MIN_DEG
PRIMARY_DISPLAY_MAX_DEG = PRIMARY_OVERLAP_RELATIVE_MAX_DEG
canonical_to_overlap_display = canonical_to_overlap_relative
overlap_display_to_canonical = overlap_relative_to_canonical
is_primary_overlap_display_angle = is_primary_overlap_relative_angle


__all__ = [
    "CYCLE_DEGREES",
    "PRIMARY_DISPLAY_MAX_DEG",
    "PRIMARY_DISPLAY_MIN_DEG",
    "PRIMARY_OVERLAP_RELATIVE_MAX_DEG",
    "PRIMARY_OVERLAP_RELATIVE_MIN_DEG",
    "canonical_to_overlap_display",
    "canonical_to_overlap_relative",
    "overlap_display_to_canonical",
    "is_primary_overlap_display_angle",
    "is_primary_overlap_relative_angle",
    "overlap_relative_to_canonical",
]
