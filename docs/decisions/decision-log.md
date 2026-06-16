# Decision Log

Status: draft
Date: 2026-06-16

This log records the product and architecture decisions for `cam-analyzer`.
Decisions originate either from the original request
([`prompt.md`](../../prompt.md), [`Camshaft_Analysis_Spec.md`](../../Camshaft_Analysis_Spec.md))
or from the divergent-ideation design round
([`design/ROUND1_SYNTHESIS.md`](../design/ROUND1_SYNTHESIS.md)). They sharpen as
the shared understanding does.

Status values:

```text
proposed     under design; not yet a commitment
accepted     a commitment the code and reviews must honor
deferred     a good idea, deliberately not now
rejected     considered and ruled out (kept as provenance)
superseded   replaced by a later accepted decision (named in Consequences)
```

Decisions sourced from `prompt.md` / the spec are **accepted** (they are the
original request). Decisions distilled by the round-1 synthesis are **proposed**:
round 1 explicitly produced a *seed*, not a frozen design, and round 2 is still
ideating on the two open questions (D012/D013). Rejected rows below are the
round-1 *traps* — recorded so they are not re-proposed.

## Decisions

| ID | Status | Decision | Reason | Consequences | Revisit Trigger |
|---|---|---|---|---|---|
| D001 | accepted | **One-way dependency (C1).** Every analysis module imports only `CamProfile`; never a `CamCard`, parser, source format, or source type. | The original request's "most important requirement"; the whole durability claim rests on it. | Package layout is `sources → profile ← analysis`; enforced by a test, not review (see [D007](#d007--standalone)). | A consumer genuinely needs a source fact a profile cannot express. |
| D002 | accepted | **Measured ≠ inferred (C3), carried with the value.** Provenance travels *in* the returned value, not as a profile-level sidecar tag. | The request demands every value be distinguishable as measured/inferred; a sidecar tag cannot describe a per-region curve. | Queries return `Quantity` carrying provenance; see D004/D006. | — |
| D003 | accepted | **Milestone 1 is `cam card → CamProfile` (C2).** The first durable output is a profile, not an analysis result. | The request fixes this explicitly; it keeps the boundary, not a DCR number, as the deliverable. | M1 ships `CamCardApproxProfile` + one `HalfSineCamCardOperator`; DCR/PTV/spring are downstream. | — |
| D004 | proposed | **Typed boundary (Pillar A).** No bare `float` crosses the boundary; every value is a `Quantity{magnitude, unit, frame, provenance}`, `provenance` a computed monotone lattice (`MEASURED>INFERRED>EXTRAPOLATED`) with **no setter**. Angles are phantom-typed `Angle[Crank\|Cam]`. | Makes mislabeling (inferred→measured), unit, and frame errors *unconstructable* rather than discouraged (G2, C3, C6). | A `quantity.py` value layer; `mypy --strict`; the ergonomics tax becomes the central open risk (D012). | Round-2 resolution of ergonomics-as-integrity. |
| D005 | proposed | **Single canonical representation (Pillar B).** `CamProfile` is a `@final` facade over one immutable `CanonicalLiftModel` + a *named* operator; the eight queries are *generated* projections (derivatives differentiate one operator). | Implementers supply only the canonical object, so inconsistent derivatives and sparse-as-continuous are unconstructable. | No subclass method hooks; measured data swaps the operator with zero downstream change (C4). | A source cannot be expressed as samples + one operator. |
| D006 | proposed | **Per-region fitness + first-class ignorance (Pillar C).** Provenance is per query / per crank region / per derivative order via a `ProvenanceMap`; derivative provenance auto-downgrades past Nyquist support; consumers ask `is_good_enough_for(AnalysisKind)`. | A cam-card profile is near-certain at its anchors and fabricated between; a single tag is a lie (D008). | Safety consumers must pattern-match the unsupported case; fabricated seat-ramp values cannot be laundered into "safe". | — |
| D007 | proposed | **Conformance by adversary corpus (Pillar D).** ★ C1/C3/C4 are enforced by a frozen suite of traps a profile must refuse + an import guard — not reviewer vigilance. Standalone ADR: [`D007.md`](D007.md). | The durable asset is the trap suite, not the interface; it is the only thing that keeps A/B/C honest as the code grows (G2, G4). | A `conformance/` corpus + `tests/test_architecture_boundary.py` ship with the spec; correctness is defined by attacks withstood. | — |
| D008 | rejected | **Confidence as a single scalar tag.** A per-profile `confidence="high\|medium\|low"` field. | Refuted independently by three branches: confidence is a property of each query at each crank angle, not of the profile. | Superseded by D006 (per-region provenance). | — |
| D009 | accepted | **C4 is code-stability, not verdict-stability.** "Swap source without changing code" must never be sold as "swap without changing the answer." | PTV-contact and spring-float are cliff functions; a plausible measured curve can flip a verdict while code stays byte-identical. | Docs and reports must state this; round 2 owns what the boundary *says* about discontinuity (D013). | — |
| D010 | proposed | **Blends must prove derivative continuity.** Any `CompositeProfile` joining measured + inferred regions must prove C¹/C² continuity at the seam. | A naive blend injects phantom acceleration/jerk at the join → fake spring-float findings. | A conformance trap: identical halves with a seam must not produce a `jerk_at` spike. | — |
| D011 | deferred | **Ensemble / reactive-evidence-graph profile (Cluster E).** One profile exposing an ensemble of feasible curves; an invalidation graph rederiving results from evidence nodes. | The right *infinite-budget* shape, but premature for Milestone 1 — overbuild before measured data exists. | Revisit once measured data and multiple sources are real. | Measured data + ≥2 live sources exist. |
| D012 | proposed | **Open: ergonomics-as-integrity.** Make the provenance-carrying path *strictly more convenient* than bare floats, so the guarantee is un-strippable in practice. | All three frontier models named the `.magnitude` "laundry utility" escape hatch as the #1 risk. | A round-2 divergence question; until resolved, `.magnitude` must be ugly, grep-able, lint-flagged. | Round-2 synthesis. |
| D013 | proposed | **Open: honesty under discontinuity.** What `CamProfile` owes a consumer when the verdict is a cliff function of the profile. | C4 silently changing answers is the second-biggest round-1 risk (D009). | A round-2 divergence question; candidate: a `DualProfile` that quantifies source-sensitivity. | Round-2 synthesis. |

## D007 — standalone

See [`D007.md`](D007.md) for the full record of the ★ non-obvious-but-viable
decision (conformance by adversary corpus), which the round-1 synthesis named as
the choice that keeps the other three pillars honest.
