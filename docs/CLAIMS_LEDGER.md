# Claims Ledger — build-status provenance for every notable claim

This ledger is the in-repo antidote to *asserted masquerading as verified*. Every
notable decision, feature, guard, pillar, and analysis is stamped with a **build
status** and its **witness**, so a reader never has to take a doc's word that
something is "implemented" / "enforced".

The status vocabulary is the project's own `MEASURED > INFERRED > EXTRAPOLATED`
lattice lifted onto *build state*:

| Status | Meaning |
|---|---|
| **VERIFIED** | A passing executable witness exists: a named test, a `file:line`, or a CLI command + expected output. |
| **ASSERTED** | A doc/decision says so; no executable witness pins it. (True by discipline, not by construction.) |
| **DESIGNED** | Explicitly **not built** — accepted/sketched as a direction, but no code. |

> No artifact in this repo may use a completion word ("implemented", "enforced",
> "accepted/done") above the status its witness earns. When code and a claim
> disagree, **the claim is wrong** — fix the claim (or build the witness), not the
> stamp.

Witnesses are relative to the repo root. Tests are referenced as
`tests/<file>.py::<test>` or by the corpus trap name. `Date: 2026-06-17`.

---

## Decisions (decision-log D-numbers)

| ID | Claim (short) | Status | Witness | Notes |
|---|---|---|---|---|
| D001 | One-way dependency (C1): analysis imports only `CamProfile` | **VERIFIED** | `tests/test_architecture_boundary.py`; corpus trap `analysis_imports_source`; `lint-imports` contract in `pyproject.toml` | Also runs under `make check` (imports). |
| D002 | Measured ≠ inferred, carried in the value (C3) | **VERIFIED** | `tests/test_conformance_traps.py::test_quantity_unsealed_construction_is_rejected`, `::test_no_public_value_factory_confers_provenance_by_argument` | |
| D003 | M1 is `cam card → CamProfile` (C2) | **VERIFIED** | `tests/test_cam_card_source.py` exercises `profiles_from_cam_card(CamCard.wr250r_reference())` | |
| D004 | Typed boundary (Pillar A): sealed stamped value, no setter | **VERIFIED** | sealed-mint + phantom-type traps in `tests/test_conformance_traps.py` | Refined by RFC 0001 (value object, not float subclass). |
| D005 | Single canonical representation (Pillar B) | **ASSERTED** (one operator) / **DESIGNED** (derivative-consistency) | `tests/test_conformance_traps.py::test_sparse_as_continuous_refuses_eight_point_lookup` (sparse-as-continuous only) | `evaluate`/`derivative` are independent hand-written methods (`sources/cam_card.py:138`, `:149`); consistency is operator-TRUSTED. See `adr-derivatives-operator-trusted.md`. |
| D006 | Per-region fitness + first-class ignorance (Pillar C) | **VERIFIED** | `tests/test_provenance_map.py`; `tests/test_safety_and_reporting.py` (PTV/spring `UNDECIDABLE_FROM_CAM_CARD` via `is_good_enough_for`) | |
| D007 | Conformance by adversary corpus (Pillar D) | **VERIFIED** (partial) | `_EXECUTABLE_TRAPS` set, `tests/test_conformance_traps.py:23` (9 of ~12 executable) | Declared-only traps (e.g. `seam_phantom_jerk`) are `DESIGNED`. |
| D008 | Confidence-as-scalar | n/a (**rejected**) | — | Kept as provenance; superseded by D006. |
| D009 | C4 is code-stability, not verdict-stability | **ASSERTED** | docs (`domain-driven-design.md`) state it; constructive guard is D013 (`DESIGNED`) | Today enforced only by the single-curve `UNDECIDABLE_FROM_CAM_CARD` refusal. |
| D010 | Blends must prove derivative continuity at seams | **DESIGNED** | corpus trap `seam_phantom_jerk` (`src/cam_analyzer/conformance/__init__.py:50`), **declared-only** | No `CompositeProfile` exists. |
| D011 | Ensemble / reactive-evidence-graph profile | **DESIGNED** (deferred) | — | Premature for M1. |
| D012 | Ergonomics-as-integrity (the honest value is the convenient value) | **VERIFIED** (revised by RFC 0001) | sealed-construction + phantom-type traps in `tests/test_conformance_traps.py`; `ProvFloat = Quantity[Any]` at `src/cam_analyzer/quantity.py:230` | Round-2 sketched a `float` subclass; RFC 0001 §9 proved it can't work → value object. |
| D013 | Bracketed verdict-agreement (two-curve, earliest/latest) | **DESIGNED** | — (absent from code) | `analysis/piston_to_valve.py`, `analysis/spring_safety.py` are single-curve PASS/FAIL/UNDECIDABLE; no two-curve loop. Deferred roadmap. |
| D014 | Derivative-capability matrix + Nyquist gate | **VERIFIED** (partial) | `tests/test_approximate_derivatives.py`; `tests/test_canonical_profile.py`; `Refusal` path in `profile/canonical.py:161` | `--approximate`/`approximate_anyway` downgrade built. |
| D015 | Separate threshold owner from curve owner | **VERIFIED** | `ThresholdPolicy`/`SpringThresholdPolicy` with `owner` field (`analysis/piston_to_valve.py`, `analysis/spring_safety.py`, `analysis/safety.py`) | |
| D016 | `Answer \| Refusal` at every safety-facing call | **VERIFIED** | PTV/spring return `… \| Refusal`; `velocity/acceleration/jerk_at -> Answer` (`profile/__init__.py:36-38`); `tests/test_safety_and_reporting.py` | |
| D017 | `ProvArray` — provenance through NumPy | **DESIGNED** | — (no `ProvArray` in `src`) | RFC 0001 Pillar D follow-on. |
| D018 | Value-of-information work orders | **DESIGNED** (deferred) | — | Depends on D013 brackets. |
| D019 | Honest visualization projection and rendering grammar | **VERIFIED** (partial) | `tests/test_visualization_projection.py`; `tests/test_visualization_grammar.py`; `tests/test_visualization_svg.py`; `tests/test_cli.py`; `tests/test_architecture_boundary.py` | Built: source-blind JSON projection, grammar-owned provenance legend, threshold-duration table, heuristic confidence bands, quality warnings, `cam-analyze --charts json`, overlap-centered static SVAJ SVG with hard event markers, threshold lines, summary panel, validation section, and secondary 720° overview via `cam-analyze --charts svg`. `DESIGNED`: ECharts adapter, crop-proof ledger, calibrated uncertainty bands, PTV collision chart, "go measure THIS", web UI. |

