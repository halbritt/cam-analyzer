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
| `cam_analyzer.profile` | **The boundary.** The `CamProfile` port (the C5 query surface), the canonical lift model + named operator that backs it (Pillar B), the sealed `Quantity[Unit]` stamped scalar (`ProvFloat` is a back-compat alias) and provenance lattice (Pillar A), and the per-region `ProvenanceMap` (Pillar C). |
| `cam_analyzer.analysis` | **Consumers.** The eight analyses. Each imports only `cam_analyzer.profile` (+ stdlib/numpy). A consumer that needs a source-specific fact is a design bug, caught by a test. |
| `cam_analyzer.conformance` | **The honesty harness (Pillar D).** A frozen adversary corpus of traps every profile must refuse, plus the C1 import guard. This is the durable asset that keeps the other three honest as the codebase grows. |

Dependency rule (enforced, not aspirational): `sources → profile ← analysis`, and
`conformance` may import anything in order to attack it. **Analysis never imports
sources.** See [`tests/test_architecture_boundary.py`](tests/test_architecture_boundary.py).

## The three pillars (one architecture, three facets)

Round 1 converged on these as *not competitors* but three facets of one design;
adopt them together. Full rationale: [`docs/design/ROUND1_SYNTHESIS.md`](docs/design/ROUND1_SYNTHESIS.md).

- **A · Typed provenance boundary** — a sealed, phantom-typed `Quantity[Unit]`
  (RFC 0001). `provenance` is an `IntEnum` lattice `MEASURED > INFERRED >
  EXTRAPOLATED` so `min()` *is* the join; arithmetic is defined only between
  matching `(unit, frame)` values and the result inherits the weakest input's
  stamp. Construction is **sealed**: a `Quantity` can't be built without the
  module-private mint token, provenance is *conferred* by acquisition factories
  (`measured`/`inferred`/`extrapolated`) rather than passed as an argument, and
  `measured()` conferral is confined to **the source layer + `analysis/safety.py`**
  (the spec-policy authority) — enforced by the `measured_confined_to_sources`
  trap (`tests/test_conformance_traps.py::test_measured_conferral_is_confined_to_the_source_layer`)
  — so relabeling inferred→measured is genuinely **unconstructable** (not just
  discouraged). The
  unit is a phantom *type* parameter and angles are phantom-typed
  `Angle[Crank|Cam]`, so `mm + inch` and cam-as-crank are `mypy` errors. There is
  no `.magnitude`; the one bare-scalar exit is `float(x)`. `ProvFloat` is now a
  back-compat alias for `Quantity`.
- **B · Single canonical representation** — `CamProfile` is a `@final` facade over
  one immutable `CanonicalLiftModel` (normalized 720° samples + a *named* operator:
  `SinePowerCamCardOperator` today; `CubicPeriodicSpline`, `MeasuredPeriodicSeries`
  planned). Every query delegates to that one operator. **Sparse-as-continuous is
  unconstructable** (trapped, `VERIFIED`). **Derivative consistency, however, is
  operator-TRUSTED, not constructed** (`ASSERTED`): an operator hand-writes
  `evaluate` and `derivative` as *independent* methods (`sources/cam_card.py:138`,
  `:149`); nothing differentiates one to check the other, so the stronger claim
  "inconsistent derivatives are unconstructable" over-states what the code
  guarantees. See [`adr-derivatives-operator-trusted.md`](docs/decisions/adr-derivatives-operator-trusted.md).
- **C · Per-region fitness + first-class ignorance** — queries return a value
  resolved against an interval `ProvenanceMap` (`bisect`, O(log N)): e.g.
  `[0,15]:MEASURED`, `[15,345]:EXTRAPOLATED`. Derivative provenance auto-downgrades
  when sampling density can't support differentiation (Nyquist). A consumer asks
  `is_good_enough_for(AnalysisKind)` without coupling to the source; safety
  consumers must pattern-match the unsupported case.
- **D · Conformance by adversary corpus** — the suite of traps a profile must
  refuse or be unable to construct *is* the spec of correctness. **9 of the ~12
  traps are executable** (`_EXECUTABLE_TRAPS`, `tests/test_conformance_traps.py:23`;
  `VERIFIED`), converting C1 (import guard), C3 (sealed mint, no `provenance=`,
  `measured()`-confined-to-source-layer-plus-`analysis/safety.py`), and C6
  (cross-unit and cam-as-crank `mypy` traps) from reviewer vigilance into CI; the
  rest (e.g. `seam_phantom_jerk`/D010) stay **declared-only** (`DESIGNED`) until
  their machinery lands.

## The boundary contract (C5 surface)

