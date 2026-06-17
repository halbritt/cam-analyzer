"""The conformance corpus — the durable asset (Pillar D / D007).

A frozen museum of traps a conformant CamProfile (or CamCard ingest) must *refuse
or be unable to construct*. Correctness is defined by the attacks the boundary
withstands, not by the happy path. Trap names are part of the ubiquitous language.

Each trap is a name + intent. Many are now *executable* (enforced by a test);
the rest stay declared until their machinery lands. As of RFC 0001 the executable
set is: `analysis_imports_source` (tests/test_architecture_boundary.py),
`advertised_lt_050`, `sparse_as_continuous`, `fabricated_nose_as_measured`,
`mm_labeled_as_inch`, `quantity_unsealed_construction`, `provenance_as_argument`,
and `measured_confined_to_sources` (tests/test_conformance_traps.py). See that
module's `_EXECUTABLE_TRAPS` set for the live list.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Trap:
    name: str
    intent: str  # what a conformant boundary must do: refuse / cannot-construct


CORPUS: tuple[Trap, ...] = (
    Trap("non_monotone_then_returns", "lift that dips negative then recovers must be rejected"),
    Trap("never_closes", "lift that never returns to seat over 720° must be rejected"),
    Trap("mm_labeled_as_inch", "a mm magnitude carrying unit='inch' must not type-check at the boundary"),
    Trap("advertised_lt_050", "cam card with advertised_duration < duration@0.050\" cannot construct"),
    Trap("sparse_as_continuous", "an 8-point lookup masquerading as a continuous function must be rejected"),
    Trap("seam_phantom_jerk", "a CompositeProfile seam must not inject a jerk spike on identical halves (D010)"),
    Trap("fabricated_nose_as_measured", "an invented seat-ramp value must not return MEASURED provenance (C3)"),
    Trap("analysis_imports_source", "no cam_analyzer.analysis module imports cam_analyzer.sources (C1)"),
    Trap(
        "quantity_unsealed_construction",
        "a Quantity built without the module-private mint token must not construct (Pillar A / C3)",
    ),
    Trap(
        "provenance_as_argument",
        "no public value factory may accept a provenance argument (Pillar A / C3)",
    ),
    Trap(
        "measured_confined_to_sources",
        "MEASURED provenance may only be conferred in the source / spec-policy layer (Pillar A / C3)",
    ),
    Trap(
        "cam_angle_as_crank",
        "a cam-frame angle passed where a crank angle is required must not type-check (Pillar B / C6)",
    ),
)
"""The seed corpus. Adding a source or analysis means adding its trap here."""
