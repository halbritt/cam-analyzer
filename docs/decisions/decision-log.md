# Decision Log

Status: draft
Date: 2026-06-16

This log records the product and architecture decisions for `cam-analyzer`.
Decisions originate either from the original request
([`prompt.md`](../../prompt.md), [`Camshaft_Analysis_Spec.md`](../../Camshaft_Analysis_Spec.md))
or from the two divergent-ideation design rounds
([`design/ROUND1_SYNTHESIS.md`](../design/ROUND1_SYNTHESIS.md),
[`design/round2/IDEATION_SYNTHESIS.md`](../design/round2/IDEATION_SYNTHESIS.md)).
They sharpen as the shared understanding does.

Status values (the *decision* lifecycle):

```text
proposed     under design; not yet a commitment
accepted     a commitment the code and reviews must honor
deferred     a good idea, deliberately not now
rejected     considered and ruled out (kept as provenance)
superseded   replaced by a later accepted decision (named in Consequences)
```

> **`accepted` is a decision word, not a build word.** A decision can be an
> accepted commitment while the *code that honors it* does not yet exist.
> To stop "accepted" from being read as "implemented", every row also carries a
> **build-status stamp** (lifted from the project's own `MEASURED > INFERRED >
> EXTRAPOLATED` lattice applied to *build state*):
>
> - **VERIFIED** — a passing executable witness exists (a named test / `file:line` / a CLI command with expected output).
> - **ASSERTED** — a doc/decision says so; no executable witness pins it.
> - **DESIGNED** — explicitly not built; the decision is accepted but the build is deferred.
>
> The cross-repo manifestation is [`docs/CLAIMS_LEDGER.md`](../CLAIMS_LEDGER.md),
> which stamps every decision/feature/guard with its status and witness.

Decisions sourced from `prompt.md` / the spec are **accepted** (they are the
original request). The round-1 synthesis settled the boundary skeleton
(Pillars A/B/C + the conformance discipline D) — now **accepted**. Round 2
resolved the two questions round 1 left open (D012/D013) into a build plan and
is **accepted** as the design direction. D012 has partly landed in code:
`quantity.py` defines `ProvFloat` **as a sealed-`Quantity[Any]` alias** (not a
`float` subclass — RFC 0001 §9 proved a float subclass cannot make `mm + inch` a
type error), while `Quantity` is the real value type. D013 is **accepted but not
built** (`DESIGNED`): no two-curve verdict-agreement code exists yet. Rejected
rows are the round-1 and round-2 *traps* — recorded so they are not re-proposed.

## Decisions

`Status` is the decision lifecycle; `Build` is the build-status stamp
(VERIFIED / ASSERTED / DESIGNED) with its witness named in Consequences.

| ID | Status | Build | Decision | Reason | Consequences | Revisit Trigger |
|---|---|---|---|---|---|---|
| D001 | accepted | VERIFIED | **One-way dependency (C1).** Every analysis module imports only `CamProfile`; never a `CamCard`, parser, source format, or source type. | The original request's "most important requirement"; the whole durability claim rests on it. | Package layout is `sources → profile ← analysis`; enforced by a test, not review (see [D007](#d007--standalone)). Witness: `tests/test_architecture_boundary.py` (C1 import guard) + the `analysis_imports_source` corpus trap. | A consumer genuinely needs a source fact a profile cannot express. |
| D002 | accepted | VERIFIED | **Measured ≠ inferred (C3), carried with the value.** Provenance travels *in* the returned value, not as a profile-level sidecar tag. | The request demands every value be distinguishable as measured/inferred; a sidecar tag cannot describe a per-region curve. | Queries return stamped boundary values (`Quantity[Unit]`, with `ProvFloat` as a back-compat alias) carrying provenance; see D004/D006. Witness: the sealed-construction traps (`tests/test_conformance_traps.py::test_quantity_unsealed_construction_is_rejected`, `::test_no_public_value_factory_confers_provenance_by_argument`) plus the confined-conferral trap `::test_measured_conferral_is_confined_to_the_source_layer`, which now flags both `measured()` and a MEASURED-carrying `Quantity._mint(...)` outside the source layer + `analysis/safety.py`. | — |
| D003 | accepted | VERIFIED | **Milestone 1 is `cam card → CamProfile` (C2).** The first durable output is a profile, not an analysis result. | The request fixes this explicitly; it keeps the boundary, not a DCR number, as the deliverable. | M1 ships `profiles_from_cam_card()` backed by `PolynomialMotionLawCamCardOperator`. DCR/PTV/spring are downstream. Witness: `tests/test_cam_card_source.py` exercises `profiles_from_cam_card(CamCard.wr250r_reference())`. | — |
| D004 | accepted | VERIFIED | **Typed boundary (Pillar A).** No bare `float` crosses the boundary; every value is a stamped value carrying unit, frame, and a computed monotone `Provenance` lattice (`MEASURED>INFERRED>EXTRAPOLATED`) with **no setter**. Angles are phantom-typed `Angle[Crank\|Cam]`. | Makes mislabeling (inferred→measured), unit, and frame errors *unconstructable* rather than discouraged (G2, C3, C6). | A sealed `Quantity[Unit]` value object in `quantity.py` + `mypy --strict`; **refined by RFC 0001** (provenance conferred, not declared; units/frames in the type). Witness: the sealed-mint / no-`provenance=` / phantom-type traps in `tests/test_conformance_traps.py`. | — |
| D005 | accepted | ASSERTED | **Single canonical representation (Pillar B).** `CamProfile` is a `@final` facade over one immutable `CanonicalLiftModel` + a *named* operator; the eight queries are *generated* projections that delegate to that one operator. | Implementers supply only the canonical object, so sparse-as-continuous is unconstructable (that one *is* trapped). | No subclass method hooks; measured data swaps the operator with zero downstream change (C4). **Derivative consistency is operator-TRUSTED, not constructed:** an operator hand-writes both `evaluate()` and `derivative()` as *independent* methods (`src/cam_analyzer/sources/cam_card.py:138`, `:149`) — nothing differentiates `evaluate` to *check* `derivative`, so "inconsistent derivatives are unconstructable" over-claims. The honest claim is that consistency is the operator author's discipline. See [`adr-derivatives-operator-trusted.md`](./adr-derivatives-operator-trusted.md). Witness for the part that *is* built: the `sparse_as_continuous` trap (`tests/test_conformance_traps.py::test_sparse_as_continuous_refuses_eight_point_lookup`). | A finite-difference-consistency trap lands; or a source cannot be expressed as samples + one operator. |
| D006 | accepted | VERIFIED | **Per-region fitness + first-class ignorance (Pillar C).** Provenance is per query / per crank region / per derivative order via a `ProvenanceMap`; derivative provenance auto-downgrades past Nyquist support; consumers ask `is_good_enough_for(AnalysisKind)`. | A cam-card profile is near-certain at its anchors and fabricated between; a single tag is a lie (D008). | Safety consumers must pattern-match the unsupported case; fabricated seat-ramp values cannot be laundered into "safe". Witness: `tests/test_provenance_map.py`; PTV/spring return `UNDECIDABLE_FROM_CAM_CARD` via `is_good_enough_for` in `tests/test_safety_and_reporting.py`. | — |
| D007 | accepted | VERIFIED (partial) | **Conformance by adversary corpus (Pillar D).** ★ C1/C3/C6 are enforced by a frozen suite of traps a profile must refuse + an import guard — not reviewer vigilance. Standalone ADR: [`D007.md`](D007.md). | The durable asset is the trap suite, not the interface; it is the only thing that keeps A/B/C honest as the code grows (G2, G4). | A `conformance/` corpus + `tests/test_architecture_boundary.py` ship with the spec; correctness is defined by attacks withstood. **9 of the ~12 traps are executable** (`_EXECUTABLE_TRAPS` in `tests/test_conformance_traps.py:23`); the rest (e.g. `seam_phantom_jerk`, D010) stay declared-only until their machinery lands. A **coverage guard** (`tests/test_conformance_traps.py::test_every_corpus_trap_is_executable_or_explicitly_declared_only`) asserts every corpus trap is executable *or* explicitly listed in `conformance.DECLARED_ONLY`, so the gap can't grow silently. C2/C4/C5 remain conventions, not tests. | — |
| D008 | rejected | n/a | **Confidence as a single scalar tag.** A per-profile `confidence="high\|medium\|low"` field. | Refuted independently by three branches: confidence is a property of each query at each crank angle, not of the profile. | Superseded by D006 (per-region provenance). | — |
| D009 | accepted | ASSERTED | **C4 is code-stability, not verdict-stability.** "Swap source without changing code" must never be sold as "swap without changing the answer." | PTV-contact and spring-float are cliff functions; a plausible measured curve can flip a verdict while code stays byte-identical. | Docs and reports must state this (they do — see `domain-driven-design.md`). The constructive enforcement (two-curve bracketing, D013) is `DESIGNED`, not built; today this is an *asserted* discipline, not a tested guard. | — |
| D010 | proposed | DESIGNED | **Blends must prove derivative continuity.** Any `CompositeProfile` joining measured + inferred regions must prove C¹/C² continuity at the seam. | A naive blend injects phantom acceleration/jerk at the join → fake spring-float findings. | A conformance trap: identical halves with a seam must not produce a `jerk_at` spike. **Declared-only** — `seam_phantom_jerk` is in the corpus (`src/cam_analyzer/conformance/__init__.py:50`) but not in `_EXECUTABLE_TRAPS`; no `CompositeProfile` exists yet. | — |
| D011 | deferred | DESIGNED | **Ensemble / reactive-evidence-graph profile (Cluster E).** One profile exposing an ensemble of feasible curves; an invalidation graph rederiving results from evidence nodes. | The right *infinite-budget* shape, but premature for Milestone 1 — overbuild before measured data exists. | Revisit once measured data and multiple sources are real. | Measured data + ≥2 live sources exist. |
| D012 | accepted | VERIFIED (revised by RFC 0001) | **Ergonomics-as-integrity.** Every query returns a stamped scalar carrying one `Provenance`; there is no `.magnitude` field to strip, arithmetic propagates the lattice-`min` stamp, and the sole bare-scalar exit is `float(x)`. | Round-2 question 1: the honest value must not cost more than the lie, or the guarantee is bypassed (refines D004). | **Revised by RFC 0001 §9:** round 2 proposed a `float` *subclass*, but a `mypy --strict` spike proved a float subclass cannot make `mm + inch` a type error (it is-a `float`, so the unit erases). The value is therefore a sealed, phantom-typed `Quantity[Unit]` value object; **`ProvFloat` is now `Quantity[Any]`, a back-compat alias** (`src/cam_analyzer/quantity.py:230`), *not* a float subclass. Witness: the sealed-construction + phantom-type traps in `tests/test_conformance_traps.py`. NumPy interop (`ProvArray`, D017) remains `DESIGNED`. | Vectorized math escapes the scalar stamp without D017. |
| D013 | accepted | DESIGNED | **Honesty-under-discontinuity → bracketed verdict-agreement.** For cliff analyses (PTV, spring float) build the earliest- and latest-plausible curves from the card's tolerances, run the identical analysis on both, and publish only whether the *verdict* agrees; a flip emits `UNDECIDABLE FROM CAM CARD`, never a number. | Round-2 question 2: honors D009 ("swap ≠ verdict-stable") by construction; strongest cross-family signal in the run. | **Accepted as the design direction but NOT BUILT.** No two-curve comparison exists: `analysis/piston_to_valve.py` and `analysis/spring_safety.py` are *single-curve* PASS/FAIL/`UNDECIDABLE_FROM_CAM_CARD` paths (`evaluate_piston_to_valve`, `evaluate_spring_safety`); there is no earliest/latest tolerance-envelope loop. Building it is deferred roadmap work; the tolerance envelope itself will need provenance or it manufactures false agreement. | A two-curve verdict-comparison loop is implemented. |
| D014 | accepted | VERIFIED (partial) | **Derivative-capability matrix + Nyquist gate.** Each operator publishes crank-interval → max justified derivative order (computed from sample spacing, not declared); `velocity/acceleration/jerk_at` returns a stamped value on pass, a structured `Refusal{requested_order, max_supported, reason, remedy}` on fail. | Closes Pillar B's named failure mode — a smooth cam-card approximation emitting authoritative jerk fiction; it is the gate PTV/spring sit behind. | The `Refusal` path and `max_supported_derivative` gate are implemented (`src/cam_analyzer/sources/cam_card.py`). The M1 cam-card operator now supplies C2-continuous motion-law derivatives through jerk, provenance-capped as model-derived answers; safety fitness gates still reject the cam-card profile for derivative-sensitive cliff conclusions. Witness: `tests/test_cam_card_source.py`, `tests/test_approximate_derivatives.py`, `tests/test_canonical_profile.py`, `tests/test_profile_quality.py`. | Over-restriction drives bypass; or model-derived derivatives start being treated as measured dynamics. |
| D015 | accepted | VERIFIED | **Separate the threshold owner from the curve owner.** ★ A named *threshold policy* owns *where safe becomes unsafe*, distinct from the operator that owns *what the lift is*. | The cliff is a decision with an owner, not a property of the curve; makes D013's `UNDECIDABLE` accountable — you learn *whose* threshold flipped. | Structural separation, not new machinery; gives the report a place to attribute every cliff verdict. Built: `ThresholdPolicy`/`SpringThresholdPolicy` with an `owner` field (`analysis/piston_to_valve.py`, `analysis/spring_safety.py`, `analysis/safety.py`). | — |
| D016 | accepted | VERIFIED | **`Answer \| Refusal` at every safety-facing call.** Clearance/spring modules may not call bare `lift_at()`; they request an answer that may formally refuse. | Round-2 runner-up (B4.1): the connective tissue wiring D012/D014 into analysis with no bare-float side door. | A `Refusal` is a first-class return, not an exception to swallow. Built: PTV/spring evaluators return `… \| Refusal`; `velocity/acceleration/jerk_at` return `Answer`. Witness: `tests/test_safety_and_reporting.py`. | — |
| D017 | proposed | DESIGNED | **`ProvArray` — provenance through NumPy.** A stamped array (`__array_ufunc__`/`__array_wrap__` + a parallel stamp array) so the value-layer guarantee survives vectorization. | `np.asarray` silently drops the stamp — the `.magnitude` leak relocated to where the safety-critical derivative math runs. | Mandatory follow-on to D012; without it D012 guards only the place provenance doesn't matter. **Not built** — no `ProvArray` exists in `src` (RFC 0001 Pillar D follow-on). | — |
| D018 | deferred | DESIGNED | **Value-of-information work orders.** When a verdict bracket straddles the cliff, the profile emits the single cheapest measurement that would collapse it (e.g. "measure nose lift at 110° to ±0.002″"). | Turns every `Refusal`/`UNDECIDABLE` from a dead end into active experiment design; bracket width + capability matrix + threshold policy already hold the inputs. | A future divergence branch; out of scope for M1 (and depends on D013 brackets, also `DESIGNED`). | Measured-data ingest exists. |
| D019 | accepted | VERIFIED (partial) | **Honest visualization projection and rendering grammar.** Charts consume a source-blind JSON projection plus a provenance/refusal rendering grammar; renderers may draw, segment, or style the projection but may not recompute source facts or upgrade provenance. | RFC 0004 turns "pretty charts" into a boundary-preserving projection problem: every plotted value carries unit/frame/provenance or a refusal, so chart output cannot launder cam-card extrapolation into measured-looking curves. | Built: `analysis/projection.py` samples only `CamProfile` C5 queries; `analysis/profile_quality.py` adds threshold durations, heuristic p50/p95 confidence bands, and quality warnings; `visualization/grammar.py` owns the provenance legend; `visualization/svg.py` renders a full-cycle overlap-centered -360° to +360° static SVAJ SVG with hard event markers, threshold lines, summary panel, validation section, and secondary canonical 0° to 720° overview from the same projection samples; `cam-analyze --charts json` exposes the static projection and `cam-analyze --charts svg` emits the SVG. Witness: `tests/test_visualization_projection.py`, `tests/test_visualization_grammar.py`, `tests/test_visualization_svg.py`, `tests/test_cli.py`, `tests/test_profile_quality.py`, and `tests/test_architecture_boundary.py`. **Not built:** ECharts adapter, crop-proof ledger, calibrated uncertainty-band math, PTV collision chart, "go measure THIS", and web UI. | A renderer adapter needs a fact not expressible through `CamProfile`, or the chart suite expands beyond the current SVAJ output. |

## Round-2 rejected ideas (do not re-propose)

Surfaced and ruled out in round 2 (see
[`round2/IDEATION_SYNTHESIS.md`](../design/round2/IDEATION_SYNTHESIS.md) trap list):

- **Cache-coherency / invalidation protocol** — profiles are immutable and recompute is cheap; pure infra tax for M1.
- **Lossy precision-as-stamp** — encoding provenance by dropping digits corrupts the number and breaks reproducibility.
- **NaN-poison companion** — `nan` launders trivially and discards the *reason* for a refusal.
- **Entropy token-bucket** — needs a calibrated uncertainty model M1 lacks; re-smuggles the global confidence budget D008 killed.
- **MPU privilege segmentation** — duplicates what provenance + refusal-gating give; fold the intent into D014.
- **Append-only audit log of naked floats** — concedes the laundering and relies on a log no analysis reads; contradicts D012.
- **AST import-graph audit at boot** — a runtime tax; the intent is correct as a CI import-linter test (D007), not a boot audit.

## D007 — standalone

See [`D007.md`](D007.md) for the full record of the ★ non-obvious-but-viable
decision (conformance by adversary corpus), which the round-1 synthesis named as
the choice that keeps the other three pillars honest.
