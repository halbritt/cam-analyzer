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
| Reporting | Markdown summary with lift-threshold durations, quality warnings, and an install checklist; static RFC-0004 chart-projection JSON via `cam-analyze --charts json`; overlap-centered -180° to +180° static SVAJ SVG with confidence bands, hard event markers, threshold lines, summary panel, and secondary 720° overview via `cam-analyze --charts svg` (HTML / PDF / ECharts / webapp are `DESIGNED`, not built) |

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

C1, C3, and C6 are not enforced by reviewer vigilance — they are enforced by
tests and the type checker. C1 by an import guard
([`tests/test_architecture_boundary.py`](tests/test_architecture_boundary.py));
C3 by sealed construction (a `Quantity` can't be built without the module-private
mint token, and no public callable accepts a `provenance=` argument); C6 by
phantom-typed units and frames (`mm(5) + inch(1)` and passing a cam angle where a
crank angle is required are `mypy --strict` errors). The executable
[conformance corpus](src/cam_analyzer/conformance/__init__.py) ties these to CI.
That is the design's central bet. (C2/C4/C5 remain conventions, not tests.)

## Architecture

Three layers, one direction of dependency (outer depends inward, never the reverse):

```
sources/      cam_card, OCR, CSV, Cam Doctor, lobe coords  ──┐ produce
                                                             ▼
profile/      CamProfile (port)  ◀── CanonicalLiftModel + named LiftOperator
              quantity (ProvFloat·Unit·Frame·Provenance lattice)
              provenance_map (per-crank-region fitness)
                                                             ▲ consume only this
analysis/     timing · overlap · DCR · PTV · spring · jerk · sensitivity · report ──┘
conformance/  the frozen adversary corpus every profile must refuse
```

The design rests on three pillars that are facets of one architecture, plus a
conformance discipline that keeps them honest — see
[`ARCHITECTURE.md`](ARCHITECTURE.md):

- **A · Typed boundary.** No bare `float` crosses the boundary; every value is a
  sealed `Quantity[Unit]` carrying unit, frame, and a provenance that is a
  *computed* monotone lattice (`MEASURED > INFERRED > EXTRAPOLATED`) with no
  setter. Construction is sealed (RFC 0001): provenance is *conferred* by
  acquisition factories (`measured`/`inferred`/`extrapolated`), never passed as an
  argument, and combinators only ever min-join it down. `ProvFloat` is now a
  back-compat annotation alias for `Quantity`.
- **B · One canonical representation.** A profile is a `@final` facade over one
  immutable `CanonicalLiftModel` + a named operator; the eight queries are
  *generated* projections that delegate to that one operator, so
  sparse-as-continuous is unconstructable. *Derivative consistency, though, is
  operator-TRUSTED, not constructed:* an operator hand-writes `evaluate` and
  `derivative` independently, so the stronger "inconsistent derivatives are
  unconstructable" over-claims (see
  [`adr-derivatives-operator-trusted.md`](docs/decisions/adr-derivatives-operator-trusted.md)).
- **C · Per-region fitness.** Provenance is per query / per crank region / per
  derivative order; safety consumers must pattern-match ignorance, so a
  fabricated seat-ramp value cannot be laundered into a "safe" verdict.
- **D · Conformance by adversary corpus.** The durable asset is the suite of
  traps a profile must refuse or be unable to construct. **9 of ~12 are
  executable** (C1 import guard; C3 sealed-mint / no-`provenance=` /
  `measured()`-confined-to-the-source-layer-plus-`analysis/safety.py` traps; C6
  cross-unit and cam-as-crank `mypy` traps); the rest stay declared-only until
  their machinery lands. The full status of every claim is tracked in
  [`docs/CLAIMS_LEDGER.md`](docs/CLAIMS_LEDGER.md).

## Round 2 — the chosen build plan

A second run (`cam_profile_architecture_r2`) took the round-1 skeleton as settled
and resolved its two open questions. The operator-facing result
([`docs/design/round2/IDEATION_SYNTHESIS.md`](docs/design/round2/IDEATION_SYNTHESIS.md))
sharpens the design into one rule and a build order:

> **A value — or a verdict — may leave the `CamProfile` boundary only if its
> fitness is proven; the instant it can't be, the boundary says so loudly.**

Build in this order — each pick answers one open question and sits on the prior:

1. **The honest value *is* the convenient value** (ergonomics-as-integrity).
   Every query returns a stamped scalar carrying one `Provenance`. There is no
   `.magnitude` field to strip; arithmetic propagates the lattice-`min` stamp; the
   sole exit is `float(x)` — grep-able. This *refines* Pillar A so the lie can never
   be cheaper than the truth.
   > ▸ **Revised by [RFC 0001](docs/rfc/0001-honest-typed-boundary.md).** Round 2
   > proposed a `float` *subclass*, but a `mypy --strict` spike (RFC §9) proved a
   > float subclass **cannot** make `mm + inch` a type error (it is-a `float`, so the
   > unit erases). The value is therefore a sealed, phantom-typed **`Quantity[Unit]`**
   > value object, not a float subclass — same ergonomics for the legal cases
   > (`float(x)`, scaling, same-unit arithmetic), but cross-unit math is now a type
   > error. NumPy interop (`ProvArray`) remains a follow-on.
2. **Derivative-capability matrix + Nyquist.** *(`VERIFIED`, partial.)* Before
   `velocity/acceleration/jerk_at` answers, check whether the data supports that
   derivative order: pass → a stamped value, fail → a structured
   `Refusal{requested_order, max_supported, reason, remedy}`. A sparse cam-card
   approximation therefore cannot emit authoritative jerk fiction.
