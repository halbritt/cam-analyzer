"""The C1 boundary guard (D001/D007, trap `analysis_imports_source`).

This is the load-bearing test: it makes "analysis depends only on CamProfile" a
*property the build checks*, not something a reviewer has to notice. It parses
every module under ``cam_analyzer/analysis`` with ``ast`` (no imports executed, no
third-party deps needed) and fails if any of them imports ``cam_analyzer.sources``.

Run: ``pytest tests/test_architecture_boundary.py``
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_ANALYSIS_DIR = _REPO_ROOT / "src" / "cam_analyzer" / "analysis"
_FORBIDDEN_PREFIX = "cam_analyzer.sources"


def _analysis_modules() -> list[Path]:
    return sorted(_ANALYSIS_DIR.rglob("*.py"))


def _imported_modules(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            names.add(node.module)
    return names


def test_analysis_dir_exists() -> None:
    assert _ANALYSIS_DIR.is_dir(), f"missing analysis package at {_ANALYSIS_DIR}"
    assert _analysis_modules(), "no analysis modules found to check"


@pytest.mark.parametrize("module_path", _analysis_modules(), ids=lambda p: p.name)
def test_analysis_never_imports_sources(module_path: Path) -> None:
    """C1: no analysis module may import the source layer."""
    tree = ast.parse(module_path.read_text(), filename=str(module_path))
    offenders = {
        name
        for name in _imported_modules(tree)
        if name == _FORBIDDEN_PREFIX or name.startswith(_FORBIDDEN_PREFIX + ".")
    }
    assert not offenders, (
        f"{module_path.relative_to(_REPO_ROOT)} violates C1 (one-way dependency): "
        f"imports {sorted(offenders)}. Analysis must consume only the CamProfile "
        f"boundary; route the need through cam_analyzer.profile."
    )
