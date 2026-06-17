# RFC 0003 — Piston-to-valve clearance model

- **Status:** Proposed (pre-decision). **Build status:** `DESIGNED` — nothing in
  this RFC exists in `src` yet. The current `evaluate_piston_to_valve`
  (`src/cam_analyzer/analysis/piston_to_valve.py`) has **no kinematic model**: it
  returns `UNDECIDABLE_FROM_CAM_CARD` unless handed a `measured_clearance`, and even
  then only computes `measured − threshold` — it *rubber-stamps a clay-check number*,
  it does not derive clearance from geometry.
- **Date:** 2026-06-17
- **Motivating decision:** an owner with a 13.5:1 piston (tall dome) + a longer-lift
  Web Cam grind needs to know whether the valves clear and, if not, **how deep to cut
  the valve reliefs** — see
  [`docs/explanation/dcr-report-wr250r-webcam-81-651.md`](../explanation/dcr-report-wr250r-webcam-81-651.md).
- **Relationship to RFC 0001 / 0002:** consumes the RFC-0001 typed `CamProfile` lift
  curves; shares the `CC`/`Mm` volume units with [RFC 0002](0002-static-cr-chamber-volume-solver.md)
  (a deeper relief adds clearance volume → feeds back into the CR solver).

---

## 1. Summary

P2V is the failure mode that bends valves and cracks pistons, and it is exactly
where this build is most exposed: a high-dome 13.5 piston *loses* clearance while a
bigger cam *demands* more. This RFC gives `piston_to_valve.py` a real
**static-kinematic** model: at each crank angle in the overlap window it computes
the vertical gap between the piston crown (with valve reliefs) and each valve, finds
the minimum and the angle it occurs, compares to the policy thresholds (≥0.050″
intake, ≥0.080″ exhaust), and **inverts** to the relief depth needed to make margin.

The result is honest by construction: its provenance is the **min-join of its
weakest input**. Fed a cam-card-`INFERRED` lift curve, the verdict is at best
`INFERRED` — a *screening estimate*, never a `MEASURED` PASS. **It does not replace
a clay check; it tells you whether you need one and roughly how much to cut.**

## 2. Motivation

The tool today can only say `UNDECIDABLE`, or echo a clearance you already measured.
Neither helps *before* you cut metal. The owner needs a pre-machining estimate:
- *Is the 13.5 dome + this cam even close to interference?*
- *If tight, how much relief depth buys the 0.050″/0.080″ minimum, plus margin?*

That estimate is computable from geometry the owner can measure on a bench (valve
head diameters, seat angle, deck height, current relief depth/diameter, installed
valve drop) plus the lift curves the profile already produces.

### Non-goals

- **Replacing the clay check.** The clay check is the `MEASURED` ground truth; this
  model is the `INFERRED` screen that decides whether/where to clay, and sizes the
  first cut. The RFC must never let a geometric estimate render as `MEASURED`.
- **Valvetrain dynamics.** This is a *static* kinematic model — valve position from
  the lift curve at each angle. Float, lash ramp, and rod/deck deflection at RPM are
  out of scope (they generally *reduce* clearance, so the static result is an
  optimistic bound — stated as a risk, §5).
- **Full 3D solid intersection.** A 1D vertical-gap model along the valve axis is the
  v1; circular-pocket/angled-valve corner cases are an explicit open question (§7).

## 3. Design

### 3.1 Kinematics

```
piston crown below deck at crank θ:
    s(θ) = (stroke/2)·(1−cosθ) + L − √(L² − (stroke/2)²·sin²θ)     # crank-slider drop from TDC
    crown_to_deck(θ) = deck_clearance + s(θ)                       # +reliefs handled per-valve below

valve tip below deck at θ (per valve, along bore axis):
    valve_drop(θ) = installed_drop − lift_at(θ)·cos(valve_angle)   # lift closes the gap

clearance_v(θ) = crown_to_deck(θ) + relief_depth_v − valve_drop(θ)
P2V_v = min over the overlap window of clearance_v(θ);  record argmin θ
```

Computed independently for intake and exhaust, over the overlap window (and a
configurable margin around it). The lift curves come straight from the profile
(`intake.lift_at` / `exhaust.lift_at`).

