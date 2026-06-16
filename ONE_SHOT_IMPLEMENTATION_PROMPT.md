# One-Shot Implementation Prompt

Status: executable prompt for a future implementation agent.

Use this to finish `cam-analyzer` as a coherent v0.1 / Milestone-1 vertical
slice. "Finish" means the current architecture skeleton becomes a usable,
tested Python package that can turn the reference cam card into honest
`CamProfile` objects and run source-blind analyses that either produce stamped
answers or formally refuse. It does not mean implementing OCR, Cam Doctor
imports, full measured-data pipelines, PDF reports, or a complete physical PTV
engine in the same pass.

## Implementation Plan

1. Baseline the repo.
   - Read `AGENTS.md`, `README.md`, `ARCHITECTURE.md`, `docs/index.md`,
     `docs/reference/spec.md`, `docs/reference/ubiquitous-language.md`,
     `docs/decisions/decision-log.md`, and
     `docs/design/round2/IDEATION_SYNTHESIS.md`.
   - Run the existing tests before editing:
     `python3 -m pytest tests/test_architecture_boundary.py`.
   - Keep the C1 rule green: `cam_analyzer.analysis` never imports
     `cam_analyzer.sources`.

2. Lock the public contract with tests first.
   - Add focused tests for the value layer, provenance propagation, refusal
     results, cam-card validation, cam-card-to-profile construction, generated
     profile queries, timing/overlap, DCR refusal/downgrade behavior, and the
     architecture import guard.
   - Add conformance tests for the existing traps that can be executable now:
     `advertised_lt_050`, `fabricated_nose_as_measured`,
     `sparse_as_continuous`, and `analysis_imports_source`.

3. Implement the value and result layer.
   - Keep `Provenance` and `Angle`.
   - Implement D012 as a real `ProvFloat`: a `float` subclass carrying
     `provenance`, `unit`, and `frame`. Arithmetic must preserve unit/frame
     compatibility and propagate the weakest provenance with `Provenance.join`.
   - Keep backward-compatible names only where they reduce churn. Do not keep
     `.magnitude` as the normal in-system path.
   - Add a first-class `Refusal` result with fields such as
     `requested`, `reason`, `remedy`, and optional `provenance`.
   - Add small typed result/verdict objects only where needed. Avoid broad
     framework abstractions.

4. Implement the canonical profile core.
   - Extend `LiftOperator` so a named operator can report derivative capability
     by crank interval or by a simple `max_supported_derivative(order, angle)`
     query.
   - Implement `CanonicalCamProfile` once. Its query methods delegate to the
     operator and stamp all returned values from `ProvenanceMap` plus derivative
     capability. Do not allow source-specific method bodies.
   - Implement `ProvenanceMap.derivative_map()` or an equivalent capability
     path that ensures differentiation can only preserve or lower provenance.
   - Implement `events_at_lift`, `duration_at_lift`, `max_lift`, and
     `area_under_curve` robustly enough for the cam-card operator. Use pure
     Python math/numerical integration unless a dependency is truly justified.

5. Implement Milestone 1: cam card to profiles.
   - Make `CamCard.wr250r_reference()` construct the Web Cam 81-651 reference
     values from `docs/reference/spec.md`.
   - Resolve the current ambiguity around `CamCardApproxProfile(card)`: expose
     an explicit source-layer factory that returns both intake and exhaust
     `CamProfile` instances, or two side-specific factories with clear names.
   - Implement the named cam-card operator. It may remain
     `HalfSineCamCardOperator`, but it must honestly reconcile peak lift,
     advertised duration, duration at 0.050 in, and lobe center. If a simple
     half-sine cannot fit both duration points, use a documented sine-power
     variant inside the named operator and update docs/tests to match.
   - A cam-card approximation must never emit `MEASURED` provenance. Anchor
     information may be `INFERRED`; unsupported low-lift/nose/derivative regions
     must downgrade or refuse according to D006/D014.

6. Implement source-blind analysis surfaces.
   - Timing: centerline, lobe separation angle, overlap at a requested lift,
     and a basic 720-degree timing map. Consume only `CamProfile`.
   - Dynamic compression: add source-agnostic engine geometry input types and
     compute an approximate DCR from intake closing when the profile can support
     the query. If the needed low-lift closing is unsupported, return `Refusal`
     or a downgraded stamped result rather than a fake precise answer.
   - PTV and spring safety: add the source-agnostic input/result types and
     threshold-policy/verdict objects from D013-D016. It is acceptable for v0.1
     to return `UNDECIDABLE FROM CAM CARD` or `Refusal` when the profile cannot
     support the required derivative/clearance evidence. Do not fabricate a
     safety number from a cam card alone.
   - Reporting: add a simple Markdown/text report function for the reference
     card that includes stamped values and refusal/verdict explanations. Do not
     add PDF/HTML machinery in this pass.

