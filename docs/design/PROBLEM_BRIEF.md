# Problem Brief — Cam Profile Architecture

> author: problem-framer-author-001
> Workflow: `cam_profile_architecture` · Milestone-1 framing
> This is a **framing** document. It states the question, constraints, goals,
> non-goals, and decision criteria for the divergence branches. It deliberately
> proposes **no** solution — the branches own that space.

---

## The open-ended question

**Where exactly should the boundary between *data sources* and *analysis* sit,
and what must the `CamProfile` abstraction guarantee, so that the same analysis
code runs unchanged whether a profile came from a sparse cam card or a measured
lift curve — and never silently treats an *inferred* curve as if it were
*measured*?**

Supporting questions the branches may explore (each is deliberately under-answered):

1. What is the **minimal, durable contract** a `CamProfile` must satisfy so it
   survives the arrival of data sources nobody has imagined yet?
2. A cam card **under-determines** the lift curve — it is an inverse problem with
   many curves fitting the same sparse constraints. How should the architecture
   **represent and propagate that uncertainty** so downstream analyses stay honest?
3. Different analyses need different fidelity (event timing tolerates a crude
   curve; jerk does not). How can a consumer ask *"is this profile good enough for
   **my** question?"* without coupling to where the profile came from?
4. What does it concretely mean for a **cam-card assumption to "leak"** into
   analysis code — and how would a test even detect the leak?
5. How do you **replace an approximate profile with measured data later** with zero
   change to analysis code, and *prove* that property rather than hope for it?

---

## Context (just enough to ground the ideation)

The product analyzes automotive/motorcycle camshafts. The reference part is the
Web Cam 81-651 for a Yamaha WR250R (DOHC, 4 valves). A **cam card** publishes only
sparse specs (peak lift, advertised duration, duration at 0.050", lobe centers,
lash, open/close events). Every analysis the product wants — timing, overlap,
dynamic compression ratio, piston-to-valve clearance, valve-spring safety,
acceleration/jerk, install sensitivity, reporting — actually needs a **continuous
valve-lift function over crank angle**, plus its derivatives.

Three facts make this hard and keep the design space open:

- **Reconstruction is an inverse problem.** Going from a handful of cam-card numbers
  to a full lift curve is under-determined; the curve you draw is an *approximation
  with real, quantifiable uncertainty*, not a fact.
- **Derivatives amplify whatever you assumed.** Velocity/acceleration/jerk come from
  differentiating the curve; a smooth-looking synthetic profile can produce
  authoritative-looking jerk numbers that are essentially fiction.
- **The domain has sharp edges.** Crank angle is periodic over the 720° cycle; lash
  separates cam-side from valve-side lift and separates seat timing from 0.050"
  timing; units mix inches and millimetres. Ambiguity here is itself a leak.

The data sources will grow over time: cam card → measured dial-indicator/degree-wheel
lift → Cam Doctor exports → scanned lobe coordinates → full valvetrain-dynamics models.
The abstraction has to outlive all of them.

---

## Hard constraints (invariants any design must hold)

- **C1 — One-way dependency.** Every analysis module depends *only* on `CamProfile`.
  No analysis may import or reference `CamCard`, a PDF/CSV/OCR parser, or any
  source-specific type.
- **C2 — Milestone discipline.** Milestone 1 is `cam card → CamProfile`. It is *not*
  `cam card → DCR`. The first durable output is a profile, not an analysis result.
- **C3 — Measured ≠ inferred.** At every point a consumer can observe a value, it must
  be possible to tell whether that value was measured or inferred.
- **C4 — Hot-swappable source.** Replacing an approximate profile with a measured one
  must require *no* change to downstream analysis code.
- **C5 — Stable consumer vocabulary.** The continuous query surface
  (`lift_at`, `velocity_at`, `acceleration_at`, `jerk_at`, `events_at_lift`,
  `duration_at_lift`, `max_lift`, `area_under_curve`) is the language analyses speak.
  *How* it is backed is open; *that* analyses speak only this language is fixed.
