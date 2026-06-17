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


def _module_name(module_path: Path) -> str:
    parts = list(module_path.relative_to(_REPO_ROOT / "src").with_suffix("").parts)
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def _package_name(module_path: Path) -> str:
    module_name = _module_name(module_path)
    if module_path.name == "__init__.py":
        return module_name
    return module_name.rsplit(".", 1)[0]


def _resolve_import_from(node: ast.ImportFrom, module_path: Path) -> str | None:
    if node.level == 0:
        return node.module

    package_parts = _package_name(module_path).split(".")
    if node.level > len(package_parts):
        return None
    anchor_parts = package_parts[: len(package_parts) - node.level + 1]
    module_parts = node.module.split(".") if node.module else []
    return ".".join(anchor_parts + module_parts)


def _imported_modules(tree: ast.AST, module_path: Path) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module_name = _resolve_import_from(node, module_path)
            if module_name:
                names.add(module_name)
                names.update(
                    f"{module_name}.{alias.name}"
                    for alias in node.names
                    if alias.name != "*"
                )
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
        for name in _imported_modules(tree, module_path)
        if name == _FORBIDDEN_PREFIX or name.startswith(_FORBIDDEN_PREFIX + ".")
    }
    assert not offenders, (
        f"{module_path.relative_to(_REPO_ROOT)} violates C1 (one-way dependency): "
        f"imports {sorted(offenders)}. Analysis must consume only the CamProfile "
        f"boundary; route the need through cam_analyzer.profile."
    )
