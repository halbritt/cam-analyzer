# cam-analyzer: Domain-Driven Design Foundations

A first-time reader can come to the wrong conclusion about why this design works.
The surface looks like "a calculator with an interface and some implementations" —
everyone has seen ten of those. They look at `CamProfile`, see a familiar
`Protocol` with eight methods, and ask: *"what's load-bearing?"*

If they conclude there isn't any, they will work *around* the boundary instead of
*with* it: explicitly cast a stamped value to a bare `float` and pass it on;
reach into a `CamCard` from an analysis module "just this once"; hardcode a
`confidence = "high"` field; let `velocity_at` be implemented independently from
`lift_at`. Each one type-checks. The toolkit survives that for a while, and then a
spring-float warning fires on an interpolation artifact, or a PTV "safe" verdict
rests on a fabricated seat ramp, and the user concludes the numbers can't be
trusted.

The actual answer is that cam-analyzer is a **domain-driven design** of the
data-source ↔ analysis boundary. The vocabulary in
[`UBIQUITOUS_LANGUAGE.md`](../reference/ubiquitous-language.md) is the *model*.
The `CamProfile` query surface is the model's interface boundary. The sealed
`Quantity[Unit]` value type (`ProvFloat` is now a back-compat alias for it) and
the provenance lattice are the model's grammar. The invariants
C1–C6 in the [problem brief](../design/PROBLEM_BRIEF.md) and the boundary
decisions in [`decision-log.md`](../decisions/decision-log.md) are the *bounded
context*.

This document writes the framing down so a new reader can see what's load-bearing
and what isn't, and so future design rounds cite their domain-modeling rationale
rather than re-deriving it each time.

## Bounded context

What cam-analyzer models:

- The **continuous valve-lift function** over the periodic 720° crank cycle and
  its derivatives — the thing every analysis actually needs.
- The **provenance** of every value a profile returns: measured, inferred, or
  extrapolated, *per crank region and per derivative order*.
- The **fitness** of a profile for a specific question (`is_good_enough_for`).
- The **boundary** between a source (cam card, measured data, …) and the analyses
  that must never depend on it.

What cam-analyzer deliberately does **not** model:

- **The curve-reconstruction algorithm as *the* answer.** Many operators can back
  a profile; the boundary is agnostic to which (Pillar B). Choosing one fitting
  method is a source-layer concern, not an architectural commitment.
- **PDF parsing / OCR / CSV format details.** Those live entirely in `sources` and
  are invisible past the boundary.
- **UI, report styling, persistence, database choice.** Downstream of the model.
- **Verdict stability across a source swap.** C4 guarantees *code* does not change
  when the source changes; it pointedly does **not** promise the *answer* will not
  change (PTV/spring are cliff functions). Conflating the two is a modeling error.

The boundary is visible in the package structure: a value crosses it only as a
`Quantity[Unit]`/`Angle` (the `ProvFloat` alias), and an analysis module can
import only `cam_analyzer.profile`.
If a feature wants to live outside that boundary (a source-specific shortcut, a
bare-float fast path), it does not get to call itself analysis.

## Ubiquitous language

[`UBIQUITOUS_LANGUAGE.md`](../reference/ubiquitous-language.md) is the canonical
glossary. Three things to internalize:

- **Every term is load-bearing.** `MEASURED`, `INFERRED`, and `EXTRAPOLATED` are
  not synonyms for "good / okay / bad" — they are lattice values the type system
  joins. `CamCard` and `CamProfile` are not interchangeable nouns; one is a sparse
  source record, the other is the continuous boundary.
- **New capabilities add to the vocabulary.** The right way to introduce a concept
  (a new source, a new analysis, a fitness policy) is a glossary entry first and a
  class/field second.
- **Code agrees with the vocabulary.** Class, method, and parameter names, error
  messages, and conformance-trap names all use the glossary's words. Drift is a
  bug, not a stylistic choice.

## Aggregate roots

Entities with identity and lifecycle. The runtime enforces the listed invariants
at construction; once built, an aggregate is not mutated in flight.

| Aggregate | Identity | Invariants the model enforces |
|---|---|---|
| `CamCard` | (engine, cam part no.) | sparse published specs only; lives in `sources`; never importable by `analysis`; `advertised_duration ≥ duration@0.050″` |
| `CamProfile` | the backing `CanonicalLiftModel` | `@final` facade; periodic over 720°; every query delegates to **one** named operator. *Derivative consistency is operator-TRUSTED, not constructed:* an operator hand-writes `evaluate` and `derivative` as independent methods (`sources/cam_card.py:138`, `:149`), and the architecture trusts the author to keep them consistent — it does not differentiate one to check the other. (ASSERTED — see [`adr-derivatives-operator-trusted.md`](../decisions/adr-derivatives-operator-trusted.md).) |
| `CanonicalLiftModel` | (samples, operator name) | immutable; normalized 720° samples + exactly one named `LiftOperator`; the only thing an implementer supplies |
| `EngineGeometry` / `ValveGeometry` / `SpringPackage` / `Valvetrain` | part identity | source-agnostic physical context; explicit units/frames; no implicit inch/mm or crank/cam |