## Pillars (RFC 0001 / round-1 synthesis)

| Pillar | Claim | Status | Witness | Notes |
|---|---|---|---|---|
| A | Sealed, phantom-typed value; provenance conferred not declared | **VERIFIED** | `tests/test_conformance_traps.py` sealed-mint / no-`provenance=` traps | |
| B (units/frames) | `mm + inch` and cam-as-crank are `mypy` errors | **VERIFIED** | `tests/test_conformance_traps.py::test_phantom_types_make_unit_and_frame_errors` (runs the fixture through `mypy --strict`) | |
| B (one operator) | One canonical operator backs every query | **ASSERTED** | structural (`CanonicalLiftModel` + named operator); sparse-as-continuous trapped | |
| B (derivative consistency) | "inconsistent derivatives unconstructable" | **DESIGNED** | — | Over-claim corrected; `evaluate`/`derivative` independent. A finite-difference-consistency trap would promote to VERIFIED (`adr-derivatives-operator-trusted.md`). |
| C | Per-region/per-order provenance; pattern-match ignorance | **VERIFIED** | `tests/test_provenance_map.py`; safety `UNDECIDABLE_FROM_CAM_CARD` | |
| D (corpus) | Traps a profile must refuse = spec of correctness | **VERIFIED** (partial) | `_EXECUTABLE_TRAPS` (9/~12) | Declared-only remainder is `DESIGNED`. |
| D (ergonomic inversion) | `unsafe_strip` + `CAM001`/`CAM002` + `ProvArray` | **DESIGNED** | — (`grep -rn 'unsafe_strip\|CAM001\|CAM002\|ProvArray' src` → nothing) | Only the "no `.magnitude`, exit is `float(x)`" part is built. |

## C-guards (invariants)

| Guard | Claim | Status | Witness | Notes |
|---|---|---|---|---|
| C1 | Analysis never imports a source | **VERIFIED** | `tests/test_architecture_boundary.py`; trap `analysis_imports_source`; `lint-imports` | |
| C2 | Milestone discipline (`cam card → CamProfile`) | **ASSERTED** | convention; not a test | |
| C3 | Measured told apart from inferred; MEASURED conferral confined to **the source layer + `analysis/safety.py`** | **VERIFIED** | `tests/test_conformance_traps.py::test_measured_conferral_is_confined_to_the_source_layer` (trap `measured_confined_to_sources`); allow-list `_MEASURED_ALLOWED_FILES` (`tests/test_conformance_traps.py:39`) | Allow-list = `quantity.py` + `analysis/safety.py` + the `sources/` dir. **Strengthened (landed): the trap now also flags `Quantity._mint(..., Provenance.MEASURED)` outside the allow-list** (`tests/test_conformance_traps.py:294`), closing the keyed-mint back door — "unconstructable MEASURED" is genuinely verified, not just `measured()`-scoped. |
| C4 | Hot-swappable source (code-stable, *not* verdict-stable) | **ASSERTED** | convention; see D009/D013 | |
| C5 | Stable eight-query vocabulary | **ASSERTED** | `CamProfile` port (`profile/__init__.py`); not pinned by a "vocabulary is frozen" test | |
| C6 | Unambiguous units & frames | **VERIFIED** | `tests/test_conformance_traps.py::test_phantom_types_make_unit_and_frame_errors` (mypy) | |

## Analyses (consumer layer)

