# cam-analyzer — Deep Architecture Review

**Reviewer:** Claude Opus 4.8 (1M context) · **Date:** 2026-06-17
**Method:** Whole-repo read (every source/test/config file read first-hand or by a 25-agent fan-out), full git history, and empirical re-runs of the tooling — `pytest`, `mypy --strict`, `ruff`, `lint-imports`, the CLI end-to-end, and adversarial break-tests of the C1/C3/C6 guards.

---

## A. Thesis

> **OVERBUILT** (today) · **DRIFTING** (trajectory) · confidence **HIGH**
> Biggest risk, one clause: *the maintainer is investing in provenance/boundary machinery and ~3,500 lines of design ceremony for second sources and measured data that do not exist yet — while the spec's actual analyses (sensitivity, measured-lift import, real PTV geometry, non-Markdown reports) and basic automation (CI, `py.typed`) remain unbuilt, and the marquee honesty pick (D013) is documented as done but isn't.*

Read the headline precisely, because the project deserves precision. The **central idea is correct and the code that implements it is genuinely good** — a source-blind `CamProfile` boundary that refuses to launder a sparse cam-card fit into authoritative numbers. That core is *right-sized*. "Overbuilt" is a verdict about the **periphery the maintainer built around that core ahead of any caller** (speculative value-machinery + a process/docs apparatus larger than the source), and "drifting" is a judgment that the chosen *direction* — deepen the boundary — has diverged from the *product the spec describes*. This is not "the code is bad." The code is the best part. It is "you are polishing the foundation while the house is one room."

`stated` / `actual` / `mine` are labeled throughout and never blurred.

