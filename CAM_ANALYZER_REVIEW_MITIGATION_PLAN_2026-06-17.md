# cam-analyzer — Review Mitigation Plan

**Author:** Claude Opus 4.8 (1M context) · **Date:** 2026-06-17
**Source:** `CAM_ANALYZER_DEEP_ARCHITECTURE_REVIEW_CLAUDE_OPUS_4_8_2026-06-17.md` (+ lane addendum)
**Status of this doc:** plan-of-record for the mitigation pass; executed by a parallel sub-agent fan-out.

---

## 0. Framing — read the review through the lane lens

The maintainer confirmed (and the review's addendum records) that **cam-analyzer is a test article for the striatum production lane, not the product.** That re-targets the findings: the doc-to-code ratio and `docs/operator/**` config **dissolve** (they are the lane's output, not bloat), while the **honesty defects sharpen into lane-reliability signals** — docs outrun implementation, guarantees are over-claimed, invariants go unenforced, dead code accretes.

This plan therefore acts on the **durable** findings — the ones that are real defects in the artifact regardless of unit-of-analysis — and **explicitly declines** the recommendations the addendum dissolves. Every claim we touch is stamped with **build-status provenance** (the project's own `MEASURED > INFERRED > EXTRAPOLATED` lattice, lifted to `VERIFIED > ASSERTED > DESIGNED`) so the artifact stops letting *asserted* masquerade as *verified*.

---

## 1. Triage — every finding, dispositioned

Severity is from the review (`serious` / `smell` / `missing`). Disposition is the decision for *this* pass.

| ID | Finding (review §) | Sev | Disposition | Workstream |
|----|--------------------|-----|-------------|------------|
| S1 | No automated enforcement of the guards (no CI/hook/make) | serious | **FIX** — `make check` + pre-push hook running pytest+mypy+ruff+lint-imports | WS-ENFORCE |
| inv#2 | `mypy` guarantee silently skips; no `py.typed` | serious | **FIX** — ship `py.typed`; make the skip fail loudly under enforcement | WS-ENFORCE + WS-CODE2 |
| S2 / D013 | Bracketed verdict-agreement documented "implemented" but absent | serious | **RECONCILE** — demote to `DESIGNED` everywhere; building it is deferred feature work | WS-DOCS |
| S3 / Pillar B | "Inconsistent derivatives unconstructable" over-claims (evaluate/derivative hand-written) | serious | **RECONCILE** — demote to `ASSERTED` (author-trusted), add ADR stating derivatives are operator-trusted, not constructed | WS-DOCS |
| S4 / C3 | "Unconstructable MEASURED" over-stated — `Quantity._mint(...,MEASURED)` fabricates from any module; trap only scans `measured` | serious | **FIX (strengthen code to match doc)** — extend the conformance trap to flag `_mint(...MEASURED...)` outside the source layer, so the claim becomes `VERIFIED`; correct the "confined to sources" wording to name `analysis/safety.py` too | WS-CODE2 + WS-DOCS |
| S5 / inv#6 | DCR silently clamps out-of-range intake closing to full-stroke maximal DCR with a normal stamp | serious | **FIX** — replace the silent `closing_abdc = 0.0` branch with an honest `Refusal`/`UNDECIDABLE` | WS-CODE3 |
| S6 | `ProvFloat`-as-`float`-subclass drift in glossary/D012/RFC; RFC Pillar D unimplemented | serious | **RECONCILE** — fix glossary/D012/RFC wording to `ProvFloat = Quantity[Any]`; stamp RFC Pillar D `DESIGNED` | WS-DOCS |
| S7 / inv#5 | Real critical-path numbers (`--reference` report, DCR/LSA) unpinned | serious | **FIX** — golden snapshot test of `cam-analyze --reference` pinning the real numbers | WS-CODE4 |
| lens2 | `ROUND1_SYNTHESIS.md` fabricated frontier-model attribution (retro caught it; synthesis unpatched) | serious | **RECONCILE** — patch the synthesis to match the retrospective | WS-DOCS |
| row11 | Uncertainty-band subsystem reachable only by its own tests (worst code over-engineering) | smell | **CUT** — delete `DerivativeBand`, `*_band_at`, `approximate_derivative_band`, and `test_derivative_uncertainty_band.py` (keep `--approximate` derivatives) | WS-CODE2 |
| row12 | Dead timing cluster (`timing_map`/`TimingMap`/`TimingEvents`/`events_for_profile`) | smell | **CUT** — verified zero callers; delete | WS-CODE1 |
| row17 | Back-compat shims: `result.py`, `dynamic_compression_ratio` free fn, `HalfSineCamCardOperator`, `CamCardApproxProfile` | smell | **CUT** — repoint the 2 entangled tests, then delete | WS-CODE1/2/3 |
| row10 | Unused phantom unit tags (`Ratio` 0 refs; rate tags used in test stubs only) | smell | **CUT `Ratio` only** — rate tags (`InchPerDeg*`, `InchDeg`) are exercised by test fixtures; removing them is churn with no payoff. Keep. | WS-CODE2 |
| smell | 3 of 12 conformance traps declared-only with nothing flagging the gap | smell | **FIX** — coverage guard asserting every trap is executable *or* explicitly declared-only | WS-CODE2 |
| addendum | Lane lets `ASSERTED` masquerade as `VERIFIED` (no status-provenance on claims) | durable | **FIX (in-repo manifestation)** — add a claims ledger stamping every decision `VERIFIED`/`ASSERTED`/`DESIGNED` with a named witness | WS-DOCS |

### Explicitly NOT doing (and why)

- **Rec 5 — archive `docs/operator/**`, the retrospective, the one-shot prompt; collapse the Diátaxis tree.** The addendum **dissolves** this: those files are the striatum lane's own product/source, correctly co-located. Removing them would be deleting the lane's output as if it were CLI bloat. *Declined.*
- **Rec 6 — build the install-sensitivity analysis + measured-CSV source.** Real feature work (days→week), not a defect mitigation. Belongs to the roadmap, not this pass. *Deferred.*
- **Build D013 (two-curve verdict comparison) / Pillar B construction-time derivative consistency.** Feature builds. We make the *claims honest* now (demote with status-provenance) and leave the build to the roadmap. *Deferred — tracked as `DESIGNED`.*
- **`ProvenanceMap.intervals()` / `from_mm` / `DynamicCompressionResult` property aliases / `ReportInputs` simplification (rows 7, 13, 15).** Behavior-neutral "smell" cleanups with marginal value; the specific `intervals()` method the review cites does not appear to exist as a public no-caller method (the grep hits are the constructor param + internal `_intervals`). Excluded to keep the diff focused and low-risk. *Deferred — optional later cleanup.*
- **Striatum verification-gate + claim-ledger meta-workflow.** The durable topological fix lives in `~/git/striatum/`, out of this repo. This pass implements its *in-repo manifestation* (enforcement hook + claims ledger). *Out of scope here; pointer recorded.*

---

## 2. Workstreams (disjoint file ownership → safe parallelism)

Each workstream owns a **disjoint set of files** so the agents run concurrently with no same-file races. Shared test files are assigned to a single owner.

### WS-CODE1 — Excise self-contained dead code
**Owns:** `src/cam_analyzer/result.py` (delete), `src/cam_analyzer/analysis/timing.py`, `src/cam_analyzer/__init__.py` (only if it re-exports `result`), `tests/test_value_and_result.py`.
- Delete the dead timing cluster (`TimingEvents`, `TimingMap`, `events_for_profile`, `timing_map`) — keep `basic_timing_map`/`BasicTimingMap` (live, used by reporting). Verify zero callers first.
- Delete `result.py`; repoint its only importer (`test_value_and_result.py`) to `cam_analyzer.quantity`.

### WS-CODE2 — Excise the band subsystem, cut `Ratio`, strengthen C3, conformance coverage guard, mypy honesty
**Owns:** `src/cam_analyzer/quantity.py`, `src/cam_analyzer/profile/canonical.py`, `src/cam_analyzer/sources/cam_card.py`, `src/cam_analyzer/conformance/__init__.py`, `tests/test_derivative_uncertainty_band.py` (delete), `tests/test_conformance_traps.py`.
- Delete `DerivativeBand`, `velocity/acceleration/jerk_band_at`, `_derivative_band_at` (canonical.py); `approximate_derivative_band` (cam_card.py); the whole band test file. **Keep** the `--approximate` derivative path (`approximate_derivatives=`).
- Delete the `HalfSineCamCardOperator` and `CamCardApproxProfile` aliases; repoint `test_conformance_traps.py` (`module.CamCardApproxProfile(card)` → `module.profiles_from_cam_card(card)`).
- Cut the `Ratio` tag (0 refs). **Keep** `InchPerDeg*`/`InchDeg` (used by test fixtures).
- **Strengthen C3:** extend the `measured_confined_to_sources` trap to also flag `Quantity._mint(...)` calls carrying `Provenance.MEASURED` outside the source layer (+ `analysis/safety.py`), making "unconstructable MEASURED" `VERIFIED`.
- **Conformance coverage guard:** add a test asserting every corpus trap is either executable or explicitly marked declared-only.
- **mypy honesty:** when `CAM_ANALYZER_REQUIRE_MYPY=1` (set by the hook/make/CI) and mypy is absent, the typing-trap test must **fail**, not silently skip.

### WS-CODE3 — DCR honesty + drop the `dynamic_compression_ratio` wrapper
**Owns:** `src/cam_analyzer/analysis/dynamic_compression.py`, `tests/test_dynamic_compression.py`.
- Replace the silent `closing_abdc = 0.0` full-stroke clamp with an honest `Refusal`/`UNDECIDABLE` path (closing-before-BDC is not evidence for a maximal DCR). Verify the WR250R reference card does **not** hit this branch (golden must stay green).
- Delete the `dynamic_compression_ratio` free-function wrapper; repoint/remove its legacy test; add a regression test for the new refusal behavior.

### WS-CODE4 — Golden snapshot of the deliverable
**Owns:** `tests/test_reference_report_golden.py` (new), `tests/golden/reference_report.md` (new fixture).
- Snapshot `cam-analyze --reference` output and pin the real DCR/LSA/centerline numbers against regression. Generated **last**, after CODE1–3 land, so it captures the final output.

### WS-ENFORCE — Make the mechanism run without being asked (new files only)
**Owns:** `Makefile`, `.githooks/pre-push`, `src/cam_analyzer/py.typed` (new), `pyproject.toml` (package-data / dev-extra only).
- `make check` → `pytest && mypy && ruff check && lint-imports` (graceful if a tool is absent, but sets `CAM_ANALYZER_REQUIRE_MYPY=1`).
- `.githooks/pre-push` runs `make check`; document `git config core.hooksPath .githooks` in README (WS-DOCS cross-links).
- Ship `src/cam_analyzer/py.typed` so the unit/frame guarantee survives install.

### WS-DOCS — Reconcile docs with code + status-provenance ledger (docs only)
**Owns:** `README.md`, `ARCHITECTURE.md`, `docs/decisions/decision-log.md`, `docs/reference/ubiquitous-language.md`, `docs/rfc/0001-honest-typed-boundary.md`, `docs/explanation/domain-driven-design.md`, the round-1 `ROUND1_SYNTHESIS.md`, and a new `docs/decisions/adr-derivatives-operator-trusted.md` + new `docs/CLAIMS_LEDGER.md`.
- Demote D013 → `DESIGNED`; Pillar B → `ASSERTED` (+ ADR); RFC Pillar D → `DESIGNED`.
- Fix `ProvFloat`-as-`float`-subclass drift (glossary/D012/RFC) → `ProvFloat = Quantity[Any]`.
- Correct C3 wording: `measured()` is confined to the source layer **+ `analysis/safety.py`**; "unconstructable" now backed by the strengthened trap (cross-link WS-CODE2).
- Patch the fabricated frontier-model attribution in `ROUND1_SYNTHESIS.md` to match the retrospective.
- Add `docs/CLAIMS_LEDGER.md`: every decision/feature stamped `VERIFIED` (named test / `file:line` / CLI witness) · `ASSERTED` (doc only) · `DESIGNED` (not built). Remove/repair any HTML/PDF report claim in README (only Markdown exists).

---

## 3. Execution model

1. Commit this plan (done at the commit creating this file).
2. Fan out **WS-CODE1, WS-CODE2, WS-CODE3, WS-ENFORCE, WS-DOCS** in parallel (disjoint files).
3. Run **WS-CODE4** (golden) after the code agents land.
4. **Verification gate (the maintainer, not a producer):** run the full `make check` — `pytest`, `mypy --strict`, `ruff`, `lint-imports`, and the CLI end-to-end — and adversarially confirm each claimed deletion has zero remaining callers and each strengthened guard actually fails when violated. Nothing is called done on a producer's say-so.
5. Commit the executed changes; report VERIFIED/ASSERTED status honestly.

**Acceptance:** green `make check`; net source reduction (~300–450 LOC) with zero shipped-capability loss; every reconciled doc claim carries a build-status stamp; the strengthened C3 trap fails when a `_mint(...MEASURED...)` is injected outside the source layer; the golden `--reference` test pins the real numbers.