| Analysis | Status | Witness | Notes |
|---|---|---|---|
| Timing / overlap / LSA / centerlines | **VERIFIED** | `tests/test_analysis_timing.py` (`test_basic_timing_map_contains_centerlines_lsa_overlap_and_events`, …) | |
| Dynamic compression (DCR) | **VERIFIED** | `tests/test_dynamic_compression.py` — incl. `test_dynamic_compression_refuses_when_closing_resolves_before_bdc` (honest refusal, not silent full-stroke clamp) and `test_cam_card_dcr_accepts_published_closing_boundary` (WR250R reference stays green) | |
| Lift reconstruction + velocity/acceleration/jerk | **VERIFIED** (motion-law derivatives, provenance-capped) | `tests/test_cam_card_source.py`; `tests/test_canonical_profile.py`; `tests/test_approximate_derivatives.py`; `tests/test_profile_quality.py` | Cam-card derivatives are model-derived profile answers, not measured valvetrain dynamics. |
| Piston-to-valve (PTV) | **VERIFIED** (single-curve) | `tests/test_safety_and_reporting.py` | Two-curve bracketing (D013) is `DESIGNED`. |
| Valve-spring safety | **VERIFIED** (single-curve) | `tests/test_safety_and_reporting.py` | Two-curve bracketing (D013) is `DESIGNED`. |
| Install sensitivity | **DESIGNED** | — | Listed in the spec; not implemented. |
| Reporting | **VERIFIED** (Markdown + threshold durations + quality warnings + chart projection JSON + overlap-centered static SVAJ SVG) | `render_markdown_report` (`analysis/reporting.py`); `threshold_duration_table` / `profile_quality_warnings` (`analysis/profile_quality.py`); `project_cam_profiles` (`analysis/projection.py`); `render_valve_lift_svg` (`visualization/svg.py`); `tests/test_safety_and_reporting.py`; `tests/test_profile_quality.py`; `tests/test_visualization_projection.py`; `tests/test_visualization_svg.py`; `tests/test_cli.py` | **HTML / PDF / ECharts are `DESIGNED`, not built.** |
| `cam-analyze` CLI (`--reference`, card file, `--charts json`, `--charts svg`) | **VERIFIED** | `tests/test_cli.py::test_main_with_reference_flag_prints_report`, `::test_main_with_card_file`, `::test_main_incoherent_card_is_refused`, `::test_main_with_reference_flag_can_print_chart_projection`, `::test_main_with_reference_flag_can_print_svg_chart`; entry point `pyproject.toml:20` | `--charts svg` emits a static SVAJ SVG, not the full deferred chart suite. |

## Enforcement (WS-ENFORCE)

| Guard | Claim | Status | Witness | Notes |
|---|---|---|---|---|
| `make check` | Runs pytest + mypy(`--strict`) + ruff + import-linter | **VERIFIED** | `Makefile` targets `check`/`test`/`types`/`lint`/`imports` | `mypy`/`import-linter` skip cleanly if absent; `CAM_ANALYZER_REQUIRE_MYPY=1` set when mypy is importable, so a missing-but-required mypy is a hard failure. |
| pre-push hook | `make hooks` enables `.githooks/pre-push` (runs `make check`) | **VERIFIED** | `.githooks/pre-push`; `Makefile` `hooks` target (`git config core.hooksPath .githooks`) | Opt-in per clone. |
| `py.typed` | Typing guarantee survives install | **VERIFIED** | `src/cam_analyzer/py.typed`; `pyproject.toml:29` package-data | |
| mypy-honesty | Required-but-missing mypy fails, not skips | **VERIFIED** | `tests/test_conformance_traps.py::test_phantom_types_make_unit_and_frame_errors` + `CAM_ANALYZER_REQUIRE_MYPY` wiring in `Makefile` | |
| Golden `--reference` snapshot | Real DCR/LSA/centerline numbers pinned | **VERIFIED** | `tests/test_reference_report_golden.py` (full-text golden + pinned LSA 107.000 / centerlines 109.500·615.500 / DCR 11.272 / overlap 28.000 / intake-closing 228.500); fixture `tests/golden/reference_report.md` | Drives `main(["--reference"])` in-process; trailing-newline-insensitive full snapshot plus explicit numeric anchors. |
| Conformance coverage guard | Every trap is executable or explicitly declared-only (no silent gap) | **VERIFIED** | `tests/test_conformance_traps.py::test_every_corpus_trap_is_executable_or_explicitly_declared_only` (`:134`); `_EXECUTABLE_TRAPS` ∪ `conformance.DECLARED_ONLY` must cover `CORPUS` | Landed (WS-CODE2). |

---

## How to use this ledger

- Adding a feature or decision? Add a row here with its status and witness **in the
  same change**. A claim with no witness is `ASSERTED` at best.
- Promoting `ASSERTED`/`DESIGNED` → `VERIFIED` requires *naming the passing
  witness*, not asserting harder.
- The decision log carries the same `Build` stamp per row; this ledger is the
  one-screen cross-cut.

See also: [`decisions/decision-log.md`](decisions/decision-log.md),
[`decisions/adr-derivatives-operator-trusted.md`](decisions/adr-derivatives-operator-trusted.md),
[`rfc/0001-honest-typed-boundary.md`](rfc/0001-honest-typed-boundary.md),
[`../README.md` § Enforcement](../README.md).
