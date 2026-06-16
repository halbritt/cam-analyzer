# Branch 1 — Divergence under frame `adversarial_boundary`

> author: diverger-author-001
> Workflow: `cam_profile_architecture` · branch: `branch_1_adversarial_boundary`
> Mode: **DIVERGENT** (generator, not critic). No evaluation, ranking, or hedging below.

**Transform applied (before ideating):** *Find the input that technically satisfies
every stated requirement while violating its spirit.*
**Vantage:** redesign so that letter-satisfying / spirit-violating input is **impossible** —
harden the *spec*, not just the code.

---

## Checkable intermediate (what the transform produced)

### Kernel / invariant the design must hold

The spec's true requirement is the **implication**

> **`well-typed CamProfile`  ⟹  `physically-coherent ∧ honestly-labeled lift function`**

Today that implication is **false**. Any class carrying the eight C5 query methods
(`lift_at … area_under_curve`) plus a `confidence` field *type-checks*, regardless of
whether its numbers describe a real cam. The whole attack surface is exactly the **gap
between *well-typed* and *physically true***. The adversary wins by shipping a
**well-typed-but-false** profile. "Hardening the spec" = moving the coherence/honesty
guarantees out of convention and *into the type system / spec*, so the spirit-violating
input is **unconstructable**, not merely discouraged.

### Restated problem

> Not *"expose a `CamProfile` interface + a confidence field"* (letter), but
> *"guarantee every object handed to analysis as a `CamProfile` **is** a physically
> coherent, periodic, unit-/frame-explicit lift function whose declared provenance is
> true — such that no input can pass the contract while feeding analysis numbers that
> are inconsistent, mislabeled, fabricated, or sparse-pretending-continuous."*

### Trap inputs the transform surfaced (each passes the letter, breaks the spirit)

- **T1 — Inconsistent derivatives.** `velocity_at`/`acceleration_at`/`jerk_at` are
  *independently implemented* and free to disagree with the integral of `lift_at`.
  (Violates the spirit of C5; great-looking jerk that is fiction — see brief §Context.)
- **T2 — Unit/frame/label spoof.** `lift_at` returns mm where the 0.050"/0.080" PTV
  thresholds assume inches; or an *inferred* value returns through the same bare-`float`
  channel as a *measured* one. (Defeats C3, C6.)
- **T3 — Meaningless confidence.** The `confidence`/quality field *exists* (letter) but is
  hardcoded `"high"` (spirit). G3 satisfied on paper, betrayed in fact.
- **T4 — Fabricated unsupported region.** A cam-card profile *invents* the seat-ramp /
  low-lift region — the part that actually drives DCR and PTV — with a default polynomial,
  then hands back confident bare numbers as if measured.
- **T5 — Sparse-as-continuous.** `lift_at` is really a lookup at the 8 published cam-card
  points with junk between, masquerading as a continuous function over 720°.
- **T6 — Leakage-through-numbers.** "No analysis module imports `CamCard`" holds (C1
  letter), yet cam-card *assumptions* (symmetric flanks, defined only at integer degrees,
  never returns to seat) reach analysis baked into the *values* (C1 spirit broken).

### Banned obvious answers — **NOT** used below

1. Add a cam-card "consistency validator." 2. Write more unit / property tests.
3. Add a confidence field and *tell* implementers to fill it honestly.
(The spec already half-does #3, and the adversary walks straight through all three.)

---

## Six ideas (divergent)

### Idea 1 — Sealed canonical-representation profile; query methods are *generated* projections
A `CamProfile` is not "any class with the 8 methods." It is a **sealed** type backed by
exactly **one** canonical object: declared lift samples + a *named* interpolation operator
over the periodic 720° domain. `velocity/acceleration/jerk` are *generated* by
differentiating that single operator; `max_lift/area_under_curve/events_at_lift/
duration_at_lift` are *generated* by reducing it. Implementers supply the canonical object —
**never** a derivative or a method body. There is simply no socket in which to place an
inconsistent or domain-incomplete value. *(Makes T1 and T5 unconstructable at the type level.)*

### Idea 2 — No bare `float` at the boundary: every value is a `Quantity{unit, frame, provenance}`
`lift_at` returns `Quantity[Lift]` tagged `inch|mm` × `valve-side|cam-side` ×
`measured|inferred|extrapolated`; the argument is `Angle[crank|cam]`. Thresholds
(PTV 0.050"/0.080") are written *against* `Quantity`, and every analysis result is
auto-stamped with the **weakest provenance among its inputs** — a computed lattice *join*
with **no setter**. Relabeling inferred-as-measured is impossible (the label is derived and
propagates); a mm/inch or crank/cam swap is a *type* error. *(Closes T2; enforces C3 + C6 structurally.)*

### Idea 3 — Confidence is a monotone-only lattice value, never an assertable field
`confidence`/quality has **no setter**. It is *computed* from evidence, and every operation
that touches a profile — interpolate, extrapolate, smooth, resample, advance/retard — can
only **lower** it. "High confidence" becomes *unforgeable*: it must be *earned* by measured
support, not *declared*. An adversary can pin every other knob but cannot synthesize trust.
*(Closes T3; gives G3 teeth.)*

### Idea 4 — Mandatory evidence/support map; `Unknown`/`Extrapolated` is a first-class, non-skippable return
Every profile must expose **which crank regions are measured vs interpolated vs
extrapolated**, and a query inside an unsupported region must return a boxed
`Extrapolated{value, basis}` (or `Unknown`) — **never** a bare number. Safety consumers'
*signatures* (PTV, DCR) are obligated to pattern-match the unsupported case, so they
physically cannot launder a fabricated seat-ramp value into a confident result; the
fabrication is loud at the call site. *(Closes T4; serves G5 + bounds blast radius.)*

### Idea 5 — Ship an **adversary corpus** *with the spec*; conformance = "attacks survived"
The repo freezes a **museum of traps** as a first-class spec artifact: a
non-monotone-then-returns lift, a never-closes lift, an `mm`-labeled-as-`inch` profile, a
card with `advertised_duration < duration@0.050"`, a sparse-lookup profile. A `CamProfile`
implementation or a `CamCard` ingest is **not conformant** until the suite proves it
*rejects or cannot construct* every trap. Correctness is *defined by the attacks the
boundary withstands*, not by the happy path — the spec grows by adversary, not by feature.
*(Hardens the spec itself; makes "well-typed ⟹ valid" a tested property — G2, G4.)*

### Idea 6 — Boundary **perturbation contract**: CI fuzzes profiles with physically-valid, source-agnostic mutations
Before any analysis output is trusted, the harness feeds each consumer the same profile
under source-agnostic transforms — resample at *irrational* crank angles, add an asymmetric
*measured* flank, shift seat timing within lash, swap the backing impl for a behaviorally
equivalent one — and asserts every output stays **defined** and changes **continuously**.
A module that breaks reveals it secretly depended on cam-card *shape* (symmetric flanks,
integer-degree grid): a **C1 leak through the numbers** with no offending `import` anywhere.
*(Closes T6; makes C1 leak-detectable by a *test*, not reviewer vigilance — the named tie-breaker.)*

---

### Distinct mechanisms (so the critic can see six, not one)
1 eliminates the degrees of freedom · 2 types the values · 3 makes confidence un-spoofable ·
4 makes ignorance representable · 5 defines correctness by an attack corpus ·
6 polices leakage by behavioral perturbation.
Each targets a different trap (T1/T5, T2, T3, T4, all-of-them-as-oracles, T6) and a
different brief constraint (C5, C3/C6, G3, G5, G2/G4, C1).
