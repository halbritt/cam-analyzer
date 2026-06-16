# Round-1 Synthesis & Round-2 Seed — Cam Profile Architecture

> Produced by the `/adhd` deepen→synthesize pass over the 5 divergence branches of
> run `run_0d48ede6…` (which produced the diverge phase before wedging on striatum
> #302/#317/#290/#296). The **deepen** step drew genuine input from all three frontier
> models — **Claude Opus** (typed boundary), **Codex / GPT** (canonical representation),
> **Gemini** (per-region fitness). This document is the **input/seed** for the next
> striatum `divergent_ideation` run; it is not a committed design decision.

---

## 1. Brief (problem + reframe)

The brief asked *where the data-source ↔ analysis boundary sits and what `CamProfile`
must guarantee*. Round 1 converged hard enough that the **reframe for round 2** is no
longer "what should the abstraction be" but:

> **Given a typed, provenance-carrying `CamProfile` is the right shape — how do we make the
> *honest* path the *ergonomic* path, so the guarantees can't be quietly stripped, and how
> do we stay truthful where analysis verdicts are *discontinuous* in the profile?**

## 2. Wide set (clustered, scored `[N V F]`)

- **A — Type the boundary** (no bare floats; unit·frame·provenance in the value; confidence = computed monotone lattice, no setter): B1·I2, B3·S6, B4·I5, B1·I3 → `[8 8 10]` (3-branch convergence)
- **B — One canonical representation; query methods are *generated* projections** (derivatives differentiate one operator; reductions reduce it): B1·I1, B4·I4, B4·I2 → `[8 8 9]`
- **C — Per-region fitness + first-class `Unknown`/`Extrapolated`** (confidence is per-query/per-crank-region/per-derivative-order; safety consumers must pattern-match ignorance): B1·I4, B3·S3, B2·I6, B5 → `[7 7 10]`
- **D — Prove the boundary by *test*, not vigilance** (adversary corpus = conformance; CI perturbation/equivalence; import grep): B1·I5/I6, B4·I6, B3·S1 → `[8 7 8]`
- **E — Reactive / ensemble / live-evidence-graph** (rederive from evidence nodes; ensemble of feasible curves): B2·I2/I4/I5 → `[8 4 6]` *(maximalist; premature for M1 — see traps)*

## 3. Converge (shortlist + traps)

Clusters A, B, C are **not competitors** — they are three facets of one architecture and
should be adopted together:

- **A** = the *value type* a query returns.
- **B** = the *backing* (one sealed canonical operator) those values come from.
- **C** = the *per-crank provenance/fitness map* that stamps each returned value.

★ **Non-obvious-but-viable pick:** **D — conformance-by-adversary-corpus.** The durable
asset isn't the interface; it's the *frozen suite of traps a profile must refuse*. It turns
C1/C3/C4 from reviewer vigilance into a test, and it is the only cluster that keeps the
other three honest as the codebase grows.

**Traps (carry as hard constraints, do NOT re-propose in round 2):**
- 🔴 **Confidence-as-a-single-scalar-tag is dead** — refuted independently by 3 branches. Confidence is per-query/per-region/per-derivative-order or it is a lie.
- 🔴 **`.magnitude` / "laundry utility" escape hatch** — *all three frontier models named this as the #1 load-bearing risk, unprompted.* Any provenance scheme that is more verbose than dropping to bare floats will be bypassed. This is the central round-2 problem.
- 🔴 **"Swap source without code change" ≠ "swap without changing the verdict."** PTV-contact and spring-float are **cliff functions**: a plausible measured curve flips "safe"→"contact" discontinuously while analysis code stays byte-identical. C4 must not be sold as verdict-stability. (B3·S2)
- 🔴 **`CompositeProfile` naive blending injects phantom acceleration/jerk at the seam** → fake spring-float findings. Any blend must prove derivative continuity at joins. (B3·S5)
- 🟡 **Ensemble-of-curves / reactive invalidation graph (Cluster E)** is the right *infinite-budget* shape but **premature for Milestone 1** — over-build now, revisit once measured data exists.

## 4. Focus — the three deepened pillars (one per frontier model)

### Pillar A · Typed provenance boundary — *Claude Opus*
A frozen `Quantity(magnitude, unit, frame, provenance)`; `provenance` is an `IntEnum`
lattice `MEASURED > INFERRED > EXTRAPOLATED` so `min()` **is** the join. Angles are phantom
`Angle[Crank|Cam]`; arithmetic is defined only between matching `(unit, frame)` and the
result inherits the weakest input's stamp — relabeling inferred→measured is unconstructable.
- **Risk:** ergonomics tax → `.magnitude` laundering. Mitigation: the in-system path (convert/differentiate/integrate/compare) must be *more* convenient than dropping to floats; `.magnitude` should be ugly, grep-able, lint-flagged.
- **First step:** `quantity.py` (`Unit`, `Frame`, `Confidence: IntEnum`, frozen `Quantity`, phantom `Angle`) + express the C5 surface as a `Protocol` returning only `Quantity`/`Angle`, backed by a trivial `ConstantProfile`, proven by `mypy --strict`.
- **Unlocks:** provenance-carrying NumPy (kills the perf motive to escape); reason-chain breadcrumbs (`why is this EXTRAPOLATED?`); 2-axis lattice (provenance ⟂ numeric-quality); frame-only converters; a typed-thresholds library.

### Pillar B · Single canonical representation — *Codex / GPT*
`CamProfile` is a `@final` facade over one immutable `CanonicalLiftModel` = normalized
720° samples + a **named operator** (`HalfSineApproximation`, `CubicPeriodicSpline`,
`MeasuredPeriodicSeries`). Every query delegates to that one operator: derivatives via
`operator.derivative(order=n)`, reductions by sampling/solving it. Implementers supply only
the canonical object — no method bodies — so inconsistent derivatives / sparse-as-continuous
are unconstructable. M1 = one crude `HalfSineCamCardOperator`; measured data swaps the
operator with zero downstream change.
- **Risk:** the operator becomes *too authoritative* for weak input — a smooth half-sine emits authoritative-looking jerk that is fiction unless loudly marked low-confidence inferred. (Ties Pillar B to Pillar C.)
- **First step:** `CamProfile.from_canonical(model)` + exactly one `HalfSineCamCardOperator`, generating all 8 methods; no subclass hooks.
- **Unlocks:** `OperatorRegistry` (versioned, serializable for reports); `DualProfile` (run approx vs measured through the same surface to quantify source-sensitivity — directly addresses the cliff-function trap); `DerivativePolicy` (block/warn high-order derivatives on sparse backing).

### Pillar C · Per-region fitness + first-class ignorance — *Gemini*
Queries return `ProfileResult[T]` resolved against an interval `ProvenanceMap`
(`bisect`, O(log N)): e.g. `[0,15]:MEASURED`, `[15,345]:EXTRAPOLATED`. Derivative provenance
auto-downgrades when sampling density can't support differentiation (Nyquist). Safety
consumers must pattern-match the unsupported case, so a fabricated seat-ramp/nose value
can't be laundered into a "safe" verdict. A consumer asks `is_good_enough_for(AnalysisKind)`
without coupling to the source.
- **Risk:** same ergonomic friction → metadata-stripping laundry utilities.
- **First step:** `ProvenancedValue` (Generic) + `ProvenanceMap` (bisect interval lookup).
- **Unlocks:** `with profile.require(MEASURED):` guardrail context manager; Nyquist derivative-downgrading; per-analysis "required-confidence mask" fitness check; ignorance heatmaps in reports.

## 5. Provocation (wildcard for round 2)

> **What if the analysis modules don't *read* a profile at all — they *submit a question with a required fitness*, and the profile either answers with a provenance-stamped value or formally *refuses*?** Invert the call direction: `profile.answer(Query.PTV_min_clearance, require=MEASURED_NOSE)` returns `Answer | Refusal{reason, what_would_fix_it}`. This makes "good enough for my question?" the *only* way to get a number, makes refusal a first-class result, and may dissolve the `.magnitude` escape hatch by removing the bare-float exit entirely — at the cost of a heavier query surface. Worth a full divergence branch.

---

## Seed instructions for the next `divergent_ideation` run

Round 2 should **assume Pillars A+B+C as the settled skeleton** and diverge on the two
unresolved, high-stakes questions round 1 surfaced:

1. **Ergonomics-as-integrity:** how to make the provenance-carrying path strictly more
   convenient than bare floats, so the guarantee is un-strippable in practice (not just in
   the type system). *All three models flagged this as the failure mode.*
2. **Honesty under discontinuity:** how the boundary should behave when the analysis verdict
   is a cliff function of the profile (PTV contact, spring float) — what `CamProfile` owes a
   consumer when "swap without code change" silently changes the answer.

Plus the inverted-query provocation (§5) as at least one wild branch.