```
lift_at(Angle[Crank]) -> ProvFloat              events_at_lift(ProvFloat) -> [Angle[Crank], …]
velocity_at(Angle[Crank]) -> Answer             duration_at_lift(ProvFloat) -> Angle[Crank]
acceleration_at(...) -> Answer                  max_lift() -> ProvFloat
jerk_at(...) -> Answer                          area_under_curve() -> ProvFloat
```

Every numeric answer is a `ProvFloat` carrying unit, frame, and a *computed*
provenance, or a formal `Refusal` through the `Answer` alias where the query may
not be justified. The only explicit escape to a bare scalar is `float(value)`.
*How* a profile is backed is open; *that* analyses speak only this language is
fixed (C5).

## Domain model (who owns what)

- **`CamCard`** — the sparse published timing specs (peak lift, durations, lobe
  centers, lash, events). A source-layer entity. Analysis cannot see it.
- **`CamProfile`** — the continuous lift function over crank angle. The boundary.
- **`Valvetrain`, `EngineGeometry`, `ValveGeometry`, `SpringPackage`** — the
  physical context an analysis needs *in addition to* a profile (geometry, masses,
  clearances). Source-agnostic value/aggregate types.
- **`Quantity[Unit]`, `Angle[Frame]`, `Provenance`, `ProvenanceMap`** — value
  objects (Pillars A/C). Immutable, equality-by-value, sealed construction, no
  provenance setters. `ProvFloat` is a back-compat annotation alias for
  `Quantity`.

See [`docs/reference/ubiquitous-language.md`](docs/reference/ubiquitous-language.md)
for the canonical definitions and [`docs/explanation/domain-driven-design.md`](docs/explanation/domain-driven-design.md)
for the aggregate-root / value-object framing.

## Round 2 — resolved (the build plan)

Round 2 (`cam_profile_architecture_r2`,
[`docs/design/round2/IDEATION_SYNTHESIS.md`](docs/design/round2/IDEATION_SYNTHESIS.md))
took the pillars above as settled and resolved the two questions round 1 left
open, under one rule: **a value — or a verdict — may leave the boundary only if
its fitness is proven; the instant it can't be, the boundary says so loudly.**
Build order (each pick sits on the prior):

1. **Ergonomics-as-integrity** (D012) — `VERIFIED`. Every query returns a sealed,
   phantom-typed `Quantity[Unit]` carrying one `Provenance` stamp. **Revised by
   RFC 0001 §9:** round 2 sketched a `float` *subclass*, but a float subclass
   cannot make `mm + inch` a type error, so the value is a value object, **not** a
   float subclass; `ProvFloat = Quantity[Any]` is a back-compat alias. There is no
   `.magnitude` to strip; arithmetic propagates the lattice-`min` stamp; the only
   bare-scalar exit is `float(x)`. Follow-on `ProvArray` (D017) for NumPy is
   `DESIGNED` (not built).
2. **Derivative-capability matrix + Nyquist gate** (D014) — `VERIFIED` (partial).
   `velocity/acceleration/jerk_at` answer only where sample density supports that
   order, else return a structured `Refusal`. Closes Pillar B's "smooth cam-card
   approximation emits authoritative jerk" failure mode.
3. **Bracketed verdict-agreement** (D013) — **`DESIGNED`, not built.** The intent:
   run cliff analyses (PTV, spring float) on the earliest- and latest-plausible
   curves from the card's tolerances and publish only whether the *verdict* agrees;
   a flip emits `UNDECIDABLE_FROM_CAM_CARD`, never a number. **In code today,
   PTV/spring are *single-curve* PASS/FAIL/UNDECIDABLE** (`analysis/piston_to_valve.py`,
   `analysis/spring_safety.py`); there is no two-curve tolerance-envelope loop. The
   round-1 "swap ≠ verdict-stable" trap is honored by the single-curve
   `UNDECIDABLE_FROM_CAM_CARD` refusal, not yet by bracketing. Building the bracket
   is deferred roadmap work.

★ **The cliff is in the policy, not the curve** (D015): a named **threshold owner**
(*where* safe becomes unsafe) is separated from the **curve owner** (*what* the lift is),
so a flipped verdict names *whose* threshold moved — making the `UNDECIDABLE`
accountable. The runner-up wiring (`Answer | Refusal` at every safety-facing call, D016),
the round-2 rejected traps, and the value-of-information wildcard (D018) are in the
[round-2 synthesis](docs/design/round2/IDEATION_SYNTHESIS.md) and the
[decision log](docs/decisions/decision-log.md).

## Where to go deeper

1. [`Camshaft_Analysis_Spec.md`](Camshaft_Analysis_Spec.md) — the product boundary (source of truth).
2. [`docs/reference/ubiquitous-language.md`](docs/reference/ubiquitous-language.md) — the vocabulary the code must agree with.
3. [`docs/decisions/decision-log.md`](docs/decisions/decision-log.md) — why the boundary is shaped this way.
4. [`docs/index.md`](docs/index.md) — every doc, one line each.