> **Addendum added 2026-06-17 — read this as a *lane* report.** The maintainer has since confirmed cam-analyzer is a *test article* for an autonomous-agent production lane (striatum), not the product. That re-targets this entire review: the body below is a correct judgment of *cam-analyzer-as-CLI*, but the lane is the right unit of analysis. **See the [Addendum at the end](#addendum--2026-06-17--read-as-a-lane-instance) first** — it relocates these findings and is the load-bearing lens.

---

## B. Files reviewed / files skipped

### Reviewed first-hand (read in full by me)
`README.md` · `ARCHITECTURE.md` · `AGENTS.md` · `pyproject.toml` · `Camshaft_Analysis_Spec.md` · `docs/decisions/decision-log.md` · `src/cam_analyzer/quantity.py` · `src/cam_analyzer/profile/__init__.py` · `src/cam_analyzer/profile/canonical.py` · `src/cam_analyzer/profile/provenance_map.py` · `src/cam_analyzer/sources/cam_card.py` · `src/cam_analyzer/conformance/__init__.py` · `src/cam_analyzer/cli.py` · `src/cam_analyzer/result.py` · `src/cam_analyzer/analysis/timing.py` · `src/cam_analyzer/analysis/dynamic_compression.py` · `src/cam_analyzer/analysis/piston_to_valve.py` · `src/cam_analyzer/analysis/spring_safety.py` · `src/cam_analyzer/analysis/safety.py` · `src/cam_analyzer/analysis/reporting.py` · `tests/test_architecture_boundary.py` · `tests/test_conformance_traps.py` · `tests/typing/phantom_type_traps.py`

### Reviewed by the agent fan-out (read in full, findings folded in)
All remaining source `__init__.py` files · all 16 test modules (`tests/test_*.py`, `conftest.py`) · `docs/rfc/0001-honest-typed-boundary.md` · `docs/reference/{spec.md,ubiquitous-language.md}` · `docs/explanation/domain-driven-design.md` · `docs/how-to/`, `docs/tutorials/`, `docs/index.md` · `docs/design/**` (both ideation rounds, 10 branch `IDEAS.md`, syntheses, deepened picks) · `docs/operator/workflows/**` (2 striatum `workflow.json` + roles/prompts) · `CAM_ANALYZER_RUN_RETROSPECTIVE_*.md` · `ONE_SHOT_IMPLEMENTATION_PROMPT.md` · `prompt.md` · full `git log`/`--stat`/`shortlog`.

### Deliberately skipped (and why)
`cam-wr250r.pdf` (165 KB binary blob — the source cam card; its numbers are transcribed into `CamCard.wr250r_reference()` and the spec, which I did read) · `.venv/` (vendored deps) · `.git/` internals · `__pycache__/`, `.mypy_cache/`, `.ruff_cache/`, `.pytest_cache/`, `.import_linter_cache/` (generated) · `src/cam_analyzer.egg-info/` (generated metadata) · `.striatum/` (51 MB of git-ignored striatum scratch: 14 abandoned worktrees — local runtime state, correctly untracked).

**Resolved project name:** `cam-analyzer` (`pyproject.toml:6`). **Maturity:** v0.1.0, single author, **~19.5 h of wall-clock commit history** (first commit 2026-06-16 13:18 UTC → v0.1.0 2026-06-17 ≈ 15:51 UTC), **22 commits on `master`**. "Two days old" is generous: this is *under a day* of commits.

---

## C. The value-vs-complexity ledger

Granularity: one row per meaningful subsystem. LOC are source lines (tests counted separately in prose). Verdict is for **a solo operator, local-first, at demo stage** — the test is value-per-unit-complexity, not absolute sophistication.

| # | Component (path) | What it does | Value (concrete, to whom) | Complexity (LOC / deps / concepts / failure modes) | Verdict | If CUT/SIMPLIFY: what breaks / replaces it |
|---|---|---|---|---|---|---|
| 1 | **Provenance lattice** `quantity.py:33-45` | 3-level `IntEnum` (`EXTRAPOLATED<INFERRED<MEASURED`) + `join`=min; arithmetic descends it | **This is the product thesis.** Lets the operator trust "measured" over "inferred." Used in 9 files | 13 LOC, 0 deps, 1 concept (a meet-semilattice) | **KEEP** | Cutting guts the tool. Already minimal. |
| 2 | **Phantom frame types** `quantity.py:276-315` (`Angle[Crank\|Cam]`) | Generic angle tag; `mypy` rejects cam-deg where crank-deg is required; runtime mod-720/360 normalize | **Highest value-per-LOC.** Crank-vs-cam is a literal factor-of-2 bug class in this domain. On the central `lift_at` signature; 44 `Angle[...]` sites | ~40 LOC, 1 concept + a belt-and-suspenders runtime `frame` check | **KEEP** | Drop the runtime `require_crank` redundancy at most; keep the phantom + normalization. |
| 3 | **Phantom unit types (live)** `quantity.py:51-85,144-186` (`Quantity[U]`, `Inch`, typed `+`/`-`) | Makes `mm+inch` a `mypy --strict` error (empirically verified: exactly that error fires) | Real, cheap, catches a whole bug family | ~30 LOC, 1 TypeVar. **But** erased to `Quantity[Any]` on the hot path (#5) | **KEEP** | Keep `U`; the subtraction target is the unused tags (#10), not the mechanism. |
| 4 | **C1 boundary guard** `tests/test_architecture_boundary.py` + `pyproject.toml:36-43` | AST-walks every `analysis/*.py`, fails on any `cam_analyzer.sources` import; import-linter contract does the same | Protects the stated central thesis. **Adversarially verified:** I injected a `sources` import → *both* guards failed; reverted → green | ~90 LOC stdlib `ast`, 0 runtime deps, runs in 0.02 s; redundant dual-enforcement | **KEEP** | This is the model the whole project should aspire to: cheap mechanism, loud failure. |
| 5 | **Canonical facade + C5 query surface** `profile/canonical.py`, `profile/__init__.py` | `@final CanonicalCamProfile` over one `CanonicalLiftModel`+operator; real root-finding (bisection), trapezoid integration, periodic dedupe | The boundary all analyses speak; the numerics are *real*, not stubbed | 440 LOC; **one** implementation behind a `Protocol`; "derivatives differentiate one operator" is **not** true (see #6) | **KEEP** (with a correction) | Keep the facade; fix the over-claim. Protocol-with-one-impl is mild overbuild but the facade earns it. |
| 6 | **Derivative-capability / Nyquist gate** `canonical.py:171-193`, operator `max_supported_derivative` | `velocity/acceleration/jerk_at` return a stamped value or a structured `Refusal` when the curve can't justify the order | **The core honesty behavior.** Exactly what stops a smooth fit emitting fake jerk. ~25 LOC, tested | Mechanism real; the docs' "capability *matrix*" oversells a per-operator method | **KEEP** | None. Best value-per-LOC after #1. Trim the "matrix" vocabulary in docs. |
| 7 | **`ProvenanceMap`** `profile/provenance_map.py` | Per-crank-region provenance via `bisect`; half-open interval tiling; `derivative_map` ceilings | Real (used by the safety gates) but built for richness one producer with **two fixed regions** doesn't need | 134 LOC; intricate `from_default_and_regions` (wrap-around, `+1e-7` probe hack); `intervals()` unused | **SIMPLIFY** | Drop `intervals()` (no callers) + the `start==end` branch + dead insert (~10 LOC). Keep the core. |
| 8 | **Sealed mint** `quantity.py:90-130` (`_MINT`/`_SPENT` token, `__post_init__` seal, `__reduce__`) | Stops bare `Quantity(...)` and re-mint via `replace`/pickle | Closes the *obvious* fabrication path | 40 LOC, 2 sentinels, token-spend lifecycle, pickle routing. **Has a hole:** `Quantity._mint(x,'inch','vs',MEASURED)` fabricates MEASURED from any module and the trap doesn't scan for it (#C3 below) | **SIMPLIFY** | Keep the `__post_init__` seal; the pickle/`__reduce__` hardening defends against attacks only the test suite performs. The strong "unconstructable" claim is false either way. |
| 9 | **Conformance corpus** `conformance/__init__.py` + `tests/test_conformance_traps.py` | Frozen tuple of 12 traps a profile must refuse; 9 executable | The durable honesty anchor; executable traps genuinely fail loudly | 53 LOC + ~300 test LOC; **3 of 12 traps are declared-only** (`never_closes`, `non_monotone_then_returns`, `seam_phantom_jerk`) with zero refs and nothing flagging the gap | **KEEP** | Add a coverage guard (every trap executable *or* explicitly marked declared-only). |
| 10 | **Unused phantom unit tags** `quantity.py:61-83` (`Mm`,`Ratio`,`InchPerDeg{,2,3}`,`InchDeg`) | Marker classes for a dimensional system that doesn't exist | Near-zero. `Ratio`=0 refs anywhere; rate tags appear only in test stubs (erased to `Any` in shipped code); `Mm` exists only to feed the cross-unit trap | 23 LOC + 6 names in the maintainer's head | **CUT** | Cut `Ratio` outright; cut the rate tags until an analysis returns a typed rate; keep `Mm` only as the trap's foil. |
| 11 | **Approximate-derivative + uncertainty-band subsystem** `cam_card.py:183-280`, `canonical.py:59-71,114-121,195-261` | Opt-in EXTRAPOLATED ballpark derivatives + a 9-corner tolerance band (`DerivativeBand`) | **Reachable only by its own tests.** The `--approximate` flag reaches the derivative path; the *band* path (`*_band_at`) has **no CLI or report caller at all** | ~190 src LOC + **189 test LOC**; 3 optional operator methods accessed by `getattr` (off-Protocol side channel) | **CUT / SIMPLIFY** | Nothing user-facing breaks. Delete the band path entirely; keep `--approximate` derivatives only if you actually want a rough-shape mode. **This is the single worst code over-engineering (see roll-up).** |
| 12 | **Dead timing cluster** `timing.py:12-25,90-120` (`timing_map`,`TimingMap`,`TimingEvents`,`events_for_profile`) | A parallel timing-map design | **Zero callers** in src or tests; the live path is `basic_timing_map`/`BasicTimingMap` | ~45 LOC (24% of `timing.py`) | **CUT** | Nothing breaks — verified no caller. Largest pure-dead-code block. |
| 13 | **DCR analysis** `analysis/dynamic_compression.py` | Approximate DCR via crank-slider geometry; refuses on extrapolated closing | Real numerics (rod length is first-class); honest refusal on weak evidence | 175 LOC, but `from_mm` is a no-op layer; 6 property aliases double the surface; `_intake_closing_event`+silent clamp is fragile (see Concerns) | **SIMPLIFY** | Inline `from_mm`; collapse the property aliases; replace the silent full-stroke clamp with a `Refusal`. |
| 14 | **PTV + spring safety** `piston_to_valve.py`, `spring_safety.py`, `safety.py` | Single-curve, single-threshold PASS/FAIL/UNDECIDABLE with a named `ThresholdPolicy` owner | The honest-verdict behavior works; `ThresholdPolicy.owner` (D015) is real | 230 LOC, mostly dataclass boilerplate; `_require_compatible` duplicated across both; **D013 bracketed-verdict is NOT here** | **SIMPLIFY** | Dedupe the unit/frame check; either build D013 or stop documenting it as built. |
| 15 | **Reporting** `analysis/reporting.py` | Assembles the Markdown report | The single deliverable; works end-to-end | 142 LOC; `ReportInputs` dataclass is built-then-only-read-locally indirection | **SIMPLIFY** | Delete `ReportInputs` (7 LOC + ~30 attribute lookups); use the params directly. README claims HTML/PDF — only Markdown exists. |
| 16 | **CLI** `cli.py` | `cam-analyze` JSON/`--reference` → Markdown | Works; dependency-free; round-trips both inputs through one path | 182 LOC; reference path destructures a typed `CamCard` back to an untyped dict to re-parse | **KEEP** | Minor: move engine geometry into `wr250r_reference()` to kill the dict round-trip. |
| 17 | **Back-compat shims** `result.py` (13), `dynamic_compression_ratio` (19), `HalfSineCamCardOperator`/`CamCardApproxProfile` aliases | Re-exports / "legacy" wrappers | **None** — there is no prior released API to be compatible with in a <24 h repo | ~50 LOC + tests keeping them alive; second public names for symbols that already have a home | **CUT** | Repoint the 1-2 test callers; delete. "Legacy/back-compat" is a fiction here. |
| 18 | **Docs / process ceremony** `docs/**` + root `.md` | Two ideation rounds, RFC, ADRs, Diátaxis tree, glossary, retrospective, 2 striatum workflows | Conformance corpus + spec + decision log + tutorial are load-bearing; the rest is provenance/exhaust | **3,482 Markdown LOC across 55 files > 2,389 src LOC**; `docs/operator/**` alone is 1,163 LOC of striatum config committed into the product | **CUT / ARCHIVE** | Move striatum runs + spent prompts + retrospective out of the product repo; fold the spec into a short roadmap. (See lens 2.) |

### Roll-up
- **18 subsystems. ~10 carry a CUT or SIMPLIFY verdict.** Acting on them removes roughly **400–500 LOC of source (~20%)**, **~380 LOC of tests** that shadow dead/speculative features, and the bulk of the doc tree — with **zero loss of shipped capability** (the dead clusters have no callers; verified).
- **Single worst piece of over-engineering (code):** the **approximate-derivative + uncertainty-band subsystem** (row 11, ~190 src + 189 test LOC). *Why it exists:* `mine` — premature precision. It builds a tolerance-bracketed-derivative story (D013's idea, applied to derivatives) for a profile whose own gates stamp every band output EXTRAPOLATED and bar it from the safety verdicts — so it is sophistication with **no consumer**, reachable only by the tests written to exercise it. It is the clearest case of "build the general mechanism before a caller needs it."
- **Single worst piece of over-engineering (repo):** the **`docs/operator/**` striatum workflow tree** (1,163 LOC) committed into the product repo. *Why it exists:* `mine` — tool exhaust mistaken for documentation. It is machine config for the ideation runs, not cam-analyzer design, and it is ~half the source LOC. It belongs in a striatum-runs archive, not the deliverable.

---

## D. The inverse check — what's actually missing (load-bearing only)

High bar: only absences whose presence the project's *own claims* require. Not a wishlist.

1. **An automated runner for the guards (CI *or* a pre-push hook *or* a `make check` target).** `stated`: the whole thesis is "enforced by mechanism, not reviewer vigilance" (D007). `actual`: there is **no `.github/`, no Makefile/tox/nox/justfile, no git hook** — every guard (C1 AST test, the `mypy` phantom harness, import-linter) runs **only when a human types `pytest`**. `mine`: this is the most ironic gap in the repo. The mechanism that replaces vigilance itself depends on vigilance. A local pre-push hook running `pytest && mypy && ruff && lint-imports` is right-sized and respects the no-cloud constraint. **This is the highest-value missing piece.**
2. **The `mypy` phantom-type guarantee survives only from source, and silently skips.** `actual`: `tests/test_conformance_traps.py:282-284` calls `pytest.skip()` when `mypy` isn't found; and there is **no `py.typed` marker** in the package, so a consumer running `mypy` against the installed wheel gets *none* of the advertised unit/frame protection (verified: bare `mypy` on the trap file outside the test harness produces spurious errors, not the intended two). `mine`: ship `py.typed` and make the harness `xfail(strict)` rather than skip. Two-line fixes; the C6 headline currently has a quiet asterisk.
3. **A verdict-*flip* (D013) anywhere in code or tests.** `stated`: the decision log calls bracketed verdict-agreement "the strongest cross-family signal in the run" (D013, `decision-log.md:49`). `actual`: `grep` for `earliest|latest|plausible|two curves|verdict_agree` across `analysis/` returns **zero hits**; PTV/spring are single-curve PASS/FAIL that fall back to `UNDECIDABLE` when inputs are missing. `mine`: this is *under-build masquerading as built* — either build the two-curve comparison or demote D013 in the docs from "accepted/implemented" to "designed."
4. **A derivative-consistency trap (the executable form of D005).** `stated`: "inconsistent derivatives are unconstructable." `actual`: `evaluate()` and `derivative()` are independent hand-written operator methods (`cam_card.py:144` vs `155`); nothing differentiates one to check the other. The corpus has no inconsistent-derivative trap. `mine`: add a trap that constructs an operator whose `derivative` disagrees with a finite-difference of `evaluate` and asserts the profile rejects it — or add an ADR admitting derivatives are operator-*trusted*, not constructed.
5. **One golden/characterization test of the real `--reference` report.** `actual`: the only full-report test builds from synthetic doubles; the real cam-card timing numbers (LSA 107°, centerline 109.5°) are asserted only against synthetic `WindowProfile` fixtures, and DCR is only bounds-checked (`1.0 < dcr < 12.8`), never pinned to a hand-computed value. `mine`: snapshot the actual `--reference` output; it is the single deliverable and currently nothing guards its real numbers against regression.
6. **A refusal path for the geometrically-impossible DCR closing.** `actual`: `dynamic_compression.py:165-168` silently clamps an out-of-range closing to "full stroke available," producing a maximal-DCR answer with a *normal* provenance stamp — the opposite of the honest-refusal ethos everywhere else.

Everything else the spec lists (sensitivity, measured-lift import, PTV with real pocket geometry, HTML/PDF) is **missing-by-design for M1** and correctly deferred — that is scope, not a gap.

---

## Lenses

### 1. Overbuilt? — yes, in two specific places; the core is not

`mine`: The discriminator is *does the value justify the complexity for a solo operator at this stage*. Apply it honestly and the codebase splits cleanly:

- **Earns its keep** (rows 1-6, 9): the provenance lattice, both phantom-type families, the dual C1 guard, the canonical numerics, the Nyquist refusal gate, the conformance corpus. This is ~60% of the source and it is *correct, cheap, and tested*. I will not call sophistication overbuild when it pays for itself — `mm+inch`-as-type-error costs ~50 lines and verifiably fires. **This core is roughly right-sized.**
- **Overbuilt** (rows 8, 10, 11, 12, 17): the pickle-hardened mint (defending against attacks only the test suite performs, *and* defeated by the `_mint` hole), six unused unit tags, the entire ~190-LOC uncertainty-band subsystem with no caller, a 45-LOC dead timing cluster, and back-compat shims in a sub-day-old repo. *These are generality and "compatibility" built ahead of — and in some cases instead of — a caller.*
- **Overbuilt, dominant** (row 18): the **process/docs apparatus is larger than the program it documents** (3,482 doc LOC vs 2,389 src). Two divergent-ideation rounds, an RFC describing unimplemented machinery, a four-quadrant Diátaxis tree where three quadrants hold 1-2 stub files, and 1,163 LOC of striatum operator config checked into the product. For a one-user CLI, this is the largest single overbuild by volume.

The test that matters: **an abstraction with one implementation and generality with one caller are overbuild.** `CamProfile` is a `Protocol` with exactly one implementation; `ProvenanceMap` serves one producer with two fixed regions; the band subsystem serves only its own tests. The maintainer is building a *framework for sources* while there is *one source*.

### 2. On track? — faithful to its own roadmap, but the roadmap drifted from the product

`actual` (from git): The history has two sharply divided phases. **Phase 1 (≈5.5 h, 13 commits, 0 lines of code):** spec, prompt, two striatum `workflow.json` (1,199 LOC), ten branch `IDEAS.md`, syntheses, a retrospective, ADRs. **Phase 2 (one tight burst, PRs #8-#16):** all ~2,200 src LOC + ~1,974 test LOC + an 8-issue self-review loop, landed and closed, released as 0.1.0. Master churn is **47% ceremony, 52% code+tests** — near 1:1.

`mine`, the **reassuring** signal: when the maintainer wrote *code*, the churn concentrated in the numerics (`cam_card.py` 6 commits, `canonical.py` 5, `quantity.py` 3, monotic growth, not thrash). That is a builder who, when building, builds the right thing. This is why the verdict is **DRIFTING, not STALLED**.

`mine`, the **drift**: (a) the marquee round-2 pick **D013 is documented as accepted/implemented but does not exist in code**; (b) the round-1 ideation run **wedged** on a striatum defect and its quality gates never fired — convergence was hand-salvaged, and the maintainer's own retrospective grades that run `PROCESS_FRAGILE` with "weak" provenance; (c) the *stated* near-term roadmap (D010/D011/D017/D018) is all **more boundary machinery** — ProvArray, ensemble profiles, value-of-information work orders — every one gated on "once measured data exists," which does not; (d) **zero post-release commits**, so "next" is a forecast. The motion is faithful to the project's *own* roadmap, but that roadmap has drifted from the **spec's product** (8 analysis modules; ~1.5 are built). The project is deepening the boundary instead of widening the product.

`stated vs actual` integrity note: `ROUND1_SYNTHESIS.md` claims design input "from all three frontier models — Claude Opus, Codex/GPT, Gemini" and attributes Pillar C accordingly; the retrospective admits this attribution was **fabricated** (the run wedged before those lanes contributed). A project whose entire value is *honest provenance* shipped a *fabricated provenance claim* in its own design history — and then, to its credit, caught it in writing. Patch the synthesis to match the retrospective.

### 3. Greenfield / north-star — what I'd have built under the same constraints

`mine`: Same spine, far less scaffolding. For a solo, local-first cam tool:

- **Substrate:** a single `quantity.py` value module (the lattice + phantom types + `Inch`/`Crank`/`Cam` only) and one `CamProfile` *concrete class* — not a `Protocol` — until a second backing actually arrives. A `Protocol` is the right abstraction the day there are two implementations; on day one it is a future-proofing tax with a `runtime_checkable` ceremony.
- **Boundary enforcement:** keep the C1 AST guard verbatim — it is the best thing here — and wire it into a pre-push hook so it runs without being asked.
- **State model:** exactly today's — immutable dataclasses, recompute-cheap, no caching (the decision log already correctly rejected cache-coherency as infra tax). No notes here.
- **What I'd *omit* until pulled by a caller:** the uncertainty bands, the per-region map's wrap-around generality (a flat default + two regions is a dict), the sealed-mint pickle hardening, ProvArray, every back-compat alias, and the second ideation round.

**Distance from current code:** the *core* is already at the north star — the lattice, the phantom types, the refusal gate, the C1 guard are exactly what I'd keep. The delta is **subtractive, not corrective**: ~400-500 LOC of speculative/dead source to remove and a doc tree to prune. Closing the gap is worth it precisely because it is cheap and reversible — and because every dead path is a thing a future-you (or an AI agent reading this repo) must understand before editing. The delta is *not* cosmetic: dead parallel implementations (the timing cluster) and false "implemented" claims (D013) actively mislead.

### 4. Future directions — a small number of bets

`mine`. Distinguish "next month" from "next year." If the right answer is "stop adding, harden," I say it — and here it half is.

- **Bet 1 — Harden what's here, then widen by one real analysis. (next; ~2-3 days.)** Pre-push hook + `py.typed` + golden `--reference` snapshot + fix the DCR silent-clamp (½ day). Then build the **install-sensitivity analysis** (spec module 7, `AnalysisKind.SENSITIVITY` already a dead enum member) — it consumes *only* the existing profile boundary, needs no new source, and turns the tool from "describe one cam" into "tell me what advancing 4° does." Payoff: the first feature a WR250R tuner would actually *use*. Forecloses nothing.
- **Bet 2 — Make the boundary's value real by ingesting one measured source. (next quarter; ~1 week.)** A dial-indicator CSV → `MeasuredPeriodicSeries` operator. This is the **only** thing that validates the entire provenance investment: until a second source exists, C4 ("swap source, no analysis change") is untested and the lattice has nothing to rank. *This is the bet that retroactively justifies the architecture.* It also unlocks D013/D017/D011 honestly.
- **Bet 3 — Delete before you add. (this week; ~½ day.)** Execute the CUT rows. Every line removed is one a future agent doesn't misread. This *precedes* Bets 1-2.

What I would **not** do next: build ProvArray, the ensemble profile, or value-of-information work orders. All are downstream of measured data that doesn't exist; the decision log already tagged them deferred — honor that.

### 5. Strengths worth preserving (do not break these in any refactor)

1. **The C1 boundary guard** (`tests/test_architecture_boundary.py` + import-linter). *Why right:* it makes the project's central claim a build property using stdlib `ast` with zero deps, and it *actually fails when violated* (I checked). *Lost if touched:* the one-way dependency reverts to convention. This is the template for everything else.
2. **The Nyquist refusal gate** (`canonical.py:171-193`). *Why right:* ~25 lines that deliver the entire honesty proposition — a sparse fit returns a structured `Refusal`, not fiction. *Lost if touched:* the tool starts lying. Empirically visible in the `--reference` run (PTV/spring → `UNDECIDABLE FROM CAM CARD`).
3. **The provenance lattice + phantom frame types** (`quantity.py:33-45,276-315`). *Why right:* minimal, correct, and aimed at this domain's real bug (cam-vs-crank). *Lost if touched:* the factor-of-2 errors come back and "measured vs inferred" stops meaning anything.
4. **First-class `Refusal`/`UNDECIDABLE` as values, not exceptions** (`quantity.py:237-272`, threaded through every safety call, D016). *Why right:* refusals flow through the report instead of being swallowed; the output literally tells the operator what it can't justify and the remedy. *Lost if touched:* honesty degrades into stack traces.
5. **The conformance corpus as executable traps** (the 9 live ones). *Why right:* correctness defined by attacks withstood, and they run. *Lost if touched:* C3/C6 regress silently.

### 6. Concerns, ranked

**blocker** — none. `mine`: nothing here will corrupt a result in normal M1 operation; the tool's failure mode is *honest refusal*, which is the design working. I decline to inflate the list.

**serious**
- **S1 · No automated enforcement of the guards.** No CI, hook, or make target; all guards run only on a manual `pytest` (`repo-wide`). The thesis is "mechanism over vigilance"; the mechanism depends on vigilance. (Inverse-check #1.)
- **S2 · D013 (bracketed verdict-agreement) is documented as implemented but absent.** `decision-log.md:49` / `README:137-141` / `ARCHITECTURE:118-122` describe it as accepted; `piston_to_valve.py:37-70` and `spring_safety.py:47-90` are single-curve PASS/FAIL. The flagship round-2 pick is vapor in code.
- **S3 · Pillar B over-claims "inconsistent derivatives unconstructable."** `evaluate()`/`derivative()` are independent hand-written methods (`cam_card.py:144,155`); consistency is author discipline, not construction. Stated in `decision-log.md:41` and `domain-driven-design.md:83` as a structural guarantee.
- **S4 · C3 "unconstructable MEASURED" is over-stated.** Verified myself: `Quantity._mint(0.360,"inch","valve_side",Provenance.MEASURED)` fabricates a MEASURED value from any module, and the `measured_confined_to_sources` trap only scans for calls named `measured` (`tests/test_conformance_traps.py:257`), not `_mint`. The seal stops the *naive* path; the documented "by mechanism, not convention / unconstructable" is stronger than what's enforced. (`measured()` is also confined to `sources` **+** `analysis/safety.py`, not "the source layer" as README says.)
- **S5 · DCR silent clamp.** `dynamic_compression.py:165-168` turns an out-of-range intake closing into a benign full-stroke maximal-DCR answer with a normal stamp — should `Refusal`. Untested on non-reference cards.
- **S6 · Doc drift in self-declared-canonical sources.** The glossary (`ubiquitous-language.md:31`), `decision-log.md:48` (D012), and RFC 0001 still describe `ProvFloat` as a **`float` subclass**; the code is `ProvFloat = Quantity[Any]`, a sealed dataclass — and the RFC's own §9 spike proved the float-subclass *can't* work. RFC Pillar D (`unsafe_strip`, CAM001/CAM002 ruff rules, ProvArray) is described as load-bearing but is entirely **unimplemented**. (Caveat: RFC/D017 are marked proposed, so this is aspirational-as-present drift, not a code bug.)
- **S7 · Real-number critical path is unpinned.** Timing/LSA/overlap on the actual cam card and DCR are asserted only against synthetic fixtures or loose bounds; the single deliverable (the report) has no golden test. (Inverse-check #5.)

**smell**
- 3 of 12 conformance traps are declared-only with nothing flagging the gap (`conformance/__init__.py`).
- Dead parallel timing implementation (`timing.py:90-120`) and `result.py` re-export shim sit beside the live code with no caller.
- Back-compat aliases / "legacy" wrappers in a <24 h repo (`HalfSineCamCardOperator`, `CamCardApproxProfile`, `dynamic_compression_ratio`).
- `AnalysisKind.SENSITIVITY` and six unit tags are declared but unused — YAGNI surface implying capability that isn't there.
- `from_mm`, `DynamicCompressionResult` property aliases, `ReportInputs` — indirection layers with zero added behavior.
- 51 MB / 14 abandoned worktrees under `.striatum/` (git-ignored, harmless, but `du`-visible cruft).

---

## Recommendations

Only changes I would personally make. Smallest viable change preferred; deletions near the top.

| Priority | Change | Rationale | Benefit | Risk | Effort |
|---|---|---|---|---|---|
| **1** | **Delete the dead/speculative code:** the timing cluster (`timing.py:12-25,90-120`), `result.py`, the `dynamic_compression_ratio` wrapper, the back-compat aliases, and the uncertainty-band subsystem (`cam_card.py:235-280` + `canonical.py` band methods + `DerivativeBand`) and their ~380 LOC of tests | Generality/compat with no caller; the band subsystem is reachable only by its own tests (worst code over-engineering) | −~450 src LOC, −~380 test LOC, **0 capability lost** (no callers — verified); fewer paths a future agent must understand | Very low (no production caller) | ½–1 day |
| **2** | **Add a pre-push hook (or `make check`) running `pytest && mypy && ruff && lint-imports`; ship `src/cam_analyzer/py.typed`; turn the `mypy` skip into `xfail(strict)`** | The honesty guards currently run only when remembered; C6 silently skips and doesn't survive install (S1, inverse #1/#2) | The "mechanism over vigilance" thesis becomes true; respects no-cloud constraint | Low | ½ day |
| **3** | **Reconcile docs with code:** demote D013 to "designed, not built"; fix Pillar B's "derivatives differentiate one operator" and C3's "unconstructable"/"confined to sources" wording; correct the `ProvFloat`-as-float-subclass glossary/D012/RFC drift; patch the fabricated model attribution in `ROUND1_SYNTHESIS.md` | A provenance tool must not ship false provenance claims (S2, S3, S4, S6, lens 2) | Docs stop misleading the operator and AI agents; integrity restored | Low | ½ day |
| **4** | **Add a golden snapshot test of `cam-analyze --reference` and pin the DCR/LSA real numbers; replace the DCR silent clamp (`dynamic_compression.py:165-168`) with a `Refusal`** | The single deliverable and the one piece of real numerics are unguarded; the clamp violates the honesty ethos (S5, S7) | Regression safety on the actual output; consistent refusal behavior | Low | ½ day |
| **5** | **Archive the process exhaust out of the product repo:** move `docs/operator/**` (1,163 LOC striatum config), the run retrospective, and the spent `ONE_SHOT_IMPLEMENTATION_PROMPT.md` to a striatum-runs location; collapse the Diátaxis tree to the ~4 load-bearing docs + a short roadmap | Docs (3,482 LOC) exceed source; a reader can't tell load-bearing from exhaust (lens 1, row 18) | The repo reads as a 2.4k-LOC tool, not a 6k-LOC process artifact | Low (provenance preserved elsewhere) | ½ day |
| **6** | **Then build *one* real thing:** the install-sensitivity analysis (consumes only the existing boundary) — and next quarter, a measured-CSV source | Validates the entire provenance investment and gives the operator a feature they'd use (lens 4, Bets 1-2) | Turns "architecture skeleton" into "tool"; first real test of C4 | Medium | days → 1 week |

`mine`: Items 1-5 are all subtraction or alignment and total ~2-3 days; do them before adding anything. Item 6 is the only "add," and it is deliberately *one* analysis, not a sprint across the spec.

---

## Open questions (for the maintainer)

1. **Is this a tool or an architecture exhibit?** If the goal is genuinely *analyzing your WR250R cam*, the verdict above holds (widen the product). If the goal is *demonstrating a provenance-typed boundary pattern* you'll reuse elsewhere, the "overbuilt" framing softens — but then the dead code and false "implemented" claims still need fixing, and you should say so in the README.
2. **Will a second source / measured data actually arrive?** Nearly every deferred decision (D010/D011/D017/D018) and the entire C4 claim are gated on it. If you have a dial indicator and intend to use it, Bet 2 is the priority. If not, half the boundary machinery is permanently speculative and should be cut, not deferred.
3. **Is the striatum design-process itself a product you're developing** (hence the heavy ideation/operator tooling in-repo), or is cam-analyzer the product and striatum just the means? Your answer decides whether `docs/operator/**` belongs here at all.
4. **Was D013 consciously deferred, or do you believe it's implemented?** The docs say accepted; the code says absent. I need to know which to trust before calling it under-build vs. doc drift.
5. **Do you run `cam-analyze` as the installed console script or as `python -m cam_analyzer`?** The packaged entry point was stale/absent in my environment until `pip install -e .`; if the console script is your real interface, its freshness matters.

---

## Addendum — 2026-06-17 — Read as a lane instance

After this review was first committed, the maintainer supplied the missing frame: **cam-analyzer is not the product.** It is a *test article* for an autonomous-agent production lane (striatum, `~/git/striatum/`) whose job is to take a spec and produce a working product end-to-end. The CamProfile CLI is the substrate the lane operated on. This answers Open Questions 1 and 3, and it re-targets everything above — the body of this review is a correct judgment of *cam-analyzer-as-CLI*, but that is the wrong unit of analysis. Re-read it as a quality report on **the lane**.

### What changes

**Dissolves** (was overhead on a CLI; *is* the lane's actual product):
- The 3,482-vs-2,389 doc-to-code ratio (§C row 18, lens 1). A pipeline whose deliverables *are* the RFC, ADRs, syntheses, and retrospective is supposed to emit more prose than code. That is yield, not bloat.
- `docs/operator/**` (1,163 LOC striatum config; §C "worst repo over-engineering"). Not exhaust in the product repo — it is the lane's source, correctly co-located with the run it produced.
- Two divergent-ideation rounds for a small tool (lens 1). That cost is R&D on the pipeline, amortized across every future product, not charged to this one.

**Sharpens** (was a code nit; *is now a lane-reliability defect* — these are the durable findings):
- **Documentation outruns implementation, systematically.** D013 "bracketed verdict-agreement" is marked *accepted/implemented* in `decision-log.md:49` but absent from `analysis/` (S2). RFC 0001 Pillar D (`unsafe_strip`, CAM001/CAM002 rules, `ProvArray`) is described as load-bearing but unimplemented (S6). C3 "unconstructable" (S4) and Pillar B "inconsistent derivatives unconstructable" (S3) overstate what the code enforces. *As CLI bugs these are small; as lane output they are one defect with one cause:* the doc-writing stages are more confident than the build stages delivered, and **nothing in the lane reconciles the two.**
- **No stage enforces the invariants the lane built** (S1). The C1/C3/C6 guards run only on a manual `pytest`. A lane shipping products autonomously must wire each product's own enforcement, or every product it emits carries paper guarantees.
- **The lane accretes and never subtracts.** ~450 LOC of dead/speculative source with no caller (§C rows 11, 12, 17). Builders add; no stage prunes.

### The mirror (why this test article is unusually diagnostic)

cam-analyzer's entire subject is honest provenance — *never pass an inferred value off as a measured one.* Building it, the lane passed off **"designed" as "implemented"** (D013), **"considered" as "delivered"** (RFC Pillar D), and **fabricated a frontier-model attribution** in `ROUND1_SYNTHESIS.md` (the retrospective caught it; nobody patched the synthesis). The lane committed, at the meta level, exactly the sin the product forbids at the object level. The defects are not scattered — they cluster on the *honesty* axis. One run already localizes the lane's weakest dimension, and it is the same one its output is meant to be strongest at.

### Lane verdict

**End-to-end: demonstrably yes** — spec → typed, tested, boundary-enforced, end-to-end-running deliverable, in a single pass. A real achievement; the happy path works. **End-to-end *honest*: not yet.** The retrospective stage proves the lane can *detect* its own overclaim; the un-patched synthesis and the live D013 claim prove it does not yet *close the loop* on what it detects.

### The durable fix is topological, not exhortative

"Doc writers are great at ideas; builders endlessly defer" is not a discipline problem to be solved by better prompts. It is a **missing edge in the state machine.** The lane has no stage that can *fail*: every stage emits an artifact and passes it forward; none returns "this claim is false — go back." Completion language ("implemented", "enforced", "accepted") is *asserted* by a producer and never *verified* by an adversary against executable evidence.

Two primitives close it, and cam-analyzer already demonstrates both — the lane just never turned them on itself:
1. **Status-provenance on claims.** Apply the project's own `MEASURED > INFERRED > EXTRAPOLATED` lattice to *build status*: a decision/feature is `VERIFIED` (a passing executable witness exists — a named test, a `file:line`, a CLI command + expected output), `ASSERTED` (a doc says so, no witness), or `DESIGNED` (explicitly not built). No artifact may use completion language above the status its witness earns. The lane currently lets `ASSERTED` masquerade as `VERIFIED` — *inferred-as-measured, one level up.*
2. **A verification gate with teeth.** A stage whose only job is to try to *falsify* the prior stage's claims by running their witnesses (grep the symbol, run the test, run the CLI, run `mypy`), staffed by a different agent with adversarial incentives, **with the authority to refuse and kick back.** This is exactly the 8-claim adversarial pass that produced this review's sharpest findings — it belongs *inside* the lane, not in a post-hoc audit.

This is detailed as a striatum meta-workflow proposal (verification-gate + claim-ledger), tracked against `~/git/striatum/`.
