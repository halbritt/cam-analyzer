# RFC 0002 — Static-CR ⇄ chamber-volume solver

- **Status:** Proposed (pre-decision). **Build status:** `DESIGNED` — nothing in
  this RFC exists in `src` yet. `grep -rn 'chamber\|clearance_volume\|dome_cc\|cc(' src` finds nothing.
- **Date:** 2026-06-17
- **Addresses:** [#17](https://github.com/halbritt/cam-analyzer/issues/17) (static CR is an
  untracked, unsourced, hardcoded input that bypasses the provenance lattice).
- **Motivating decision:** an owner holding a 13.5:1 piston needs to know *how much
  dome material to remove* to hit a survivable static CR — see
  [`docs/explanation/dcr-report-wr250r-webcam-81-651.md`](../explanation/dcr-report-wr250r-webcam-81-651.md).
- **Relationship to RFC 0001:** this is a *new analysis input provider*; it produces
  the `static_compression_ratio` that DCR consumes, as a sealed provenance-stamped
  `Quantity`, not a bare float. It depends on RFC 0001's sealed-mint + phantom-typed
  value layer being the home for the new volume quantities.

---

## 1. Summary

Today `static_compression_ratio` enters DCR as a bare `float` — hardcoded,
unsourced, and (in the fixture) wrong (issue #17). This RFC adds a small,
**measurement-driven** solver that *computes* static CR from chamber geometry and,
crucially, **inverts** it: given a target CR, it returns the clearance-volume delta
— i.e. **the dome material (in cc) to remove**. The CR it emits is a sealed
`Quantity` whose provenance is the min-join of its measured inputs, so DCR stops
trusting an untracked scalar.

It is pure closed-form geometry. It needs *bench measurements* (CC the head,
measure deck/gasket), not a cam card — and it must say so, never inventing a CR.

## 2. Motivation

Two pressures meet here:

1. **Architecture (issue #17).** The whole boundary exists to make a number's
   integrity legible. The DCR's most leveraged input has *none*. A CR computed from
   measured chamber volumes carries honest provenance; a hardcoded `12.8` does not.
2. **A real decision.** The owner's 13.5:1 piston is a fixed dome. The actionable
   question is the *inverse*: "to land at CR *X* on my fuel, how many cc of dome do
   I cut?" Nothing in the tool answers that — it only consumes a CR it is handed.

The spec already anticipated the inputs (`Camshaft_Analysis_Spec.md:44-51`:
`bore_mm`, `compression_ratio_static`, `deck_clearance_mm`, `gasket_bore_mm`,
`piston_dish_cc`) — this RFC turns those listed fields into a model.

### Non-goals

- **Detonation / "will it survive" verdict.** CR is an *input* to that question;
  this RFC does not judge fuel adequacy or knock margin. (See the report's caveats.)
- **Converting cc-of-dome to a single mill depth.** Removing *N* cc from a domed
  crown is not one flat-cut depth unless the dome's area profile is known; the
  honest deliverable is **target dome volume (cc)** and the **Δcc to remove**, with
  a clearly-labelled flat-deck-area *approximation* of mill depth as a convenience
  (`Δdepth ≈ Δcc / (π/4 · bore²)`), stamped `INFERRED`.
- **Piston-to-valve.** Orthogonal; that is RFC 0003. (They couple only weakly:
  deepening a valve relief adds a little clearance volume — the solver should accept
  a relief-cc term so the two analyses stay consistent.)

## 3. Design

### 3.1 The geometry (forward)

```
Vd  = (π/4) · bore² · stroke                     # swept volume per cylinder
Vc  = V_chamber + V_deck + V_gasket + V_dish − V_dome (+ V_relief)
       V_deck   = (π/4) · bore²        · deck_clearance     # crown-below-deck at TDC
       V_gasket = (π/4) · gasket_bore² · gasket_thickness
       V_dish, V_dome, V_relief: measured piston features (dish/relief add, dome subtracts)
CR  = (Vd + Vc) / Vc
```

`V_chamber` (head CC), `V_dish`/`V_dome`/`V_relief` (piston), and `deck_clearance`
are **measured**; bore/stroke/gasket are spec or measured. CR's provenance =
`Provenance.join(...)` over every input — so a CR built from one `INFERRED` guess
is itself at best `INFERRED`, and the DCR that consumes it descends accordingly.

### 3.2 The inverse (the actionable half)

```
target CR  →  Vc_target = Vd / (CR_target − 1)
           →  Δcc = Vc_target − Vc_current        # +Δ ⇒ remove that much dome
```

Returned as a `ChamberSolveResult { static_cr: Quantity, clearance_volume: Quantity[CC],
material_to_remove_cc: Quantity[CC], approx_mill_depth: Quantity[Mm] (INFERRED) }`,
or a `Refusal` when inputs are missing/insufficient (mirrors the DCR refusal style).

### 3.3 Worked example (this piston)

Vd = 249.60 cc. For this cam/engine:

| static CR | Vc | to reach from 13.5 |
|---|---|---|
| 13.5 (this piston) | 19.97 cc | — |
| 12.8 | 21.15 cc | remove **1.19 cc** of dome |
| 12.5 | 21.70 cc | remove **1.74 cc** of dome |
| 11.8 (stock) | 23.11 cc | remove **3.14 cc** of dome |

These are computed (see the report's CR-sensitivity table); the solver makes them
first-class, provenance-stamped, and driven by *your* measured chamber CC rather
than the assumed Vc above.

### 3.4 Placement & units

- New module `cam_analyzer/analysis/chamber.py` (an analysis; consumes no `CamProfile`).
- New unit tag `CC` (cm³) in the RFC-0001 phantom-typed `Quantity` family, plus the
  `(π/4)·bore²·h` volume helper. mm³↔cc is one explicit conversion.
- `DynamicCompressionInput.static_compression_ratio` migrates from `float` to
  `Quantity[Ratio]`; `analyze_dynamic_compression` min-joins it into the DCR
  provenance. **This is the concrete close-out of issue #17.**

## 4. Enforcement plan (mechanism, not review)

> Build-status legend: **[DESIGNED]** = planned, not built. Nothing here is built.

- **[DESIGNED]** Round-trip property test: `solve_cr(geometry).static_cr` then
  `solve_target(CR).material_to_remove_cc == 0` at the current CR (self-consistency).
- **[DESIGNED]** Provenance test: a CR built with any `INFERRED` input is not
  `MEASURED`, and `analyze_dynamic_compression`'s result provenance ≤ the CR's.
- **[DESIGNED]** A conformance trap: feeding the *cam card alone* (no chamber CC)
  yields a `Refusal`, never a fabricated CR — same honesty the cam-card path has.
- **[DESIGNED]** Golden update: once landed, the `--reference` fixture's bare `12.8`
  is replaced by a sourced CR (stock 11.8 *or* a labelled high-comp value), and the
  golden regenerated (closes #17).

## 5. Risks & mitigations

- **Garbage-in.** CR on a 250 is brutally sensitive to chamber CC: ±0.5 cc on a
  ~20 cc chamber swings CR by ~0.3. *Mitigate:* the result should carry the input
  it was most sensitive to, and the report should print the chamber CC it used —
  never a CR without its volumes (same disclosure rule #17 asks for).
- **cc→mill-depth over-trust.** The flat-deck-area depth is an approximation for a
  domed crown. *Mitigate:* stamp it `INFERRED`, label it "flat-cut equivalent", and
  keep the cc figure as the primary deliverable.
- **Scope creep into detonation.** *Mitigate:* hard non-goal; CR is an input, the
  survive/fuel verdict is out of scope (and arguably never a pure-geometry claim).

## 6. Alternatives considered

- **Keep CR a bare input, just source it in the fixture.** Cheapest; fixes the
  *symptom* of #17 (wrong number) but not the *disease* (untracked input, and no
  way to answer "how much to remove"). Rejected as half a fix.
- **Full 3D crown volume from a scanned dome mesh.** Most accurate, massive
  over-build for a single-cylinder hobby decision. Deferred; the cc-term interface
  leaves the door open to feed a measured dome cc from any source later.

## 7. Open questions

- Does `static_compression_ratio` become `Quantity[Ratio]` everywhere at once, or
  behind a `from_geometry()` constructor while the float path is deprecated? (Touches
  the golden test and the CLI card schema.)
- Should the CLI card JSON grow a `chamber: {head_cc, deck_clearance_mm, gasket_*,
  dome_cc}` block (compute CR) *in addition to* the literal `static_compression_ratio`
  (declare CR), with provenance distinguishing the two paths?