- **C6 — Unambiguous frames & units.** Crank vs cam degrees, valve-side vs cam-side
  lift, seat vs 0.050" timing, lash applied or not, inches vs millimetres — all must be
  explicit and non-guessable at the boundary.

---

## Goals (what a strong design maximizes)

- **G1 — Durability.** The contract survives unforeseen data sources without churn.
- **G2 — Leak-resistance.** It is *structurally* hard for a source assumption to reach
  analysis code, not merely discouraged by convention.
- **G3 — Honesty.** Confidence / provenance / quality metadata travels *with* the
  profile, so results can declare how much to trust them.
- **G4 — Provable replaceability.** Source-agnosticism is something a test suite can
  demonstrate, not just an aspiration.
- **G5 — Fitness signalling.** A consumer can determine whether a given profile is
  adequate for the specific question it is about to ask.

---

## Non-goals (explicitly out of scope for this ideation)

- Implementing the numerical analyses themselves (DCR, PTV geometry, spring dynamics).
- Choosing one curve-reconstruction / fitting algorithm as *the* answer.
- PDF parsing, OCR, or CSV-format details.
- UI, report styling, persistence, or database choices.
- Picking a language or framework as the point. Python is the reference; the question
  is architectural, not syntactic.

---

## Decision criteria (how convergence will judge the ideas)

Scored on **novelty / viability / fit**, read in this domain as:

- **Novelty** — Does it reframe the *boundary* or the *uncertainty* problem in a
  non-obvious way, rather than restating "make an interface"?
- **Viability** — Could a builder actually ship Milestone 1 with it, and would it still
  stand when measured data arrives?
- **Fit** — Does it genuinely enforce C1 (one-way dependency) and C3 (measured ≠
  inferred), or only appear to?

Tie-breakers when ideas are close:

- **Leak-detectability** — can a test catch a violation of C1, or does it rely on
  reviewer vigilance?
- **Cost of a new source** — how much must change to add Cam Doctor or lobe coordinates?
- **Blast radius** — when an inferred assumption turns out wrong, how far does the damage
  spread into already-computed results?

---

## Deliberately left open (room for the branches)

- Whether confidence is a single scalar, per-method, per-crank-region, or something richer.
- Whether `CamProfile` is one interface, a layered contract, or a family of capabilities.
- Whether the inverse-problem uncertainty is hidden, surfaced on demand, or made
  first-class in the type itself.
- Whether an analysis may **refuse** a profile that is too weak for its question.
- What the *letter-satisfying, spirit-violating* failure of the core invariant looks like
  (the adversarial-boundary branch will want this).

---

## Reference vocabulary (from the source spec — context, not a mandated design)

Shared nouns the branches can reuse without re-deriving. Listing them is *not* a
commitment to any particular structure.

- **Domain entities:** `CamCard` (sparse published specs), `CamProfile` (continuous
  lift over crank angle), `Valvetrain`, `EngineGeometry`, `ValveGeometry`, `SpringPackage`.
- **Candidate profile-backing implementations named in the source:**
  `CamCardApproxProfile`, `MeasuredValveLiftProfile`, `CamDoctorProfile`,
  `LobeCoordinateProfile`, `PolynomialProfile`, `SplineProfile`, `CompositeProfile`.
- **Consumers that must stay source-blind:** timing, overlap, dynamic compression ratio,
  piston-to-valve clearance, valve-spring safety, acceleration/jerk, cam advance/retard
  sensitivity, report generation.
- **Reference cam-card numbers (WR250R / Web Cam 81-651):** lift 0.360" (9.14 mm); lash
  0.006" intake / 0.008" exhaust cold; advertised duration 262°/270°; duration @0.050"
  238°/246°; lobe centers 109.5° intake / 104.5° exhaust (107° LSA); IO 9.5° BTDC,
  IC 48.5° ABDC, EO 47.5° BBDC, EC 18.5° ATDC.
