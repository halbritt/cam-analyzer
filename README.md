# cam-analyzer

A camshaft analysis toolkit built around one load-bearing idea: **every analysis
depends only on a `CamProfile`, never on where the profile came from** — and a
profile can never silently pass off an *inferred* curve as a *measured* one.

It starts from a sparse cam card (the reference part is the Web Cam 81-651 for a
Yamaha WR250R, DOHC 4-valve) and must survive the arrival of richer data sources
— measured dial-indicator lift, Cam Doctor exports, scanned lobe coordinates,
full valvetrain-dynamics models — **without changing a line of analysis code**.

> Status: **architecture / DDD skeleton.** Two divergent-ideation rounds are
> complete: round 1 settled the boundary skeleton (Pillars A/B/C + conformance D),
> round 2 resolved its two open questions into a concrete build plan
> ([Round 2](#round-2--the-chosen-build-plan)). This repo currently holds the design,
> the decision record, and a typed package skeleton that structurally enforces the
> boundary — not a finished analyzer.

## What It Does

Given a cam card, engine geometry, and (optionally) measured lift data, the
finished product computes:

| Analysis | Question it answers |
|---|---|
| Timing | centerlines, LSA, overlap at advertised and 0.050″ timing, full 720° map |
| Lift reconstruction | continuous valve-lift curve + velocity / acceleration / jerk |
| Dynamic compression | effective stroke, DCR, trapped CR, cranking-pressure estimate |
| Piston-to-valve | minimum intake/exhaust clearance, crank angle of minimum, safety margin |
| Valve-spring safety | coil-bind margin, retainer-to-guide margin, seat/open pressure, float RPM |
| Acceleration / jerk | valvetrain dynamics from the curve's derivatives |
| Install sensitivity | how advance/retard, lash, and deck/gasket variation move every result |
| Reporting | HTML / PDF / Markdown summary with warnings and an install checklist |

Every one of these consumes **only** the `CamProfile` query surface. None of them
can see a `CamCard`, a PDF/CSV parser, or a measured-data file.

## The CamProfile Boundary

`CamProfile` is the continuous-query surface analyses speak — and the **only**
language they speak:

```python
lift_at(angle)          velocity_at(angle)      acceleration_at(angle)
jerk_at(angle)          events_at_lift(lift)    duration_at_lift(lift)
max_lift()              area_under_curve()
```

Six invariants make the boundary load-bearing rather than decorative
(full text in [`docs/reference/ubiquitous-language.md`](docs/reference/ubiquitous-language.md)
and the brief in [`docs/design/PROBLEM_BRIEF.md`](docs/design/PROBLEM_BRIEF.md)):

- **C1 — One-way dependency.** Analysis imports `CamProfile` and nothing source-specific.
- **C2 — Milestone discipline.** Milestone 1 is `cam card → CamProfile`, *not* `cam card → DCR`.
- **C3 — Measured ≠ inferred.** Any observable value can be told apart as measured or inferred.
- **C4 — Hot-swappable source.** Swapping an approximate profile for a measured one changes no analysis code.
- **C5 — Stable consumer vocabulary.** The eight queries above are fixed; how they are backed is open.
- **C6 — Unambiguous frames & units.** Crank vs cam degrees, valve- vs cam-side lift, seat vs 0.050″, inch vs mm — explicit and non-guessable at the boundary.

C1 and C3 are not enforced by reviewer vigilance — they are enforced by a test
(see [`tests/test_architecture_boundary.py`](tests/test_architecture_boundary.py)
and the conformance corpus). That is the design's central bet.

## Architecture

Three layers, one direction of dependency (outer depends inward, never the reverse):

```
sources/      cam_card, OCR, CSV, Cam Doctor, lobe coords  ──┐ produce
                                                             ▼
profile/      CamProfile (port)  ◀── CanonicalLiftModel + named LiftOperator
              quantity (Quantity·Unit·Frame·Provenance lattice)
              provenance_map (per-crank-region fitness)
                                                             ▲ consume only this
analysis/     timing · overlap · DCR · PTV · spring · jerk · sensitivity · report ──┘
conformance/  the frozen adversary corpus every profile must refuse
```

The design rests on three pillars that are facets of one architecture, plus a
conformance discipline that keeps them honest — see
[`ARCHITECTURE.md`](ARCHITECTURE.md):

- **A · Typed boundary.** No bare `float` crosses the boundary; every value is a
  `Quantity{magnitude, unit, frame, provenance}` and provenance is a *computed*
  monotone lattice (`MEASURED > INFERRED > EXTRAPOLATED`) with no setter.
- **B · One canonical representation.** A profile is a `@final` facade over one
  immutable `CanonicalLiftModel` + a named operator; the eight queries are
  *generated* projections (derivatives differentiate one operator), so
  inconsistent derivatives are unconstructable.
- **C · Per-region fitness.** Provenance is per query / per crank region / per
  derivative order; safety consumers must pattern-match ignorance, so a
  fabricated seat-ramp value cannot be laundered into a "safe" verdict.
- **D · Conformance by adversary corpus.** The durable asset is the frozen suite
  of traps a profile must refuse; it turns C1/C3/C4 into tests.

## Round 2 — the chosen build plan

A second run (`cam_profile_architecture_r2`) took the round-1 skeleton as settled
and resolved its two open questions. The operator-facing result
([`docs/design/round2/IDEATION_SYNTHESIS.md`](docs/design/round2/IDEATION_SYNTHESIS.md))
sharpens the design into one rule and a build order:

> **A value — or a verdict — may leave the `CamProfile` boundary only if its
> fitness is proven; the instant it can't be, the boundary says so loudly.**

Build in this order — each pick answers one open question and sits on the prior:

1. **`ProvFloat` — the honest value *is* the convenient value** (ergonomics-as-integrity).
   Every query returns a `float` *subclass* carrying one `Provenance` stamp. There is no
   `.magnitude` field to strip; arithmetic propagates the lattice-`min` stamp; the sole
   exit is `float(x)` — ugly, grep-able, lint-flagged. This *refines* Pillar A: the
   round-1 `Quantity` wrapper becomes a stamped scalar, so the lie can never be cheaper
   than the truth. Mandatory follow-on: `ProvArray` for NumPy, where `np.asarray`
   silently drops a subclass.
2. **Derivative-capability matrix + Nyquist.** Before `velocity/acceleration/jerk_at`
   answers, check whether the data supports that derivative order: pass → a stamped
   value, fail → a structured `Refusal{requested_order, max_supported, reason, remedy}`.
   A sparse half-sine cam-card backing therefore cannot emit authoritative jerk fiction.
3. **Bracketed verdict-agreement** (honesty-under-discontinuity). For cliff functions
   (PTV contact, spring float) build the earliest- and latest-plausible curves from the
   card's own tolerances, run the identical analysis on both, and publish only whether
   the *verdict* agrees; a flip emits **`UNDECIDABLE FROM CAM CARD`**, never a number.
   This is C4/D009 honored by construction.

★ **Non-obvious pick — separate the *threshold owner* from the *curve owner*.** The cliff
lives in the policy, not the curve: a named threshold policy owns *where safe becomes
unsafe*, distinct from whoever owns the lift curve — so when a verdict flips you learn
*whose threshold* flipped it. It is what makes pick 3's `UNDECIDABLE` accountable.

**Wildcard (a future round):** when a verdict bracket straddles the cliff, have the
profile emit the single cheapest measurement that would collapse it — turning "we don't
know" into a ranked measurement work order.

These are the latest design direction, not yet committed code. The decision log tracks
them as the resolution of the two open questions ([D012/D013](docs/decisions/decision-log.md)),
and `src/cam_analyzer/quantity.py` still implements the round-1 `Quantity` form pending
the `ProvFloat` refinement.

## Repository Layout

```
README.md                  this file
ARCHITECTURE.md            the navigable map (boundary, layers, pillars)
prompt.md                  the original request
Camshaft_Analysis_Spec.md  the source product spec (reference numbers, modules)
src/cam_analyzer/          typed package skeleton (boundary + layers)
tests/                     boundary-conformance tests
docs/
  explanation/             why it is this way — incl. domain-driven-design.md
  reference/               ubiquitous-language.md, spec pointer
  decisions/               the decision log (ADRs)
  how-to/  tutorials/      task and learning docs (stubs)
  design/                  round-1 ideation provenance (problem brief, branches, synthesis)
  operator/                striatum run provenance (workflows, decisions)
```

## Quick Start

```bash
# (skeleton) install in editable mode and run the boundary guard
python -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
pytest tests/test_architecture_boundary.py   # C1/C3 enforced by test, not vigilance
```

The implementation modules currently raise `NotImplementedError` with a docstring
naming the invariant they must uphold. The boundary test and the package
structure are real; the numerics are not yet written.

## Documentation

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — the map; start here.
- [`docs/explanation/domain-driven-design.md`](docs/explanation/domain-driven-design.md) — what's load-bearing and why.
- [`docs/reference/ubiquitous-language.md`](docs/reference/ubiquitous-language.md) — the canonical glossary.
- [`docs/reference/spec.md`](docs/reference/spec.md) — the product boundary (source of truth).
- [`docs/decisions/decision-log.md`](docs/decisions/decision-log.md) — the boundary decisions and why.
- [`docs/index.md`](docs/index.md) — every doc, one line each.

## Provenance

This architecture was produced by two multi-model divergent-ideation runs
(`cam_profile_architecture`, `_r2`) under [striatum](https://github.com/halbritt/striatum):
branch frames diverged on the boundary problem, and synthesis passes distilled the
pillars and the build plan above.

- Round 1 — problem framing: [`docs/design/PROBLEM_BRIEF.md`](docs/design/PROBLEM_BRIEF.md)
- Round 1 — synthesis (the pillars): [`docs/design/ROUND1_SYNTHESIS.md`](docs/design/ROUND1_SYNTHESIS.md)
- Round 1 — branch ideas: [`docs/design/branches/`](docs/design/branches/)
- Round 2 — build plan: [`docs/design/round2/IDEATION_SYNTHESIS.md`](docs/design/round2/IDEATION_SYNTHESIS.md) · [`CONVERGENCE.md`](docs/design/round2/CONVERGENCE.md) · [branches](docs/design/round2/branches/) · [deepened picks](docs/design/round2/deepened/)
- Process audit of the round-1 run: [`CAM_ANALYZER_RUN_RETROSPECTIVE_CAM_PROFILE_ARCHITECTURE_0D48EDE6_CLAUDE_OPUS_4_8_2026-06-16.md`](CAM_ANALYZER_RUN_RETROSPECTIVE_CAM_PROFILE_ARCHITECTURE_0D48EDE6_CLAUDE_OPUS_4_8_2026-06-16.md)

Both rounds are syntheses, not frozen decisions: round 1 settled the skeleton
(Pillars A/B/C + the conformance discipline D); round 2 resolved the two open
questions into the build plan above. The decision log marks which parts are
`accepted` vs `proposed`.
