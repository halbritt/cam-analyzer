# cam-analyzer Architecture Map

One navigable map of the system. It orients a fresh agent or human without the
full doc tour; it does **not** replace the product boundary in
[`Camshaft_Analysis_Spec.md`](Camshaft_Analysis_Spec.md), the
[problem brief](docs/design/PROBLEM_BRIEF.md), or the
[decision log](docs/decisions/decision-log.md) — when this map disagrees with
them, they win.

cam-analyzer is a **camshaft analysis toolkit** organized around a single durable
abstraction, the `CamProfile`. The whole point of the design is that the eight
analyses (timing, overlap, dynamic compression, piston-to-valve, spring safety,
acceleration/jerk, install sensitivity, reporting) speak **only** the `CamProfile`
query surface, and that the boundary makes it *structurally* hard — not merely
discouraged — to (a) reach a cam-card assumption from analysis code or (b) treat
an inferred lift value as if it were measured.

## Components (three layers, one direction of dependency)

| Layer (package) | Role |
|---|---|
| `cam_analyzer.sources` | **Producers.** Source-specific ingest: `CamCard` and its parsers (manual, CSV, PDF, OCR), measured-lift import, Cam Doctor, lobe coordinates. Each emits a `CamProfile`; nothing here is importable by analysis. |
| `cam_analyzer.profile` | **The boundary.** The `CamProfile` port (the C5 query surface), the canonical lift model + named operator that backs it (Pillar B), the `Quantity` value type and provenance lattice (Pillar A), and the per-region `ProvenanceMap` (Pillar C). |
| `cam_analyzer.analysis` | **Consumers.** The eight analyses. Each imports only `cam_analyzer.profile` (+ stdlib/numpy). A consumer that needs a source-specific fact is a design bug, caught by a test. |
| `cam_analyzer.conformance` | **The honesty harness (Pillar D).** A frozen adversary corpus of traps every profile must refuse, plus the C1 import guard. This is the durable asset that keeps the other three honest as the codebase grows. |

Dependency rule (enforced, not aspirational): `sources → profile ← analysis`, and
`conformance` may import anything in order to attack it. **Analysis never imports
sources.** See [`tests/test_architecture_boundary.py`](tests/test_architecture_boundary.py).

## The three pillars (one architecture, three facets)

Round 1 converged on these as *not competitors* but three facets of one design;
adopt them together. Full rationale: [`docs/design/ROUND1_SYNTHESIS.md`](docs/design/ROUND1_SYNTHESIS.md).

- **A · Typed provenance boundary** — `Quantity(magnitude, unit, frame, provenance)`.
  `provenance` is an `IntEnum` lattice `MEASURED > INFERRED > EXTRAPOLATED` so
  `min()` *is* the join; arithmetic is defined only between matching `(unit, frame)`
  and the result inherits the weakest input's stamp. Relabeling inferred→measured
  is **unconstructable**. Angles are phantom-typed `Angle[Crank|Cam]`.
- **B · Single canonical representation** — `CamProfile` is a `@final` facade over
  one immutable `CanonicalLiftModel` (normalized 720° samples + a *named* operator:
  `HalfSineApproximation`, `CubicPeriodicSpline`, `MeasuredPeriodicSeries`). Every
  query delegates to that one operator; derivatives differentiate it; reductions
  reduce it. Implementers supply only the canonical object — no method bodies — so
  inconsistent derivatives and sparse-as-continuous are unconstructable.
- **C · Per-region fitness + first-class ignorance** — queries return a value
  resolved against an interval `ProvenanceMap` (`bisect`, O(log N)): e.g.
  `[0,15]:MEASURED`, `[15,345]:EXTRAPOLATED`. Derivative provenance auto-downgrades
  when sampling density can't support differentiation (Nyquist). A consumer asks
  `is_good_enough_for(AnalysisKind)` without coupling to the source; safety
  consumers must pattern-match the unsupported case.
- **D · Conformance by adversary corpus** — the frozen suite of traps a profile
  must refuse *is* the spec of correctness. It converts C1/C3/C4 from reviewer
  vigilance into CI.

## The boundary contract (C5 surface)

```
lift_at(Angle[Crank]) -> Quantity[Lift]          events_at_lift(Quantity[Lift]) -> [Angle[Crank], …]
velocity_at(Angle[Crank]) -> Quantity[Velocity]  duration_at_lift(Quantity[Lift]) -> Angle[Crank]
acceleration_at(...) -> Quantity[Accel]          max_lift() -> Quantity[Lift]
jerk_at(...) -> Quantity[Jerk]                   area_under_curve() -> Quantity[Area]
```

Every return is a `Quantity` (or `Angle`) carrying unit, frame, and a *computed*
provenance — never a bare `float`. *How* a profile is backed is open; *that*
analyses speak only this language is fixed (C5).

## Domain model (who owns what)

- **`CamCard`** — the sparse published timing specs (peak lift, durations, lobe
  centers, lash, events). A source-layer entity. Analysis cannot see it.
- **`CamProfile`** — the continuous lift function over crank angle. The boundary.
- **`Valvetrain`, `EngineGeometry`, `ValveGeometry`, `SpringPackage`** — the
  physical context an analysis needs *in addition to* a profile (geometry, masses,
  clearances). Source-agnostic value/aggregate types.
- **`Quantity`, `Angle`, `Provenance`, `ProvenanceMap`** — value objects (Pillars
  A/C). Immutable, equality-by-value, no setters.

See [`docs/reference/ubiquitous-language.md`](docs/reference/ubiquitous-language.md)
for the canonical definitions and [`docs/explanation/domain-driven-design.md`](docs/explanation/domain-driven-design.md)
for the aggregate-root / value-object framing.

## What this design deliberately does *not* settle

Carried into round 2 as open (not failures — open):

- How to make the provenance-carrying path *strictly more convenient* than bare
  floats, so the guarantee is un-strippable in practice, not just in the types
  (the `.magnitude` "laundry utility" escape hatch — flagged by all three models).
- What `CamProfile` owes a consumer when the analysis verdict is a **cliff
  function** of the profile (PTV contact, spring float): "swap without code change"
  must not be oversold as "swap without changing the verdict."

## Where to go deeper

1. [`Camshaft_Analysis_Spec.md`](Camshaft_Analysis_Spec.md) — the product boundary (source of truth).
2. [`docs/reference/ubiquitous-language.md`](docs/reference/ubiquitous-language.md) — the vocabulary the code must agree with.
3. [`docs/decisions/decision-log.md`](docs/decisions/decision-log.md) — why the boundary is shaped this way.
4. [`docs/index.md`](docs/index.md) — every doc, one line each.
