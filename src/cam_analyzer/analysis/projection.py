"""Renderer-agnostic JSON projection of source-blind CamProfile samples.

The projection is deliberately read-only: it samples profiles only through the
C5 boundary and serializes the stamped answers a renderer is allowed to draw.
Renderers may style or scale this data, but they do not get to recompute values
or upgrade provenance.
"""

from __future__ import annotations

import json
import math
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import Any

from cam_analyzer.profile import CamProfile
from cam_analyzer.quantity import Angle, Crank, ProvFloat, Provenance, Quantity, Refusal

SCHEMA = "cam_analyzer.visualization_projection.v1"
_CYCLE_DEGREES = 720.0
_DEFAULT_SAMPLE_STEP_DEG = 5.0
_DEFAULT_SAMPLE_DEGREES = tuple(
    float(degrees)
    for degrees in range(0, int(_CYCLE_DEGREES) + 1, int(_DEFAULT_SAMPLE_STEP_DEG))
)


@dataclass(frozen=True, slots=True)
class ProfileProjectionInput:
    """A named profile to include in a visualization projection."""

    name: str
    profile: CamProfile
    role: str | None = None


@dataclass(frozen=True, slots=True)
class _SeriesQuery:
    name: str
    derivative_order: int | None = None


@dataclass(frozen=True, slots=True)
class _ProjectionSample:
    index: int
    crank_deg: float
    answer: dict[str, object]


_SERIES_QUERIES = (
    _SeriesQuery("lift"),
    _SeriesQuery("velocity", derivative_order=1),
    _SeriesQuery("acceleration", derivative_order=2),
    _SeriesQuery("jerk", derivative_order=3),
)


def project_cam_profiles(
    profiles: Iterable[ProfileProjectionInput] | Mapping[str, CamProfile],
    *,
    sample_degrees: Iterable[float] | None = None,
    event_lifts: Iterable[ProvFloat] = (),
) -> dict[str, object]:
    """Project one or more profiles into deterministic, JSON-serializable data.

    ``profiles`` may be either a mapping of name to profile or explicit
    :class:`ProfileProjectionInput` rows. The output intentionally contains only
    renderer-neutral JSON values: quantities, refusals, query errors, samples,
    and provenance/refusal style metadata.
    """

    profile_inputs = _normalize_profiles(profiles)
    sample_grid = _normalize_sample_degrees(
        _DEFAULT_SAMPLE_DEGREES if sample_degrees is None else sample_degrees
    )
    event_lift_values = tuple(event_lifts)

    return {
        "schema": SCHEMA,
        "cycle_degrees": _CYCLE_DEGREES,
        "sample_degrees": list(sample_grid),
        "profiles": [
            _project_profile(profile_input, sample_grid, event_lift_values)
            for profile_input in profile_inputs
        ],
    }


def projection_to_json(projection: Mapping[str, object]) -> str:
    """Serialize a projection with stable key ordering and strict JSON numbers."""

    return json.dumps(projection, allow_nan=False, separators=(",", ":"), sort_keys=True)


def _normalize_profiles(
    profiles: Iterable[ProfileProjectionInput] | Mapping[str, CamProfile],
) -> tuple[ProfileProjectionInput, ...]:
    if isinstance(profiles, Mapping):
        normalized = tuple(
            ProfileProjectionInput(name=name, profile=profile)
            for name, profile in profiles.items()
        )
    else:
        normalized = tuple(profiles)

    if not normalized:
        raise ValueError("at least one profile is required")

    seen_names: set[str] = set()
    for profile_input in normalized:
        if not profile_input.name:
            raise ValueError("profile names must be non-empty")
        if profile_input.name in seen_names:
            raise ValueError(f"duplicate profile name: {profile_input.name}")
        seen_names.add(profile_input.name)
    return normalized


def _normalize_sample_degrees(sample_degrees: Iterable[float]) -> tuple[float, ...]:
    normalized = tuple(float(degrees) for degrees in sample_degrees)
    if not normalized:
        raise ValueError("sample_degrees must contain at least one angle")

    previous = -math.inf
    for degrees in normalized:
        _require_finite(degrees, "sample degree")
        if not 0.0 <= degrees <= _CYCLE_DEGREES:
            raise ValueError("sample_degrees must be within [0, 720]")
        if degrees <= previous:
            raise ValueError("sample_degrees must be strictly increasing")
        previous = degrees
    return normalized


def _project_profile(
    profile_input: ProfileProjectionInput,
    sample_degrees: tuple[float, ...],
    event_lifts: tuple[ProvFloat, ...],
) -> dict[str, object]:
    profile_projection: dict[str, object] = {
        "name": profile_input.name,
        "summary": {
            "max_lift": _call_boundary_query("max_lift", profile_input.profile.max_lift),
            "area_under_curve": _call_boundary_query(
                "area_under_curve",
                profile_input.profile.area_under_curve,
            ),
        },
        "series": {
            query.name: _project_series(profile_input.profile, query, sample_degrees)
            for query in _SERIES_QUERIES
        },
    }
    if profile_input.role is not None:
        profile_projection["role"] = profile_input.role
    if event_lifts:
        profile_projection["events_at_lift"] = [
            _project_events_at_lift(profile_input.profile, lift) for lift in event_lifts
        ]
    return profile_projection


def _project_series(
    profile: CamProfile,
    query: _SeriesQuery,
    sample_degrees: tuple[float, ...],
) -> dict[str, object]:
    samples = tuple(
        _ProjectionSample(
            index=index,
            crank_deg=degrees,
            answer=_sample_profile_query(profile, query, degrees),
        )
        for index, degrees in enumerate(sample_degrees)
    )
    return {
        "query": query.name,
        "derivative_order": query.derivative_order,
        "samples": [_sample_to_json(sample) for sample in samples],
        "segments": _split_segments(query.name, samples),
    }


