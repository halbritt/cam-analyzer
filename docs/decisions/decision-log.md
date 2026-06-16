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

Status values:

```text
proposed     under design; not yet a commitment
accepted     a commitment the code and reviews must honor
deferred     a good idea, deliberately not now
rejected     considered and ruled out (kept as provenance)
superseded   replaced by a later accepted decision (named in Consequences)
```

Decisions sourced from `prompt.md` / the spec are **accepted** (they are the
original request). The round-1 synthesis settled the boundary skeleton
(Pillars A/B/C + the conformance discipline D) — now **accepted**. Round 2
resolved the two questions round 1 left open (D012/D013) into a build plan and
is **accepted** as the design direction, though no implementation is committed
yet (so the code lags: `quantity.py` still implements the round-1 `Quantity`
form pending the `ProvFloat` refinement of D012). Rejected rows are the round-1
and round-2 *traps* — recorded so they are not re-proposed.

## Decisions

| ID | Status | Decision | Reason | Consequences | Revisit Trigger |
|---|---|---|---|---|---|
| D001 | accepted | **One-way dependency (C1).** Every analysis module imports only `CamProfile`; never a `CamCard`, parser, source format, or source type. | The original request's "most important requirement"; the whole durability claim rests on it. | Package layout is `sources → profile ← analysis`; enforced by a test, not review (see [D007](#d007--standalone)). | A consumer genuinely needs a source fact a profile cannot express. |
| D002 | accepted | **Measured ≠ inferred (C3), carried with the value.** Provenance travels *in* the returned value, not as a profile-level sidecar tag. | The request demands every value be distinguishable as measured/inferred; a sidecar tag cannot describe a per-region curve. | Queries return `Quantity` carrying provenance; see D004/D006. | — |
| D003 | accepted | **Milestone 1 is `cam card → CamProfile` (C2).** The first durable output is a profile, not an analysis result. | The request fixes this explicitly; it keeps the boundary, not a DCR number, as the deliverable. | M1 ships `CamCardApproxProfile` + one `HalfSineCamCardOperator`; DCR/PTV/spring are downstream. | — |
| D004 | accepted | **Typed boundary (Pillar A).** No bare `float` crosses the boundary; every value is a stamped value carrying unit, frame, and a computed monotone `Provenance` lattice (`MEASURED>INFERRED>EXTRAPOLATED`) with **no setter**. Angles are phantom-typed `Angle[Crank\|Cam]`. | Makes mislabeling (inferred→measured), unit, and frame errors *unconstructable* rather than discouraged (G2, C3, C6). | A `quantity.py` value layer + `mypy --strict`; **refined by D012 (`ProvFloat`)** so the value *is* the magnitude (no `.magnitude` to strip). | — |
| D005 | accepted | **Single canonical representation (Pillar B).** `CamProfile` is a `@final` facade over one immutable `CanonicalLiftModel` + a *named* operator; the eight queries are *generated* projections (derivatives differentiate one operator). | Implementers supply only the canonical object, so inconsistent derivatives and sparse-as-continuous are unconstructable. | No subclass method hooks; measured data swaps the operator with zero downstream change (C4). | A source cannot be expressed as samples + one operator. |
| D006 | accepted | **Per-region fitness + first-class ignorance (Pillar C).** Provenance is per query / per crank region / per derivative order via a `ProvenanceMap`; derivative provenance auto-downgrades past Nyquist support; consumers ask `is_good_enough_for(AnalysisKind)`. | A cam-card profile is near-certain at its anchors and fabricated between; a single tag is a lie (D008). | Safety consumers must pattern-match the unsupported case; fabricated seat-ramp values cannot be laundered into "safe". | — |
| D007 | accepted | **Conformance by adversary corpus (Pillar D).** ★ C1/C3/C4 are enforced by a frozen suite of traps a profile must refuse + an import guard — not reviewer vigilance. Standalone ADR: [`D007.md`](D007.md). | The durable asset is the trap suite, not the interface; it is the only thing that keeps A/B/C honest as the code grows (G2, G4). | A `conformance/` corpus + `tests/test_architecture_boundary.py` ship with the spec; correctness is defined by attacks withstood. | — |
| D008 | rejected | **Confidence as a single scalar tag.** A per-profile `confidence="high\|medium\|low"` field. | Refuted independently by three branches: confidence is a property of each query at each crank angle, not of the profile. | Superseded by D006 (per-region provenance). | — |
| D009 | accepted | **C4 is code-stability, not verdict-stability.** "Swap source without changing code" must never be sold as "swap without changing the answer." | PTV-contact and spring-float are cliff functions; a plausible measured curve can flip a verdict while code stays byte-identical. | Docs and reports must state this; resolved by D013 (bracketed verdict-agreement). | — |
| D010 | proposed | **Blends must prove derivative continuity.** Any `CompositeProfile` joining measured + inferred regions must prove C¹/C² continuity at the seam. | A naive blend injects phantom acceleration/jerk at the join → fake spring-float findings. | A conformance trap: identical halves with a seam must not produce a `jerk_at` spike. | — |
| D011 | deferred | **Ensemble / reactive-evidence-graph profile (Cluster E).** One profile exposing an ensemble of feasible curves; an invalidation graph rederiving results from evidence nodes. | The right *infinite-budget* shape, but premature for Milestone 1 — overbuild before measured data exists. | Revisit once measured data and multiple sources are real. | Measured data + ≥2 live sources exist. |
| D012 | accepted | **Ergonomics-as-integrity → `ProvFloat`.** Every query returns a `float` *subclass* carrying one `Provenance` stamp; it **is** the magnitude (no `.magnitude` to strip), arithmetic propagates the lattice-`min` stamp, `repr/str/format` always print the tag, and the sole exit is `float(x)`. | Round-2 question 1: the honest value must not cost more than the lie, or the guarantee is bypassed (refines D004). | `provfloat.py` (~40 lines) + a conformance test; **mandatory follow-on D017 (`ProvArray`)** — `np.asarray` silently drops the subclass. | Vectorized math escapes the scalar stamp without D017. |
| D013 | accepted | **Honesty-under-discontinuity → bracketed verdict-agreement.** For cliff analyses (PTV, spring float) build the earliest- and latest-plausible curves from the card's tolerances, run the identical analysis on both, and publish only whether the *verdict* agrees; a flip emits `UNDECIDABLE FROM CAM CARD`, never a number. | Round-2 question 2: honors D009 ("swap ≠ verdict-stable") by construction; strongest cross-family signal in the run. | A 2-element verdict-comparison loop over D012+D014; the tolerance envelope itself needs provenance or it manufactures false agreement. | — |
| D014 | accepted | **Derivative-capability matrix + Nyquist gate.** Each operator publishes crank-interval → max justified derivative order (computed from sample spacing, not declared); `velocity/acceleration/jerk_at` returns a stamped value on pass, a structured `Refusal{requested_order, max_supported, reason, remedy}` on fail. | Closes Pillar B's named failure mode — a smooth half-sine emitting authoritative jerk fiction; it is the gate PTV/spring sit behind. | Explicit `.approximate_anyway()` downgrades provenance to `INFERRED` rather than hiding the strip; every `Refusal` says what data would unlock the query. | Over-restriction drives bypass. |
| D015 | accepted | **Separate the threshold owner from the curve owner.** ★ A named *threshold policy* owns *where safe becomes unsafe*, distinct from the operator that owns *what the lift is*. | The cliff is a decision with an owner, not a property of the curve; makes D013's `UNDECIDABLE` accountable — you learn *whose* threshold flipped. | Structural separation, not new machinery; gives the report a place to attribute every cliff verdict. | — |
| D016 | accepted | **`Answer \| Refusal` at every safety-facing call.** Clearance/spring modules may not call bare `lift_at()`; they request an answer that may formally refuse. | Round-2 runner-up (B4.1): the connective tissue wiring D012/D013/D014 into analysis with no bare-float side door. | A `Refusal` is a first-class return, not an exception to swallow. | — |
| D017 | proposed | **`ProvArray` — provenance through NumPy.** A stamped array (`__array_ufunc__`/`__array_wrap__` + a parallel stamp array) so the `ProvFloat` guarantee survives vectorization. | `np.asarray` silently drops a `float` subclass — the `.magnitude` leak relocated to where the safety-critical derivative math runs. | Mandatory follow-on to D012; without it D012 guards only the place provenance doesn't matter. | — |
| D018 | deferred | **Value-of-information work orders.** When a verdict bracket straddles the cliff, the profile emits the single cheapest measurement that would collapse it (e.g. "measure nose lift at 110° to ±0.002″"). | Turns every `Refusal`/`UNDECIDABLE` from a dead end into active experiment design; bracket width + capability matrix + threshold policy already hold the inputs. | A future divergence branch; out of scope for M1. | Measured-data ingest exists. |

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