7. Keep docs current.
   - Update `README.md`, `ARCHITECTURE.md`, `docs/reference/ubiquitous-language.md`,
     `docs/reference/spec.md`, and `docs/decisions/decision-log.md` only where
     implementation changed the accepted contract.
   - If D012 replaces `Quantity` with `ProvFloat`, update all stale wording
     instead of leaving round-1 docs to contradict code.
   - If the operator is a sine-power cam-card approximation rather than a pure
     half-sine, document that explicitly and explain why.

8. Final validation.
   - Remove implementation stubs from `src/cam_analyzer`; no live code path
     should raise `NotImplementedError`.
   - Run:
     `python3 -m pytest`
     `python3 -m mypy src/cam_analyzer`
     `python3 -m ruff check src tests`
     `lint-imports`
     `git diff --check`
   - If a tool is missing, install the dev extra with `python3 -m pip install -e '.[dev]'`
     and retry. If a gate still cannot run, report the exact reason.

## Prompt

You are Codex working in `/home/halbritt/git/cam-analyzer`.

Your job is to finish the repository as a coherent v0.1 / Milestone-1 Python
package in one implementation pass. The finished slice must let a user construct
the reference Web Cam 81-651 cam card, convert it into source-agnostic intake
and exhaust `CamProfile` objects, run the implemented source-blind analyses, and
receive stamped answers or formal refusals instead of fabricated precision.

Do not widen scope into OCR, PDF parsing, Cam Doctor import, measured-data
pipelines, a GUI, full physical piston-to-valve modeling, full spring dynamics,
or PDF/HTML report generation. Add extension seams and honest refusal results
for those future capabilities, but keep this pass shippable.

Before editing, read:

- `AGENTS.md`
- `README.md`
- `ARCHITECTURE.md`
- `docs/index.md`
- `docs/reference/spec.md`
- `docs/reference/ubiquitous-language.md`
- `docs/decisions/decision-log.md`
- `docs/design/round2/IDEATION_SYNTHESIS.md`
- all touched modules and nearby tests

Non-negotiable constraints:

- Preserve C1: `cam_analyzer.analysis` must never import
  `cam_analyzer.sources`.
- Preserve C2: the first durable output is `cam card -> CamProfile`.
- Preserve C3: measured, inferred, and extrapolated values remain distinct on
  every observable value.
- Preserve C4 correctly: source swaps require no analysis-code change, but may
  change verdicts.
- Preserve C5: analyses speak the profile query surface, not source records.
- Preserve C6: units and frames are explicit; no silent crank/cam, inch/mm, or
  source-specific coercion.
- Implement D012-D016 enough that stamped values, derivative refusals,
  threshold policies, and `UNDECIDABLE FROM CAM CARD` are real behavior, not
  just documentation.

Work test-first where practical. Add focused tests before each major behavior:
`ProvFloat`, `Refusal`, cam-card validation, cam-card-to-profile construction,
generated profile queries, timing/overlap, DCR, source-blind import boundaries,
and executable conformance traps.

Implementation sequence:

1. Run the existing boundary test and record the baseline.
2. Implement `ProvFloat` and formal refusal/result types.
3. Implement the canonical profile facade, provenance/capability handling, and
   operator-backed C5 queries.
4. Implement the cam-card source factory for intake and exhaust profiles.
5. Implement the cam-card operator so it fits or honestly documents the reference
   cam-card constraints. Do not claim `MEASURED` provenance for generated values.
6. Implement source-blind timing and overlap.
7. Implement approximate DCR with source-agnostic geometry and refusal/downgrade
   behavior for unsupported low-lift evidence.
8. Implement source-agnostic PTV/spring result types, threshold policies, and
   bracketed-verdict/refusal behavior. Returning `UNDECIDABLE FROM CAM CARD` is
   correct when evidence is insufficient.
9. Implement a simple Markdown/text report for the reference card showing
   stamped values and refusal/verdict explanations.
10. Update docs only where code changed the contract.
11. Run the full validation set.

Acceptance criteria:

- `CamCard.wr250r_reference()` is usable.
- There is a clear public API to get intake and exhaust `CamProfile` objects
  from that cam card.
- `lift_at`, `events_at_lift`, `duration_at_lift`, `max_lift`, and
  `area_under_curve` work for the cam-card profiles.
- Derivative queries either return stamped values within supported capability
  or return `Refusal` with a concrete reason/remedy.
- Timing, overlap, and approximate DCR run without importing source-layer code.
- PTV/spring surfaces do not fabricate safety from a cam card; they return a
  formal refusal or `UNDECIDABLE FROM CAM CARD` when required.
- The architecture import guard remains green.
- No `NotImplementedError` remains in production code.
- Docs no longer contradict the implemented value model.
- These commands pass or have a precise, reproducible skip reason:
  `python3 -m pytest`
  `python3 -m mypy src/cam_analyzer`
  `python3 -m ruff check src tests`
  `lint-imports`
  `git diff --check`

Final response requirements:

- Summarize the implemented behavior, not just files touched.
- List validation commands and results.
- Name any deliberately deferred capabilities.
- Do not claim full physical safety analysis from cam-card-only evidence.
