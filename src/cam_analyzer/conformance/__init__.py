"""The conformance corpus — the durable asset (Pillar D / D007).

A frozen museum of traps a conformant CamProfile (or CamCard ingest) must *refuse
or be unable to construct*. Correctness is defined by the attacks the boundary
withstands, not by the happy path. Trap names are part of the ubiquitous language.

The traps below are declared (names + intent). Each becomes an executable case as
the implementation lands; the structural C1 trap (`analysis_imports_source`) is
already enforced by tests/test_architecture_boundary.py.
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
)
"""The seed corpus. Adding a source or analysis means adding its trap here."""
