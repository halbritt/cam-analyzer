"""Golden snapshot of the single deliverable: ``cam-analyze --reference``.

The reference report is the one end-to-end artifact the tool produces, yet its
real numbers (DCR, LSA, centerlines, overlap) were previously asserted only
against synthetic fixtures or loose bounds — nothing pinned the actual output
against regression (review S7 / inverse-check #5). This test drives the exact
CLI path (``main(["--reference"])``) in-process and compares the rendered
Markdown to a committed golden file, plus anchors the load-bearing physical
numbers explicitly so a fixture regeneration can never silently launder a
changed result.

To regenerate the golden after an *intended* output change::

    PYTHONPATH=src python3 -m cam_analyzer --reference > tests/golden/reference_report.md

and review the diff before committing.
"""

from __future__ import annotations

from pathlib import Path

from cam_analyzer.cli import main

_GOLDEN = Path(__file__).parent / "golden" / "reference_report.md"


def _render_reference(capsys) -> str:
    exit_code = main(["--reference"])
    assert exit_code == 0
    return capsys.readouterr().out


def test_reference_report_matches_golden(capsys) -> None:
    rendered = _render_reference(capsys)
    golden = _GOLDEN.read_text()
    # Trailing-newline-insensitive full snapshot: everything else must match byte-for-byte.
    assert rendered.strip("\n") == golden.strip("\n")


def test_reference_report_pins_the_real_physical_numbers(capsys) -> None:
    rendered = _render_reference(capsys)
    # These are the hand-checkable WR250R (Web Cam 81-651) numbers. They are the
    # reason the tool exists; pin them so a refactor can't drift them unnoticed.
    anchors = (
        "Lobe separation angle: 107.000 deg [crank]",
        "Intake centerline: 109.500 deg [crank]",
        "Exhaust centerline: 615.500 deg [crank]",
        "Overlap at 0.050 inch [valve_side, INFERRED]: 28.000 deg [crank]",
        "Dynamic compression ratio: 11.272 ratio [dimensionless, INFERRED]; "
        "intake closing 228.500 deg [crank]",
    )
    for anchor in anchors:
        assert anchor in rendered, f"missing pinned number: {anchor!r}"


def test_reference_safety_verdicts_stay_honest(capsys) -> None:
    # The cam card alone cannot justify PTV / spring verdicts; the report must
    # say so (UNDECIDABLE), never fabricate a PASS/FAIL. This is the honesty
    # behavior the whole architecture exists to protect.
    rendered = _render_reference(capsys)
    assert rendered.count("UNDECIDABLE FROM CAM CARD") == 3  # intake PTV, exhaust PTV, spring