## Value objects

Immutable, equality-by-value, no identity, no setters. Constructed at
validate-time and never mutated. "Changing" one means constructing a new one.

- **`Quantity[Unit]`** — the sealed, phantom-typed stamped scalar that crosses the
  boundary (carrying unit, frame, and provenance). Construction is sealed: a value
  is *minted* by an acquisition factory (`measured`/`inferred`/`extrapolated`),
  never built with a `provenance=` argument. Arithmetic is defined only between
  matching `(unit, frame)`; the result inherits the **weakest** input provenance
  (the lattice join). It is **not** a `float` subclass — RFC 0001 §9 proved a float
  subclass cannot make `mm + inch` a type error. `ProvFloat` is now a back-compat
  alias (`ProvFloat = Quantity[Any]`), not the model.
- **`Provenance`** — `IntEnum` lattice `MEASURED(2) > INFERRED(1) > EXTRAPOLATED(0)`;
  `min()` is the join. **No setter** — a value's provenance is *computed* from its
  inputs, never asserted. "High confidence" must be *earned*, not declared.
- **`Angle[Crank|Cam]`** — phantom-typed angle; a crank/cam mix-up is a type error.
- **`ProvenanceMap`** — interval map (`bisect`, O(log N)) from crank region to
  provenance; the per-region fitness backbone (Pillar C).
- **`Unit`** (`inch | mm | …`), **`Frame`** (`valve_side | cam_side`, timing
  reference), **`AnalysisKind`** (what `is_good_enough_for` is asked about).

## Domain rules as executable artifacts (the conformance corpus)

The honesty of the model is not a convention; it is a **frozen adversary corpus**
(Pillar D). Each trap is a domain rule rendered as a test the boundary must pass by
*refusing or being unable to construct* the trap:

- a non-monotone-then-returns lift; a never-closes lift;
- an `mm`-labeled-as-`inch` profile; a card with `advertised_duration < duration@0.050″`;
- a sparse-lookup profile masquerading as continuous;
- a `CompositeProfile` whose blend seam injects phantom jerk;
- an analysis module that imports anything from `sources` (the C1 leak).

This is not "we happened to write some tests." It is the load-bearing shape: the
boundary's correctness is *defined* by the attacks it withstands, so the spec grows
by adversary, not only by feature. The corpus is the thing that keeps Pillars A/B/C
honest as the codebase grows.

## The typed boundary as the write surface

In DDD terms, the `CamProfile` query surface is the model's *application service*
boundary, and the sealed `Quantity[Unit]` value type is its grammar:

- An analysis obtains numbers **only** by calling the eight C5 queries; there is no
  other supported way to get a value out of a profile.
- A profile returns values **only** as `Quantity[Unit]`/`Angle` (the `ProvFloat`
  alias); there is no supported way to hand analysis a bare `float`.
- The provenance lattice means the *one* path that downgrades trust (interpolate,
  extrapolate, smooth, differentiate beyond Nyquist support) is the *automatic*
  path; you cannot opt out by relabeling.

This is what makes the vocabulary load-bearing: an analysis cannot "just read the
cam card" because the boundary doesn't expose it, and it cannot fake a measured
value because provenance has no setter. The model is enforced by *what the types
will let you say*.

## The resolved round-2 edge

Two modeling questions round 1 surfaced and round 2 resolved into the current
build direction:

1. **Ergonomics-as-integrity.** The honest value is the sealed `Quantity[Unit]`:
   it carries provenance, `float(x)` is the one bare-scalar exit, and there is no
   `.magnitude` to strip. (RFC 0001 revised the round-2 "float subclass" sketch to
   this value object — see §9.) *Build status: VERIFIED.*
2. **Honesty under discontinuity.** Safety-facing analyses return formal refusals
   or `UNDECIDABLE_FROM_CAM_CARD` when the profile cannot prove a verdict. *Build
   status of the single-curve refusal path: VERIFIED. The stronger two-curve
   bracketed verdict-agreement (D013) is `DESIGNED`, not built — today PTV/spring
   are single-curve PASS/FAIL/UNDECIDABLE.*

## What this isn't

- A justification for adding more abstractions for their own sake.
- An assertion that DDD is the only valid framing.

It is the framing the model already has. This document writes it down so a reader
can see it instead of reverse-engineering it.

## See also

- [`UBIQUITOUS_LANGUAGE.md`](../reference/ubiquitous-language.md) — the glossary; this document's load-bearing dependency.
- [`PROBLEM_BRIEF.md`](../design/PROBLEM_BRIEF.md) — the framed question and the C1–C6 invariants.
- [`ROUND1_SYNTHESIS.md`](../design/ROUND1_SYNTHESIS.md) — the pillars and traps this model is built from.
- [`decision-log.md`](../decisions/decision-log.md) — the boundary decisions; the precedents this framing rests on.
