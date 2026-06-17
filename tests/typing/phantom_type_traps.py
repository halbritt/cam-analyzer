"""Typing-conformance fixture (RFC 0001 Pillar B / C6).

Intentional ``mypy`` errors proving the phantom *unit* and *frame* parameters turn
two whole families of C6 mistakes into type errors rather than runtime hope:

* ``mm_labeled_as_inch`` / ``cross_unit_is_a_type_error`` — adding a millimetre
  quantity to an inch quantity does not type-check.
* ``cam_angle_as_crank`` — passing a cam-frame angle where a crank angle is
  required does not type-check.

This file is *intentionally* a mypy error. It is excluded from the package's main
``mypy`` run (which checks only ``src/cam_analyzer``) and is invoked on demand by
``tests/test_conformance_traps.py::test_phantom_types_make_unit_and_frame_errors``.
The legal counterparts below must keep type-checking, so the run reports exactly
two errors.
"""

from __future__ import annotations

from cam_analyzer.quantity import Angle, Crank, Inch, Mm, Quantity, inferred


def cross_unit_sum() -> Quantity[Mm]:
    millimetres = inferred(5.0, Mm, "valve_side")
    inches = inferred(1.0, Inch, "valve_side")
    # error: Unsupported operand types for + ("Quantity[Mm]" and "Quantity[Inch]")
    return millimetres + inches


def same_unit_sum_is_fine() -> Quantity[Mm]:
    # The legal case still type-checks — same-unit arithmetic stays ergonomic.
    return inferred(5.0, Mm, "valve_side") + inferred(2.0, Mm, "valve_side")


def _needs_crank(angle: Angle[Crank]) -> float:
    return angle.require_crank()


def cam_angle_where_crank_required() -> float:
    # error: Argument 1 to "_needs_crank" has incompatible type "Angle[Cam]"
    return _needs_crank(Angle.cam(54.0))


def crank_angle_is_fine() -> float:
    return _needs_crank(Angle.crank(109.5))
