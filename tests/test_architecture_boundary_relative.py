"""Regression test for issue #1: the C1 boundary guard must catch *relative*
imports of the source layer, not just absolute ones.

Before the fix, ``_imported_modules`` only inspected ``ast.ImportFrom`` nodes
with ``node.level == 0`` (absolute imports). An analysis module that smuggled in
the source layer via a relative import -- e.g.
``from ..sources.cam_card import CamCard`` (``node.level == 2``) -- slipped past
the guard and the C1 test went green, defeating the one-way dependency rule.

These tests pin the resolver against a *synthesized* analysis module source, so
they fail loudly if the relative-import resolution regresses, regardless of what
the real ``cam_analyzer/analysis`` tree happens to contain.

Run: ``pytest tests/test_architecture_boundary_relative.py``
"""

from __future__ import annotations

import ast

from test_architecture_boundary import (
    _FORBIDDEN_PREFIX,
    _REPO_ROOT,
    _imported_modules,
)

# A module that *would* live here if it were real. We never write it to disk;
# the path is only used so relative-import resolution has a package to anchor
# against (src/cam_analyzer/analysis -> package "cam_analyzer.analysis").
_PROBE_PATH = _REPO_ROOT / "src" / "cam_analyzer" / "analysis" / "_probe.py"


def _offenders(source: str) -> set[str]:
    tree = ast.parse(source, filename=str(_PROBE_PATH))
    return {
        name
        for name in _imported_modules(tree, _PROBE_PATH)
        if name == _FORBIDDEN_PREFIX or name.startswith(_FORBIDDEN_PREFIX + ".")
    }


def test_relative_import_of_source_is_flagged() -> None:
    """C1 regression: ``from ..sources.cam_card import CamCard`` must be caught."""
    source = (
        "from __future__ import annotations\n"
        "from ..sources.cam_card import CamCard\n"
    )
    offenders = _offenders(source)
    assert "cam_analyzer.sources.cam_card" in offenders, (
        "relative import of the source layer slipped past the C1 guard: "
        f"got {sorted(offenders)}"
    )


def test_relative_import_of_source_package_is_flagged() -> None:
    """The package-level relative form (``from ..sources import cam_card``) too."""
    source = "from ..sources import cam_card\n"
    offenders = _offenders(source)
    # Both the package and the imported name resolve under the forbidden prefix.
    assert "cam_analyzer.sources" in offenders
    assert "cam_analyzer.sources.cam_card" in offenders


def test_clean_analysis_module_is_not_flagged() -> None:
    """Positive control: consuming only the CamProfile boundary is allowed."""
    source = (
        "from __future__ import annotations\n"
        "from cam_analyzer.profile import CamProfile\n"
        "from ..profile import canonical\n"  # relative, but to profile not sources
    )
    assert _offenders(source) == set()


def test_absolute_import_of_source_still_flagged() -> None:
    """Guard against losing the original absolute-import behavior."""
    source = "from cam_analyzer.sources.cam_card import CamCard\n"
    assert "cam_analyzer.sources.cam_card" in _offenders(source)