def _sample_profile_query(
    profile: CamProfile,
    query: _SeriesQuery,
    crank_deg: float,
) -> dict[str, object]:
    angle = Angle.crank(crank_deg)
    try:
        if query.name == "lift":
            return _serialize_boundary_result(profile.lift_at(angle))
        if query.name == "velocity":
            return _serialize_boundary_result(profile.velocity_at(angle))
        if query.name == "acceleration":
            return _serialize_boundary_result(profile.acceleration_at(angle))
        if query.name == "jerk":
            return _serialize_boundary_result(profile.jerk_at(angle))
    except ValueError as exc:
        return _serialize_query_error(f"{query.name}_at({crank_deg:.3f} crank deg)", exc)
    raise AssertionError(f"unknown projection query: {query.name}")


def _call_boundary_query(
    requested: str,
    query: Callable[[], object],
) -> dict[str, object]:
    try:
        return _serialize_boundary_result(query())
    except ValueError as exc:
        return _serialize_query_error(requested, exc)


def _project_events_at_lift(profile: CamProfile, lift: ProvFloat) -> dict[str, object]:
    projection: dict[str, object] = {
        "threshold": _serialize_quantity(lift),
    }
    try:
        projection["events"] = [
            _serialize_angle(event) for event in profile.events_at_lift(lift)
        ]
        projection["duration"] = _serialize_angle(profile.duration_at_lift(lift))
    except ValueError as exc:
        projection["error"] = _serialize_query_error("events_at_lift", exc)
    return projection


def _serialize_boundary_result(result: object) -> dict[str, object]:
    if isinstance(result, Quantity):
        return _serialize_quantity(result)
    if isinstance(result, Refusal):
        return _serialize_refusal(result)
    raise TypeError(f"unsupported boundary result: {type(result).__name__}")


def _serialize_quantity(value: Quantity[Any]) -> dict[str, object]:
    magnitude = float(value)
    _require_finite(magnitude, "quantity value")
    return {
        "kind": "quantity",
        "value": magnitude,
        "unit": value.unit,
        "frame": value.frame,
        "provenance": value.provenance.name,
        "provenance_rank": int(value.provenance),
    }


def _serialize_refusal(refusal: Refusal) -> dict[str, object]:
    serialized: dict[str, object] = {
        "kind": "refusal",
        "requested": refusal.requested,
        "reason": refusal.reason,
        "remedy": refusal.remedy,
    }
    serialized.update(_serialized_optional_provenance(refusal.provenance))
    return serialized


def _serialize_query_error(requested: str, exc: ValueError) -> dict[str, object]:
    return {
        "kind": "query_error",
        "requested": requested,
        "reason": str(exc),
        "remedy": "sample only supported boundary points or provide a profile that can answer",
        "provenance": None,
        "provenance_rank": None,
    }


def _serialize_angle(angle: Angle[Crank]) -> dict[str, object]:
    degrees = float(angle.degrees)
    _require_finite(degrees, "angle degrees")
    return {
        "kind": "angle",
        "degrees": degrees,
        "unit": "degree",
        "frame": angle.frame,
    }


def _serialized_optional_provenance(
    provenance: Provenance | None,
) -> dict[str, object]:
    if provenance is None:
        return {"provenance": None, "provenance_rank": None}
    return {"provenance": provenance.name, "provenance_rank": int(provenance)}


def _sample_to_json(sample: _ProjectionSample) -> dict[str, object]:
    return {
        "index": sample.index,
        "crank_deg": sample.crank_deg,
        "answer": sample.answer,
    }


def _split_segments(
    query_name: str,
    samples: tuple[_ProjectionSample, ...],
) -> list[dict[str, object]]:
    if not samples:
        return []

    segments: list[dict[str, object]] = []
    start_index = 0
    active_key = _segment_key(samples[0].answer)
    for index, sample in enumerate(samples[1:], start=1):
        key = _segment_key(sample.answer)
        if key == active_key:
            continue
        segments.append(
            _segment_to_json(query_name, samples, start_index, index - 1, active_key)
        )
        start_index = index
        active_key = key
    segments.append(
        _segment_to_json(query_name, samples, start_index, len(samples) - 1, active_key)
    )
    return segments


def _segment_key(answer: Mapping[str, object]) -> tuple[str, str | None]:
    kind = answer.get("kind")
    if not isinstance(kind, str):
        raise TypeError("serialized answer is missing a string kind")
    provenance = answer.get("provenance")
    if provenance is not None and not isinstance(provenance, str):
        raise TypeError("serialized answer has a non-string provenance")
    return kind, provenance


def _segment_to_json(
    query_name: str,
    samples: tuple[_ProjectionSample, ...],
    start_index: int,
    end_index: int,
    key: tuple[str, str | None],
) -> dict[str, object]:
    kind, provenance_name = key
    return {
        "query": query_name,
        "kind": kind,
        "provenance": provenance_name,
        "sample_start_index": start_index,
        "sample_end_index": end_index,
        "start_deg": samples[start_index].crank_deg,
        "end_deg": samples[end_index].crank_deg,
        "draw_line": kind == "quantity",
        "points": [
            _segment_point(sample) for sample in samples[start_index : end_index + 1]
        ],
    }


def _segment_point(sample: _ProjectionSample) -> dict[str, object]:
    return {
        "sample_index": sample.index,
        "crank_deg": sample.crank_deg,
        "value": sample.answer.get("value"),
        "answer_kind": sample.answer["kind"],
    }


def _require_finite(value: float, label: str) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{label} must be finite")


__all__ = ["ProfileProjectionInput", "SCHEMA", "project_cam_profiles", "projection_to_json"]
