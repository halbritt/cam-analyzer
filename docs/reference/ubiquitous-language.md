# cam-analyzer Ubiquitous Language

The canonical glossary. Code (class, method, parameter, and error names),
documentation, and conformance-trap names use these words and these meanings.
Drift between code and this file is a bug, not a stylistic choice. See
[`../explanation/domain-driven-design.md`](../explanation/domain-driven-design.md)
for how these terms map onto aggregate roots and value objects.

## The boundary

| Term | Meaning |
|---|---|
| **CamProfile** | The continuous valve-lift function over crank angle and its derivatives — the *only* language analyses speak. A `@final` facade over one `CanonicalLiftModel`. Not a "class with eight methods"; a sealed type whose queries are generated from one operator. |
| **C5 surface** | The fixed eight-query vocabulary: `lift_at`, `velocity_at`, `acceleration_at`, `jerk_at`, `events_at_lift`, `duration_at_lift`, `max_lift`, `area_under_curve`. *That* analyses speak only this is fixed; *how* it is backed is open. |
| **CanonicalLiftModel** | The single immutable object backing a profile: normalized 720° samples + exactly one named `LiftOperator`. The only thing a source implementer supplies. |
| **LiftOperator** | The named operator a profile delegates to: `PolynomialMotionLawCamCardOperator` (the M1 cam-card operator), and the planned `CubicPeriodicSpline`, `MeasuredPeriodicSeries`, … A profile delegates `evaluate` and `derivative` to it; **the operator hand-writes `evaluate` and `derivative` independently** — derivative consistency is operator-trusted, not constructed (see [`adr-derivatives-operator-trusted.md`](../decisions/adr-derivatives-operator-trusted.md)). `operator.derivative(order=n)` answers only when the operator exposes a justified derivative; cam-card motion-law derivatives are model-derived and provenance-capped, not measured. |

## Sources (the producer layer)

| Term | Meaning |
|---|---|
| **CamCard** | The sparse *published* timing specs (peak lift, advertised duration, duration @0.050″, lobe centers, lash, open/close events). A source-layer record. **Never importable by analysis (C1).** |
| **Source** | Anything that produces a `CamProfile`: cam card, measured dial-indicator/degree-wheel lift, Cam Doctor export, scanned lobe coordinates, valvetrain-dynamics model. A source emits a profile and is invisible past the boundary. |
| **profiles_from_cam_card** | The Milestone-1 cam-card ingest entry point (`src/cam_analyzer/sources/cam_card.py`). It returns side-specific `CamProfile` objects backed by `PolynomialMotionLawCamCardOperator`, a constrained piecewise-quintic cam-card motion law that exactly fits the published timing anchors while preserving provenance. (The former `CamCardApproxProfile` / `HalfSineCamCardOperator` compatibility names have been removed.) |
| **MeasuredValveLiftProfile / CamDoctorProfile / LobeCoordinateProfile** | Profiles backed by measured operators; they swap in for the approximation with **zero** analysis-code change (C4). |

## Values that cross the boundary

| Term | Meaning |
|---|---|
| **Quantity[Unit]** | The stamped scalar every numeric query returns: a sealed, phantom-typed value object carrying `unit`, `frame`, and `provenance` (`src/cam_analyzer/quantity.py`). **Not** a `float` subclass — RFC 0001 §9 proved a float subclass cannot make `mm + inch` a type error. Construction is sealed (minted only by the `measured`/`inferred`/`extrapolated` acquisition factories; no `provenance=` argument). No bare `float` crosses the boundary unless a caller explicitly writes `float(value)`; there is no `.magnitude` field. Arithmetic between matching `(unit, frame)` values inherits the weakest input provenance (the lattice join). |
| **ProvFloat** | A **back-compat annotation alias** for `Quantity`: `ProvFloat = Quantity[Any]` (`src/cam_analyzer/quantity.py:230`). It was the original *float-subclass* name in the round-2 sketch; RFC 0001 retired that approach. New code annotates with `Quantity[Unit]`. |
| **Angle[Crank \| Cam]** | A phantom-typed angle. Crank vs cam is a *type* distinction, so a mix-up is a type error, not a silent 2× bug. |
| **Provenance** | An `IntEnum` lattice: `MEASURED(2) > INFERRED(1) > EXTRAPOLATED(0)`. `min()` is the join. **No setter** — provenance is computed from inputs, never asserted. Distinguishes measured from inferred at every observable value (C3). |
| **ProvenanceMap** | An interval map (crank region → provenance), `bisect` / O(log N). e.g. `[0,15]:MEASURED`, `[15,345]:EXTRAPOLATED`. The per-region fitness backbone. |
| **Unit** | `inch \| mm \| degree \| …`. Explicit at the boundary (C6). |
| **Frame** | Which reference a value is in: `valve_side \| cam_side`, seat vs 0.050″ timing, lash applied or not, TDC reference. Explicit and non-guessable (C6). |

## Fitness & honesty

| Term | Meaning |
|---|---|
| **is_good_enough_for(AnalysisKind)** | A consumer's question to a profile: is this profile adequate for *my* analysis, without coupling to where it came from (G5)? |
| **AnalysisKind** | The analysis a fitness check is about: `timing`, `overlap`, `dcr`, `ptv`, `spring_safety`, `jerk`, `sensitivity`, `report`. |
| **Refusal** | A first-class result: a query (or `answer`) may *refuse* with a reason and "what would fix it" rather than fabricate a number. Refusal is data, not an exception to swallow. |
| **Conformance corpus** | The frozen suite of traps a profile must refuse (or be unable to construct). The durable asset; correctness is defined by attacks withstood (Pillar D). |
| **Cliff function** | An analysis whose verdict is discontinuous in the profile (PTV contact, spring float): a plausible source swap can flip "safe"→"contact" while code is byte-identical. C4 must not be sold as verdict stability. |

## The invariants (C1–C6)

| ID | Invariant |
|---|---|
| **C1** | One-way dependency: analysis depends only on `CamProfile`; never imports a source, parser, or source type. |
| **C2** | Milestone discipline: Milestone 1 is `cam card → CamProfile`, not `cam card → DCR`. |
| **C3** | Measured ≠ inferred: every observable value can be told apart as measured or inferred. |
| **C4** | Hot-swappable source: swapping an approximate profile for a measured one changes no analysis code (but *may* change the answer — see *cliff function*). |
| **C5** | Stable consumer vocabulary: the eight queries are fixed; backing is open. |
| **C6** | Unambiguous frames & units: crank vs cam, valve- vs cam-side, seat vs 0.050″, inch vs mm — explicit and non-guessable. |

## Analyses (the consumer layer)

`timing` · `overlap` · `dynamic_compression` (DCR) · `piston_to_valve` (PTV) ·
`spring_safety` · `jerk` · `install_sensitivity` · `report`. Each consumes only
the C5 surface plus source-agnostic geometry/spec aggregates.

## Adding to the model

1. **Glossary first** — add the term here with its load-bearing meaning.
2. **Classify it** — aggregate root, value object, or domain rule? The design note / ADR says which.
3. **Encode the rule** — if it is a boundary rule, add a conformance trap; if a value, it is immutable and setter-free.
4. **Name it consistently** — code, errors, and tests use exactly this word.
5. **Cite it** — the decision log and design notes reference the glossary entry.
