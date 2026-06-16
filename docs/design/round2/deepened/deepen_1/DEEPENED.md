---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: deepener-author-001

# Deepen Pick 1 - Typed Boundary

## Sketch
The ranked pick is to make the `CamProfile` boundary typed enough that downstream analysis can never receive an unqualified bare number by accident. Every profile query returns a frozen value that carries magnitude, unit, crank-or-cam frame, provenance, and per-query confidence, and arithmetic on those values preserves the weakest confidence stamp. The profile facade still feels like the normal way to ask questions - `lift_at`, `duration_at_lift`, `events_at_lift`, derivative queries - but those calls return values that already know whether they came from measured data, cam-card inference, or extrapolation. Analysis modules compare typed values to typed thresholds, so piston-to-valve, spring, DCR, and report code do not need source-specific branches and cannot silently mix units or frames. The implementation should make supported operations pleasant and make raw magnitude extraction visibly exceptional, lintable, and reviewable. The first milestone can then build a crude cam-card approximation without pretending it is measured: the curve is usable through the same interface, but every returned value exposes its inferred quality.

## Load-bearing risk
The load-bearing risk is ergonomics laundering: if the typed path is clumsy, builders will unwrap `.magnitude` early, pass floats through convenience utilities, and erase the exact unit, frame, and provenance guarantees the boundary exists to protect.

## First concrete step
Create `cam/domain/quantity.py` with `Unit`, `Frame`, `Confidence`, and a frozen generic `Quantity`, then define the initial `CamProfile` protocol/facade so all public query methods return only typed quantities or structured typed results.

## Child ideas

1. Add a small typed-threshold library for safety rules, such as minimum intake clearance, exhaust clearance, coil-bind margin, and retainer-guide clearance, so comparisons stay in the typed path.
2. Make raw magnitude access intentionally explicit, for example `unsafe_magnitude_for_plotting()`, and add a grep/lint rule that forbids it outside adapters, plotting, and serialization.
3. Add confidence-aware reducers like `min_value`, `integral`, and `crossings_at_lift` that return both the numeric answer and the weakest region that influenced it.
4. Provide a report-only formatter that turns typed values into human-readable strings with unit, frame, and confidence badges, removing the common reason to unwrap values in report code.
5. Prototype a `DualProfileComparison` that runs inferred and measured profiles through identical typed queries and reports where a downstream verdict changes even though the analysis code did not.