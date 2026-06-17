"""Executable checks for the currently enforceable conformance traps."""

from __future__ import annotations

import ast
import inspect
import os
import shutil
import subprocess
import sys
from collections.abc import Mapping
from importlib import import_module
from importlib.util import find_spec
from pathlib import Path
from typing import Any, Callable

import pytest

import cam_analyzer.quantity as quantity_module
from cam_analyzer.conformance import CORPUS, DECLARED_ONLY
from cam_analyzer.quantity import Angle, Inch, Provenance, Quantity, extrapolated, inferred, measured

_EXECUTABLE_TRAPS = {
    "advertised_lt_050",
    "fabricated_nose_as_measured",
    "sparse_as_continuous",
    "analysis_imports_source",
    "mm_labeled_as_inch",
    "quantity_unsealed_construction",
    "provenance_as_argument",
    "measured_confined_to_sources",
    "cam_angle_as_crank",
}

_PACKAGE_ROOT = Path(quantity_module.__file__).resolve().parent  # .../src/cam_analyzer
_REPO_ROOT = _PACKAGE_ROOT.parents[1]
# MEASURED is conferred only by the source layer plus the spec-policy authority;
# quantity.py is where the factory is defined.
_MEASURED_ALLOWED_FILES = frozenset(
    {
        _PACKAGE_ROOT / "quantity.py",
        _PACKAGE_ROOT / "analysis" / "safety.py",
    }
)
_MEASURED_ALLOWED_DIR = _PACKAGE_ROOT / "sources"


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
    return _flatten_profile_candidates(module.profiles_from_cam_card(card))


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


def test_every_corpus_trap_is_executable_or_explicitly_declared_only() -> None:
    # Coverage guard: a trap is either exercised by a test (in _EXECUTABLE_TRAPS) or
    # explicitly admitted as declared-only (in conformance.DECLARED_ONLY). Adding a
    # new corpus trap without a witness now fails here until it is classified, so the
    # silent declared-vs-executable gap cannot grow.
    classified = _EXECUTABLE_TRAPS | DECLARED_ONLY
    unclassified = sorted(trap.name for trap in CORPUS if trap.name not in classified)
    assert not unclassified, (
        "every conformance trap must be executable or explicitly declared-only; "
        f"unclassified: {unclassified}"
    )
    # A trap cannot be both — declared-only means there is no executable witness.
    overlap = sorted(_EXECUTABLE_TRAPS & DECLARED_ONLY)
    assert not overlap, f"a trap is both executable and declared-only: {overlap}"
    # Neither set may name a trap absent from the frozen corpus.
    corpus_names = {trap.name for trap in CORPUS}
    stray = sorted(name for name in classified if name not in corpus_names)
    assert not stray, f"classified trap names absent from the corpus: {stray}"


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


# --- RFC 0001 Pillar A — sealed construction (C3) ----------------------------


def test_quantity_unsealed_construction_is_rejected() -> None:
    # The old fabricable 4-arg Quantity(...) cannot construct: the module-private
    # mint token is required, so MEASURED can't be minted from nothing and a
    # value's provenance can't be raised by reconstructing it.
    with pytest.raises(TypeError):
        Quantity(0.360, "inch", "valve_side", Provenance.MEASURED)  # type: ignore[call-arg]
    with pytest.raises(TypeError):
        Quantity(0.360, "inch", "valve_side", Provenance.MEASURED, object())


def test_dataclasses_replace_cannot_raise_a_values_provenance() -> None:
    # The seal survives dataclasses.replace(): a minted value's token is spent, so
    # carrying it back through replace cannot re-mint the value with a stronger stamp.
    import dataclasses

    value = inferred(0.050, Inch, "valve_side")
    with pytest.raises(TypeError):
        dataclasses.replace(value, provenance=Provenance.MEASURED)


def test_quantity_pickle_and_copy_roundtrip_through_the_keyed_mint() -> None:
    # __reduce__ routes pickle/copy through the keyed mint (not the spent-token
    # __init__), preserving — never conferring — provenance.
    import copy
    import pickle

    value = measured(0.060, Inch, "valve_side")
    assert pickle.loads(pickle.dumps(value)) == value
    restored = copy.deepcopy(value)
    assert restored == value and restored.provenance is Provenance.MEASURED


