"""Crank-angle projection helpers for visualization coordinates."""

from __future__ import annotations

CYCLE_DEGREES = 720.0
PRIMARY_DISPLAY_MIN_DEG = -180.0
PRIMARY_DISPLAY_MAX_DEG = 180.0


def canonical_to_overlap_display(canonical_angle_deg: float) -> float:
    """Project canonical 0-720 crank degrees into overlap-centered display degrees."""

    normalized = canonical_angle_deg % CYCLE_DEGREES
    if normalized > CYCLE_DEGREES / 2.0:
        return normalized - CYCLE_DEGREES
    return normalized


def overlap_display_to_canonical(display_angle_deg: float) -> float:
    """Return the canonical 0-720 equivalent for an overlap-centered display angle."""

    return display_angle_deg % CYCLE_DEGREES


def is_primary_overlap_display_angle(display_angle_deg: float) -> bool:
    """Whether an overlap-centered angle belongs in the primary -180 to +180 view."""

    return PRIMARY_DISPLAY_MIN_DEG <= display_angle_deg <= PRIMARY_DISPLAY_MAX_DEG


__all__ = [
    "CYCLE_DEGREES",
    "PRIMARY_DISPLAY_MAX_DEG",
    "PRIMARY_DISPLAY_MIN_DEG",
    "canonical_to_overlap_display",
    "is_primary_overlap_display_angle",
    "overlap_display_to_canonical",
]