3. **Bracketed verdict-agreement** (honesty-under-discontinuity). *(`DESIGNED` —
   accepted, **not built**.)* The intent: for cliff functions (PTV contact, spring
   float) build the earliest- and latest-plausible curves from the card's own
   tolerances, run the identical analysis on both, and publish only whether the
   *verdict* agrees; a flip emits **`UNDECIDABLE_FROM_CAM_CARD`**, never a number.
   **In code today this is *not* built** — `analysis/piston_to_valve.py` and
   `analysis/spring_safety.py` are single-curve PASS/FAIL/`UNDECIDABLE_FROM_CAM_CARD`
   with no two-curve loop. The C4/D009 "swap ≠ verdict-stable" honesty currently
   rests on the single-curve refusal; the bracket is deferred roadmap work.

★ **Non-obvious pick — separate the *threshold owner* from the *curve owner*.** The cliff
lives in the policy, not the curve: a named threshold policy owns *where safe becomes
unsafe*, distinct from whoever owns the lift curve — so when a verdict flips you learn
*whose threshold* flipped it. It is what makes pick 3's `UNDECIDABLE` accountable.

**Wildcard (a future round):** when a verdict bracket straddles the cliff, have the
profile emit the single cheapest measurement that would collapse it — turning "we don't
know" into a ranked measurement work order.

The decision log tracks them as the resolution of the two open questions
([D012/D013](docs/decisions/decision-log.md)). Their typed-boundary facet was then
sharpened by [RFC 0001](docs/rfc/0001-honest-typed-boundary.md):
`src/cam_analyzer/quantity.py` now implements a **sealed, phantom-typed
`Quantity[Unit]`** value object (provenance conferred, not declared; units/frames
in the type). `ProvFloat` remains as a back-compat annotation alias.

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
  how-to/  tutorials/      task and learning docs
  design/                  round-1 ideation provenance (problem brief, branches, synthesis)
  operator/                striatum run provenance (workflows, decisions)
```

## Quick Start

```bash
# install in editable mode and run the checks
python -m venv .venv && . .venv/bin/activate
pip install -e '.[dev]'
pytest

# default CLI output is Markdown; RFC 0004 adds optional JSON/SVAJ chart output
cam-analyze --reference
cam-analyze --reference --charts json
cam-analyze --reference --charts svg > reference-svaj.svg
```

A committed example of that SVAJ SVG output lives at
[`examples/wr250r-webcam-81651-reference-valve-lift.svg`](examples/wr250r-webcam-81651-reference-valve-lift.svg).
For a raster sanity check before publishing chart changes, render and inspect the
SVG with:

```bash
python scripts/verify_svg_layout.py examples/wr250r-webcam-81651-reference-valve-lift.svg --png /tmp/reference-svaj.png
```

Milestone 1 is implemented: the reference cam card can produce intake and exhaust
`CamProfile` objects, run source-blind timing/overlap and approximate DCR, and
return formal refusals or undecidable (single-curve) safety verdicts where
cam-card evidence is insufficient.

## Enforcement

The boundary guarantees are only load-bearing if the mechanism runs without being
asked. The repo ships that mechanism:

```bash
make check    # pytest + mypy (--strict) + ruff check + import-linter (lint-imports)
make hooks    # git config core.hooksPath .githooks  — enable the pre-push hook
```

- **`make check`** runs the full guard set: `pytest` (incl. the conformance
  corpus), `mypy --strict` (the phantom-unit/frame guarantee), `ruff check`, and
  `lint-imports` (the C1 one-way-dependency boundary). When `mypy` is required
  (`CAM_ANALYZER_REQUIRE_MYPY=1`, set by the hook/CI) its absence is a hard
  failure, not a silent skip.
- **`make hooks`** enables `.githooks/pre-push`, which runs `make check` before a
  push so a violation can't reach the remote. (Equivalent to
  `git config core.hooksPath .githooks`.)
- `src/cam_analyzer/py.typed` ships so the unit/frame typing guarantee survives a
  downstream `pip install`.

Every reconciled doc claim carries a build-status stamp
(`VERIFIED`/`ASSERTED`/`DESIGNED`); the manifest is
[`docs/CLAIMS_LEDGER.md`](docs/CLAIMS_LEDGER.md).

## Documentation

- [`ARCHITECTURE.md`](ARCHITECTURE.md) — the map; start here.
- [`docs/explanation/domain-driven-design.md`](docs/explanation/domain-driven-design.md) — what's load-bearing and why.
- [`docs/reference/ubiquitous-language.md`](docs/reference/ubiquitous-language.md) — the canonical glossary.
- [`docs/reference/spec.md`](docs/reference/spec.md) — the product boundary (source of truth).
- [`docs/decisions/decision-log.md`](docs/decisions/decision-log.md) — the boundary decisions and why (each with a build-status stamp).
- [`docs/CLAIMS_LEDGER.md`](docs/CLAIMS_LEDGER.md) — every decision/feature/guard × `VERIFIED`/`ASSERTED`/`DESIGNED` × witness.
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
`accepted` vs `proposed` and stamps each with a build status.

> **Attribution caveat (honesty note).** The round-1 run *wedged* at the
> diverge→converge fan-in; convergence and synthesis were reproduced out-of-band.
> The round-1 diverge fleet was **3 Claude + 2 Codex lanes — there was no Gemini
> lane** — so the "all three frontier models" / "Pillar C · Gemini" attributions
> in `ROUND1_SYNTHESIS.md` are corrected there. The *ideas* have real committed
> branch provenance; the per-model deepen attributions do not. See the
> [run retrospective](CAM_ANALYZER_RUN_RETROSPECTIVE_CAM_PROFILE_ARCHITECTURE_0D48EDE6_CLAUDE_OPUS_4_8_2026-06-16.md)
> §8 for the model-checked account.