def test_no_public_value_factory_confers_provenance_by_argument() -> None:
    # The blessed acquisition factories bake provenance into the NAME, never a param.
    for factory in (measured, inferred, extrapolated):
        assert "provenance" not in inspect.signature(factory).parameters, factory.__name__
    # No other *public* callable in the value module that returns a Quantity may
    # take a provenance argument (the private keyed mint `_mint` is exempt).
    offenders: list[str] = []
    for name, obj in vars(quantity_module).items():
        if name.startswith("_") or not callable(obj):
            continue
        try:
            signature = inspect.signature(obj)
        except (TypeError, ValueError):
            continue
        return_annotation = signature.return_annotation
        returns_quantity = isinstance(return_annotation, str) and "Quantity" in return_annotation
        if returns_quantity and "provenance" in signature.parameters:
            offenders.append(name)
    assert not offenders, f"public value factories must not accept provenance=: {offenders}"


def _argument_is_measured(argument: ast.expr) -> bool:
    """True if an argument node denotes MEASURED — ``Provenance.MEASURED`` or a bare ``MEASURED``.

    Catches the keyed-mint back door: ``Quantity._mint(..., Provenance.MEASURED)``
    fabricates MEASURED from any module, so a MEASURED-carrying ``_mint`` call is
    just as much a conferral as ``measured()`` and must be confined identically.
    """
    if isinstance(argument, ast.Attribute):
        return argument.attr == "MEASURED"
    if isinstance(argument, ast.Name):
        return argument.id == "MEASURED"
    return False


def test_measured_conferral_is_confined_to_the_source_layer() -> None:
    offenders: list[str] = []
    for path in _PACKAGE_ROOT.rglob("*.py"):
        if path in _MEASURED_ALLOWED_FILES or _MEASURED_ALLOWED_DIR in path.parents:
            continue
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            called = func.id if isinstance(func, ast.Name) else getattr(func, "attr", None)
            if called == "measured":
                offenders.append(f"{path.relative_to(_PACKAGE_ROOT)}:{node.lineno}")
            elif called == "_mint" and any(
                _argument_is_measured(arg) for arg in (*node.args, *(kw.value for kw in node.keywords))
            ):
                # The keyed mint carrying a MEASURED literal is MEASURED conferral too.
                offenders.append(f"{path.relative_to(_PACKAGE_ROOT)}:{node.lineno}")
    assert not offenders, (
        "MEASURED conferral — via measured() or a MEASURED-carrying Quantity._mint(...) — "
        "may only happen in the source layer or the spec-policy authority "
        f"(analysis/safety.py); found: {offenders}"
    )


# --- RFC 0001 Pillar B — phantom-typed units (C6) ----------------------------


def _mypy_command() -> list[str] | None:
    found = shutil.which("mypy")
    if found:
        return [found]
    if find_spec("mypy") is not None:
        return [sys.executable, "-m", "mypy"]
    return None


def test_phantom_types_make_unit_and_frame_errors() -> None:
    # mm + inch and cam-as-crank must be *type* errors, not runtime hope (traps
    # mm_labeled_as_inch / cross_unit_is_a_type_error and cam_angle_as_crank). Runs
    # the typing fixture through mypy and checks exactly the two illegal lines fail
    # while their legal counterparts type-check.
    mypy_command = _mypy_command()
    if mypy_command is None:
        # Under enforcement (the hook/make/CI set CAM_ANALYZER_REQUIRE_MYPY=1) an
        # absent mypy must FAIL loudly — silently skipping would drop the C6
        # phantom-type guarantee. For a casual install the env var is unset and we
        # skip for portability.
        if os.environ.get("CAM_ANALYZER_REQUIRE_MYPY") == "1":
            pytest.fail(
                "CAM_ANALYZER_REQUIRE_MYPY=1 but mypy is not installed; the C6 "
                "phantom-type guarantee cannot be enforced (pip install -e '.[dev]')"
            )
        pytest.skip("mypy is not installed in this environment (pip install -e '.[dev]')")
    fixture = Path(__file__).resolve().parent / "typing" / "phantom_type_traps.py"
    environment = {**os.environ, "MYPYPATH": str(_REPO_ROOT / "src")}
    result = subprocess.run(
        [*mypy_command, "--strict", "--no-incremental", "--explicit-package-bases", str(fixture)],
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
        env=environment,
    )
    output = result.stdout + result.stderr
    assert result.returncode != 0, f"phantom-type traps unexpectedly type-checked:\n{output}"
    assert "Unsupported operand types for +" in output, output
    assert "Quantity[Mm]" in output and "Quantity[Inch]" in output, output
    assert 'incompatible type "Angle[Cam]"' in output, output
    # Exactly the two illegal lines fail; the legal same-unit / crank cases pass.
    assert "Found 2 errors" in output, f"a legal case unexpectedly failed:\n{output}"
