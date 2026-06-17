"""Executable checks for the currently enforceable conformance traps."""

from __future__ import annotations

from collections.abc import Mapping
from importlib import import_module
from typing import Any, Callable

import pytest

from cam_analyzer.conformance import CORPUS
from cam_analyzer.quantity import Angle, Provenance, Quantity

_EXECUTABLE_TRAPS = {
    "advertised_lt_050",
    "fabricated_nose_as_measured",
    "sparse_as_continuous",
    "analysis_imports_source",
}


def _optional_import(module_name: str) -> Any | None:
    try:
        return import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name == module_name or exc.name.startswith(module_name + "."):
            return None
        if exc.name == "cam_analyzer.profile.canonical":
            return None
        raise


def _require_module(module_name: str) -> Any:
    module = _optional_import(module_name)
    assert module is not None, f"{module_name} must be importable for its conformance trap"
    return module


def _is_refusal(value: Any) -> bool:
    return value.__class__.__name__ == "Refusal"


def _looks_like_profile(value: Any) -> bool:
    return hasattr(value, "lift_at") and hasattr(value, "max_lift")


def _flatten_profile_candidates(value: Any) -> tuple[Any, ...]:
    if _looks_like_profile(value):
        return (value,)
    if isinstance(value, Mapping):
        return tuple(
            profile
            for item in value.values()
            for profile in _flatten_profile_candidates(item)
        )
    if isinstance(value, tuple | list):
        return tuple(
            profile for item in value for profile in _flatten_profile_candidates(item)
        )

    candidates = []
    for attr in ("intake", "exhaust"):
        if hasattr(value, attr):
            candidates.extend(_flatten_profile_candidates(getattr(value, attr)))
    return tuple(candidates)


def _cam_card_module() -> Any | None:
    return _optional_import("cam_analyzer.sources.cam_card")


def _cam_card_profiles(card: Any) -> tuple[Any, ...]:
    module = _cam_card_module()
    if module is None:
        return ()
    return _flatten_profile_candidates(module.CamCardApproxProfile(card))


def _assert_refused_or_not_measured(query: Callable[[], Any]) -> None:
    try:
        value = query()
    except ValueError:
        return

    provenance = getattr(value, "provenance", None)
    if _is_refusal(value):
        assert provenance is None or provenance != Provenance.MEASURED
        return

    assert provenance is not None, "trap returned an unstamped value instead of refusing"
    assert provenance != Provenance.MEASURED


def _assert_refused_or_unconstructable(query: Callable[[], Any]) -> None:
    try:
        value = query()
    except (TypeError, ValueError):
        return

    assert _is_refusal(value), "trap returned a continuous value instead of refusing"


@pytest.mark.parametrize("trap_name", sorted(_EXECUTABLE_TRAPS))
def test_executable_traps_remain_in_the_conformance_corpus(trap_name: str) -> None:
    assert trap_name in {trap.name for trap in CORPUS}


def test_advertised_lt_050_refuses_incoherent_cam_card() -> None:
    module = _require_module("cam_analyzer.sources.cam_card")

    with pytest.raises(ValueError, match="advertised_duration < duration@0.050"):
        module.CamLobeSpec(
            valve_lift_in=0.360,
            advertised_duration_deg=238.0,
            duration_050_deg=262.0,
            lobe_center_deg=109.5,
            lash_in=0.006,
        )


def test_fabricated_nose_as_measured_refuses_or_returns_non_measured() -> None:
    module = _require_module("cam_analyzer.sources.cam_card")

    profiles = _cam_card_profiles(module.CamCard.wr250r_reference())
    if not profiles:
        return

    for profile in profiles:
        _assert_refused_or_not_measured(profile.max_lift)
        _assert_refused_or_not_measured(lambda: profile.lift_at(Angle.crank(109.5)))


class _EightPointLookupOperator:
    name = "EightPointLookup"

    def evaluate(self, crank_deg: float) -> float:
        return self._nearest_sample(crank_deg)

    def derivative(self, order: int, crank_deg: float) -> float:
        return 0.0

    @staticmethod
    def _nearest_sample(crank_deg: float) -> float:
        samples = (0.0, 0.050, 0.200, 0.360, 0.200, 0.050, 0.0, 0.0)
        index = round((crank_deg % 720.0) / 90.0) % len(samples)
        return samples[index]


def test_sparse_as_continuous_refuses_eight_point_lookup() -> None:
    canonical = _require_module("cam_analyzer.profile.canonical")
    provenance_map = _require_module("cam_analyzer.profile.provenance_map")

    model = canonical.CanonicalLiftModel(
        samples_720=(0.0, 0.050, 0.200, 0.360, 0.200, 0.050, 0.0, 0.0),
        operator=_EightPointLookupOperator(),
        provenance=provenance_map.ProvenanceMap([(0.0, Provenance.MEASURED)]),
    )

    def query_sparse_midpoint() -> Quantity:
        return canonical.CanonicalCamProfile(model).lift_at(Angle.crank(45.0))

    _assert_refused_or_unconstructable(query_sparse_midpoint)
