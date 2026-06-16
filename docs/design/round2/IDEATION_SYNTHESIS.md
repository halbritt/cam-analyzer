---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: final-synthesizer-reviewer-2-001

# Round 2 Ideation Synthesis — Cam Profile Architecture

> **Operator-facing result.** Assembles the three deepened picks
> (`deepened/deepen_{1,2,3}/DEEPENED.md`) and the convergence ledger
> (`CONVERGENCE.md`) into a shortlist, one starred non-obvious pick, the trap list,
> and one wildcard. Round 1 already settled the skeleton — a typed,
> provenance-carrying `CamProfile` = Pillars **A** (typed value) · **B** (one canonical
> operator) · **C** (per-region fitness). Round 2 diverged on the two unresolved,
> high-stakes questions it left open — **ergonomics-as-integrity** and
> **honesty-under-discontinuity** — plus the inverted-query provocation. This document
> chooses what to build first.

## The spine (one sentence)

**A value — or a verdict — may leave the `CamProfile` boundary only if its fitness is
proven; the instant it can't be, the boundary says so loudly.** The three picks enforce
that one rule in three places: across **math** (the value type), across **queries** (the
derivative gate), and across **verdicts** (the bracket). They are not competitors; they
are one architecture, and they have an order.

**Build order:** ① `ProvFloat` (the conformance anchor everything stamps onto) → ②
derivative-capability gate (decides which queries may answer at all) → ③ bracketed
verdict-agreement (consumes ① and ② and turns the cliff into the product). The ★ pick
below is the small structural separation that makes ③ *accountable*.

---

## Shortlist — build these three (each maps to one round-2 question)

### 1. `ProvFloat` — the honest value *is* the convenient value  ·  `deepen_3` · B3.3 ⊕ B2.2 · Wt 8.25 · 3-family (α)
Every query returns a `float` **subclass** carrying one `Provenance` stamp
(`MEASURED > INFERRED > EXTRAPOLATED`). It *is* the magnitude, so there is no `.magnitude`
field to strip; arithmetic dunders propagate the lattice-**min** stamp (B2.2 hybrid), so a
clearance computed from one `EXTRAPOLATED` nose value is itself `EXTRAPOLATED` for free;
only `__repr__`/`__str__`/`__format__` are overridden, and they *always* print the tag, so
a laundered low-confidence number announces itself the moment it reaches a log, plot,
report cell, or debugger. The sole sanctioned exit is `float(x)` — ugly, grep-able,
lint-flagged.
- **Why it's on the list:** it is the *direct* answer to round-2 question 1
  (ergonomics-as-integrity) — the lie can never be cheaper than the truth — and it is the
  cheapest foundation (`provfloat.py` ≈ 40 lines + one conformance test, buildable in the
  "one hour, no team" budget). Everything else stamps onto it.
- **Watch (load-bearing risk):** the scalar guarantee evaporates the instant values enter
  a `np.ndarray` (`np.asarray` silently drops the subclass — the `.magnitude` laundering
  relocated to vectorization, exactly where the safety-critical derivative math lives).
  **Mandatory follow-on:** `ProvArray` (`__array_ufunc__`/`__array_wrap__` with a parallel
  stamp array) — without it this protects the one place provenance doesn't matter.

### 2. Derivative-capability matrix — refuse derivatives the data can't support  ·  `deepen_2` · B4.2 · Wt 8.30 · 2-family (ε)
Each operator publishes a matrix mapping crank-angle intervals → max justified derivative
order. Before `velocity_at`/`acceleration_at`/`jerk_at` answers, the facade checks the
matrix; pass → a stamped `ProvFloat`, fail → a structured `Refusal{requested_order,
max_supported, reason, remedy}`. A sparse half-sine cam-card backing therefore *cannot*
emit authoritative-looking jerk fiction.
- **Why it's on the list:** it kills Pillar B's named failure mode ("a smooth half-sine
  emits authoritative jerk") and is the safety gate PTV/spring modules sit behind. Fold in
  Gemini's B5.5 **Nyquist** test (sample-spacing → max order) so the cap is *computed* from
  the data, not just declared; drop B5.5's bus-protocol ceremony.
- **Watch:** over-restriction → bypass. Keep the escape explicit and grep-able
  (`.approximate_anyway()` downgrades provenance to `INFERRED` rather than hiding the
  strip), and make every `Refusal` say exactly what data would unlock the query.

### 3. ⚠️ Bracketed verdict-agreement — never emit one curve  ·  `deepen_1` · B3.5 · Wt 8.90 · 3-family (γ)
For any cliff-function analysis (PTV contact, spring float), build the **earliest-** and
**latest-plausible** curves from the cam card's own tolerances (seat-timing, lash, install
offset), run the identical analysis on both, and publish only whether the **verdict**
agrees. A flip emits `UNDECIDABLE FROM CAM CARD`, never a number.
- **Why it's on the list:** it is the *direct* answer to round-2 question 2
  (honesty-under-discontinuity) and the highest-scoring, strongest cross-family signal in
  the run. It honors the round-1 "swap ≠ verdict-stable" trap *by construction* — a
  2-element loop comparing verdicts, zero new provenance machinery, sitting on picks 1+2.
- **Watch:** the bracket is only as honest as its construction — if the tolerance envelope
  is too narrow it manufactures false agreement. The envelope itself needs provenance.