### 3.2 Install-timing sensitivity

P2V is sensitive to cam advance/retard (it shifts each lift curve vs TDC). The model
**sweeps the install range** (reusing the repo's install-sensitivity concept) and
reports the *worst-case* P2V across it — advancing the intake and retarding the
exhaust both pull their valves toward the piston near overlap.

### 3.3 The inverse (the actionable half)

```
required_relief_depth_v = max(0, (threshold_v + safety_margin) − P2V_v) + current_relief_depth_v
```

Returned as the existing `PistonToValveResult` extended with `min_clearance:
Quantity[Inch]`, `crank_angle_of_min: Angle[Crank]`, and `relief_cut_to_clear:
Quantity[Inch] | None`, or a `Refusal` when geometry is missing.

### 3.4 Seam in current code

`PistonToValveInput` grows an optional `geometry: PistonToValveGeometry` (valve
diameters, valve_angle, installed_drop, relief depth/diameter, deck_clearance).
`evaluate_piston_to_valve` branches:

1. `measured_clearance` present → today's behaviour (compare to threshold) — stays the
   `MEASURED` path (the clay check).
2. `geometry` present (no measured clearance) → **new kinematic estimate**, verdict
   provenance = min-join(lift-curve provenance, geometry provenance) → typically
   `INFERRED`; render distinguishes it from a measured PASS.
3. neither → today's `UNDECIDABLE_FROM_CAM_CARD` (unchanged).

So the cam-card-only path *stays* honest; the new model only activates when the user
supplies measured valve/deck geometry.

## 4. Enforcement plan (mechanism, not review)

> Build-status legend: **[DESIGNED]** = planned, not built. Nothing here is built.

- **[DESIGNED]** A known-geometry fixture with a hand-computed minimum clearance and
  argmin angle pins the kinematics (golden-style, like the DCR anchors).
- **[DESIGNED]** Provenance trap: a verdict produced from an `INFERRED` lift curve is
  **never** `MEASURED`/PASS-as-measured; `min-join` weakest-input is asserted.
- **[DESIGNED]** Refusal trap: `geometry=None and measured_clearance=None` still
  yields `UNDECIDABLE_FROM_CAM_CARD` (regression-guards the honesty the cam card has now).
- **[DESIGNED]** Inverse self-consistency: cutting `relief_cut_to_clear` and
  re-evaluating yields `min_clearance ≈ threshold + safety_margin`.

## 5. Risks & mitigations

- **Static model is optimistic.** Valve float and deflection at RPM eat clearance the
  static model doesn't see. *Mitigate:* mandatory non-zero `safety_margin`, and the
  result text states "static kinematic estimate — verify with a clay check at the
  intended install timing." This is a *safety-relevant* honesty requirement, not a nicety.
- **1D vertical gap misses angled-valve/pocket-edge contact.** *Mitigate:* v1 documents
  the assumption; flag builds where the valve head radius approaches the relief edge for
  a 3D follow-up (§7).
- **Laundering an estimate into confidence.** A geometric `INFERRED` number *looks*
  authoritative. *Mitigate:* the provenance min-join + the "not a clay check" render
  string are load-bearing, and the conformance trap enforces them.

## 6. Alternatives considered

- **Stay `UNDECIDABLE`, document the clay-check procedure only.** Honest but unhelpful
  before machining — leaves the owner with no pre-cut estimate. Rejected.
- **Import a CAD/solid model.** Accurate, wildly over-built for a hobby single. The 1D
  model with a measured-geometry interface gets ~90% of the decision value; the geometry
  struct leaves room to swap in a richer kernel later.

## 7. Open questions

- Vertical-gap vs along-valve-axis projection for steep valve angles — how much does
  `cos(valve_angle)` simplification cost on a ~12–15° DOHC included angle? Spike against
  one hand-computed 3D corner case.
- Should the install-timing sweep reuse RFC-0002's CR coupling (deeper relief → +Vc →
  lower CR) so a single "machining plan" reports *both* the new CR and the new P2V
  margin from one set of cuts?
- Does the clay-check `MEASURED` path want a first-class "record a clay measurement"
  CLI/card field so the screen→verify→confirm lifecycle is captured in one artifact?