> A pragmatic fourth surface, **B4.1** (`Answer | Refusal` at every safety-facing call;
> ban `lift_at()` inside clearance/spring modules), is the connective tissue that
> *operationalizes* all three — it is the runner-up by score (7.95) and the recommended way
> to wire picks 1–3 into the analysis modules without a bare-float side door.

---

## ★ Non-obvious-but-viable pick — separate the **threshold owner** from the **curve owner**  ·  B1.4 (δ, Wt 7.90, Codex-only)

**The cliff is not in the curve — it's in the policy.** Today everyone instruments the
*value's* provenance; B1.4 points out that the line between "safe" and "unsafe" is itself a
**decision with an owner**, distinct from whoever owns the lift curve. Split them: the
curve-region operator owns *what the lift is*; a named **threshold policy** owns *where
safe becomes unsafe* and converts a continuous value into a verdict.

- **Why it's the star (non-obvious):** it didn't top the score and is the only survivor of
  an otherwise single-family (Codex) cluster, so it nearly got lost — yet it is what makes
  pick 3's `UNDECIDABLE` *accountable*. When a verdict flips, you learn **whose threshold**
  flipped it, not merely that the curve moved. It reframes "honesty under discontinuity"
  from a property of the data to a *named, auditable decision* — the genuinely non-obvious
  move this round.
- **Why it's viable:** it is structural separation, not new machinery — cheap, it sharpens
  pick 3's semantics, and it gives the report a place to attribute every cliff verdict.
  Mirrors round 1's star (the durable asset that *keeps the other picks honest*).

---

## Trap list — do **not** re-propose (each with its one-line reason)

**Surfaced this round (reject):**
- 🔴 **B5.2 cache-coherency invalidation protocol** — profiles are immutable and recompute
  is cheap; a dependency-tracking coherency controller is pure infra tax for a problem that
  barely exists in M1.
- 🔴 **B3.1 lossy precision-as-stamp** — encoding provenance by throwing away digits
  corrupts the real number, collides with genuinely round measured values, and breaks
  reproducibility, to carry a flag a single byte could carry.
- 🔴 **B3.2 NaN-poison companion** — `nan` launders trivially (`nan_to_num`, `if x:`, `max`)
  and, fatally, **discards the reason** for refusal — turning an honest "I don't know" into a
  mysterious blank.
- 🔴 **B5.6 entropy token-bucket** — needs a calibrated uncertainty model M1 doesn't have,
  and its bucket size re-smuggles the single global budget round 1 already killed.
- 🟡 **B5.3 MPU privilege segmentation** — the privilege-register ceremony mostly duplicates
  what Pillar-C provenance + refusal-gating already give you; fold the intent into the gate,
  don't build an MPU.
- 🟡 **B3.4 append-only audit log** — returning naked floats and reconstructing truth
  out-of-band *concedes* the laundering and depends on a log no analysis code reads;
  contradicts ergonomics-as-integrity.
- 🟡 **B2.1 AST import-graph audit *at boot*** — parsing the whole tree on every startup is a
  runtime tax and fragile; the intent (analysis→parser imports) is excellent as a **CI
  import-linter test**, not a boot audit.

**Carried from round 1 as hard constraints (still binding):**
- 🔴 **Single-scalar confidence tag is dead** — confidence is per-query / per-region /
  per-derivative-order, or it is a lie (refuted by 3 round-1 branches).
- 🔴 **The `.magnitude` / "laundry-utility" escape hatch** — *the* central problem; any
  honest path more verbose than dropping to bare floats gets bypassed. Note its round-2
  mutation: `np.asarray` is the same leak relocated to vectorization (see pick 1's risk).
- 🔴 **"Swap source without code change" ≠ verdict-stable** — PTV and spring-float are cliff
  functions; never sell source-replaceability as outcome-stability (this is exactly what
  pick 3 exposes instead of hiding).
- 🔴 **Naive `CompositeProfile` blending** — stitching curves injects phantom
  acceleration/jerk at the seam → fake spring-float findings; any blend must prove
  derivative continuity at joins.
- 🟡 **Ensemble-of-curves / reactive-invalidation graph (Cluster E)** — the right
  infinite-budget shape but premature for M1; revisit once measured data exists.

---

## Wildcard provocation (one — opens a new direction)

> **What if the profile doesn't just *refuse* — it tells you the single cheapest
> measurement that would let it stop refusing?**

Every `UNDECIDABLE FROM CAM CARD` (pick 3) and every `Refusal` (pick 2) is a *dead end*
today. Invert it into **value-of-information**: when the verdict bracket straddles the
cliff, have the profile compute *which one physical measurement would most collapse the
bracket* and emit it as a ranked work order —
`"measure nose lift at 110° crank to ±0.002\" → PTV verdict becomes decidable."`

The provenance machinery already holds everything needed: the **bracket width** (pick 3) is
the uncertainty, the **capability matrix** (pick 2) knows which region/derivative-order is
starved, and the **threshold policy** (★ B1.4) knows how close to the cliff the verdict
sits. Combine them and `CamProfile` stops being a passive object waiting to be swapped for
measured data and becomes an **active experiment-designer**: it hands the operator a
to-do list of measurements ranked by verdict-impact, turning "we don't know" into "here is
the one number to go measure." A genuinely new direction — honesty that *acts* — worth a
full divergence branch in a future round.
