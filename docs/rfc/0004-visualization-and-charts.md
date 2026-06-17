# RFC 0004 — Visualization & chart suite (honest-by-construction)

- **Status:** Proposed (pre-decision). **Build status:** `DESIGNED` — nothing in
  this RFC exists in `src` yet. Today the only output is the Markdown report from
  `render_markdown_report` (`src/cam_analyzer/analysis/reporting.py`); there is no
  charting code, no SVG, no JSON export, and no web layer.
- **Date:** 2026-06-17
- **Motivating ask:** "make me some pretty charts like other cam and combustion
  analysis software… maybe it becomes a webapp at some point. Use the reference cam,
  which has extrapolated values. I'm okay with extrapolated values **as long as
  they're called out.**"
- **Relationship to RFC 0001 / 0002 / 0003:** charts are a *read-only projection* of
  the RFC-0001 typed `CamProfile` boundary and the `ProvenanceMap`. The
  piston-to-valve collision view (§3.2) is the visual surfacing of
  [RFC 0003](0003-piston-to-valve-clearance-model.md)'s kinematic model; the cut
  readout consumes RFC-0003's `relief_cut_to_clear` and RFC-0002's volume coupling.
  This RFC adds **no new physics** — it adds a *rendering* contract that is bound by
  the same honesty invariants as the numbers it draws.

---

## 1. Summary

Commercial cam/combustion software draws beautiful curves and, by drawing them
beautifully, makes a 5-point cam-card guess look like a measured fact. That is the
exact sin this project exists to refuse. So this RFC does **not** start with "which
charts." It starts with **how a chart is allowed to lie**, and forbids it.

The load-bearing deliverable is a **Provenance Rendering Grammar** (§3.1): one
reusable visual language — solid/dashed stroke, opacity, hatch, refuse-to-draw,
a quantified uncertainty band, a derivative-order ceiling, and an uncroppable
provenance footer — driven *mechanically* from the `ProvenanceMap`, so honesty is
structural, not per-chart decoration. Every chart in the suite is just that grammar
applied to a different projection.

On top of the grammar sit two tiers of charts:

- **Parity tier** (§3.2.A) — the charts a cam builder expects from
  Performance Trends / Lotus / COMP: the SVAJ stack, the 720° valve-lift overlay,
  the polar valve-timing clock, the cam-card panel, and a comparison overlay.
- **Differentiator tier** (§3.2.B) — two charts no bench analyzer draws, both
  flowing from this tool's honesty stance: the **piston-to-valve collision view**
  (gap vs crank angle, visibly fuzzy exactly where the lift is extrapolated) and the
  **"go measure THIS" overlay** (the tool ranks the single measurement that would
  collapse an `UNDECIDABLE` verdict into `PASS`/`FAIL`).

Rendering is **ECharts server-side SVG today, the identical spec interactive in a
browser tomorrow** (§3.3) — one codebase spans the CLI-now / webapp-later path the
ask leaves open.

On the reference cam (Web Cam 81-651, a sine-power fit to 5 numbers), the honest
result is blunt and is the whole point: most of every curve renders dashed, the
density gutter shows mostly-zero support, and **the fly-cut readout says
`UNDECIDABLE`, not a number** — because the minimum-clearance angle lands in the
extrapolated nose. The charts are pretty *and* they tell you they're mostly guessing.

## 2. Motivation

The tool can already *compute* honestly (provenance-stamped quantities, `UNDECIDABLE`
refusals). But its only face is a Markdown table. A cam builder thinks in curves:
the valve-lift overlay and the SVAJ stack are how the trade reads a profile, and the
owner's real question — *does the 13.5:1 dome clear the valves, and how much do I
cut?* — is a fundamentally *spatial* question that a table answers poorly.

Two forces make naive charting actively dangerous here, not just incomplete:

1. **A pretty curve launders extrapolation into apparent precision.** Five cam-card
   points fit across 720° produce a smooth, confident-looking curve whose nose and
   closed regions are pure model. A standard line chart erases the distinction the
   whole tool is built to preserve.
2. **Differentiation amplifies fiction.** Velocity/acceleration/jerk are derived from
   that fit; the accel and jerk panels are the *most* fabricated and, drawn normally,
   look the *most* authoritative. (Performance Trends' own manual warns errors are
   "magnified when velocity, acceleration, and jerk calculations are made.")

So the charts must encode, visibly and by construction, *what they don't know*. The
user's one hard constraint — "extrapolated values, as long as they're called out" —
is therefore not a styling note; it is the acceptance criterion.

### Non-goals

- **A combustion simulator.** PV loops, heat-release, CA50, knock, spark maps (the
  AVL/Kistler family) are out of scope until the tool *computes* cylinder pressure,
  which it does not. They are catalogued in §7 as a later projection, not built now.
  Drawing a combustion chart we can't populate would itself violate refuse-to-draw.
- **Replacing the clay check.** Per RFC 0003, the collision view is an `INFERRED`
  screen that tells you whether/where to clay — never a `MEASURED` go-ahead.
- **A full webapp.** This RFC builds the *rendering core* and static SVG output, and
  guarantees the spec is webapp-portable. The interactive app is gated behind a real
  trigger (§7), not built speculatively.
- **New physics.** Charts project existing quantities. Where a chart needs a number
  the tool doesn't have (e.g. deck geometry for the collision zero-point), that gap
  is RFC 0003's, and the chart must refuse rather than invent it.

## 3. Design

### 3.1 The Provenance Rendering Grammar (load-bearing)

One module owns the mapping from provenance to ink. Every chart consumes it; no chart
hand-styles a line.

**3.1.1 The style table.** A pure map from the existing 3-level enum (plus a reserved
refusal style) to a redundantly-coded style triplet:

| Provenance | Stroke | Opacity | Marker | Band fill |
|---|---|---|---|---|
| `MEASURED` (2) | solid | 1.0 | filled | none |
| `INFERRED` (1) | short-dash | ~0.70 | half-filled | light, no hatch |
| `EXTRAPOLATED` (0) | long-dash | ~0.45 | hollow | hatched, widening |
| `UNDECIDABLE` (refusal) | **no line** | — | — | cross-hatch + label "tool refuses to assert here" |

Redundancy is deliberate: every distinction is carried by **stroke dash *and* hatch**,
not color, so it survives grayscale print and color-blind viewing. Color (intake
blue, exhaust red/orange — the industry convention) is decoration layered *on top* of
the provenance encoding, never its sole carrier.

**3.1.2 Segment splitting (`split_series`).** The grammar's one core function walks
`ProvenanceMap.intervals()` and slices a continuous curve at provenance boundaries
into contiguous sub-series, each emitting its tag's style triplet as a separate
renderer mark. Honesty therefore lives in a *data-to-segment transform* with a single
tested home, and the ECharts vs Vega backends differ only in a thin adapter consuming
the same segment list:

```
samples + ProvenanceMap  ──split_series──▶  [StyledSegment]  ──adapter──▶  ECharts | Vega spec
```

`StyledSegment` is the renderer-agnostic IR: `(tag, x_range, y_samples,
band_halfwidth, is_undecidable)`. Both adapters render from it; a golden test asserts
they produce the *same* provenance encoding.

**3.1.3 Derivative-order ceiling, from data not hand.** The velocity/accel/jerk panels
render the map returned by `ProvenanceMap.derivative_map(order)` — which *already*
applies `Provenance.join(region, ceiling)` (1st derivative caps at `INFERRED`; 2nd+ at
`EXTRAPOLATED` unless the operator declares support). The panel's "max attainable
provenance: …" caption is read straight from `derived_map.weakest()`, and the optional
lift→jerk opacity decay is a pure function of order. A viewer therefore *cannot*
visually trust jerk as much as lift, because the stair-step cap is computed, never
typed.

**3.1.4 Refuse-to-draw.** Where the operator emits an explicit refusal sample (or the
prediction band exceeds a configured fraction of peak lift), `split_series` renders the
arc as the no-line cross-hatch band — it does **not** interpolate across the gap.
Absence of evidence becomes visible instead of being smoothed away.

**3.1.5 The evidence-density gutter.** A thin strip sharing the X-axis histograms how
many *real* cam-card points back each crank-angle bin. On the reference cam this is
mostly zero (5 points across 720°), so the eye is drawn to how thin the curve's
support actually is.

**3.1.6 The uncroppable provenance ledger.** A non-data footer band, baked into the
SSR template at fixed pixel rows, carries the **input cam-card hash**, the **fit-model
version**, and the per-tag legend. An exported or screenshotted image is therefore
self-authenticating: the caveat travels with the pixels and cannot be cropped off into
a clean-looking "fact" for a forum post or a warranty dispute.

**3.1.7 The quantified uncertainty band.** Extrapolated segments carry a band in
**real lift units** (mm/in), widening with angular distance from the nearest supported
point — not a dashed "vibe." This band's magnitude is the grammar's single hardest
dependency; see the risk in §5 and the band-math open question in §7.

### 3.2 The chart suite

#### 3.2.A Parity tier (what builders expect)

- **SVAJ stack** — four vertically-aligned panels (lift / velocity / acceleration /
  jerk) sharing one crank-angle X-axis, RPM-independent angle-based units
  (in, in/deg, in/deg², in/deg³). The accel panel shows the characteristic
  positive→negative→positive three-pulse shape (where the spring, not the cam, must
  reverse the valvetrain). Each panel obeys §3.1.3's ceiling, so the lower panels are
  visibly less-trusted.
- **Valve-lift overlay** — intake (blue) + exhaust (red/orange) over the full 720°
  cycle, 0° = TDC overlap, the overlap wedge shaded near TDC, with IVO/IVC/EVO/EVC,
  centerlines, and LSA annotated. The single most-recognized chart in the trade.
- **Polar valve-timing clock** — a circle (TDC top, BDC bottom, clockwise), the four
  events on the rim, overlap shaded as the top wedge. Notably *absent* from the
  commercial bench analyzers — a cheap differentiator — and here its event ticks carry
  provenance (hollow when extrapolated).
- **Cam-card panel** — the COMP/Web Cam tabular field set (advertised + @.050"
  duration, valve/lobe lift, LSA, centerlines, lash, IVO/IVC/EVO/EVC), dual inch/mm
  for motorcycle use, each cell tagged with its provenance.
- **Comparison overlay** — N cams on one axis (advance/retard one over a baseline,
  difference table). Each build carries its provenance pedigree forward so comparing
  two tunes is comparing two confidence levels, not just two curves.

#### 3.2.B Differentiator tier (honest-by-construction)

- **Piston-to-valve collision view** — the hero chart and the answer to the owner's
  real question. Plots `GAP(θ)` = piston-crown drop (crank-slider kinematics, already
  in `dynamic_compression._effective_stroke_from_closing`) − valve travel, through the
  overlap window, against the policy threshold line. Because `Quantity.__sub__`
  *already min-joins provenance*, the gap inherits the weakest stamp of its inputs at
  each θ for free — so the curve is solid where measured and a fattening band exactly
  over the extrapolated nose, which is precisely where the minimum lands. A single
  **cut readout** (`CLEARS by X″` / `CUT X″ REQUIRED` / `CUT ? — UNDECIDABLE`) and a
  **traffic-light bezel** that can go GREEN *only* when zero clearance-critical samples
  in the window are non-`MEASURED`. (Full kinematics: RFC 0003.)
- **"Go measure THIS" overlay** — the tool's signature move: instead of just printing
  `UNDECIDABLE`, it ranks the single real measurement (one dial-indicator reading at a
  named crank angle, or a clay squish) whose addition would most shrink the
  threshold-straddling band and decide the verdict — rendered as ranked wrench icons on
  a degree wheel with "dial indicator here, expect ~X thou, that decides it." Each
  fed-back reading becomes a new `MEASURED` region via
  `ProvenanceMap.from_default_and_regions`, collapsing the band locally and re-ranking
  the next best measurement. This converts the tool's most-common output
  (`UNDECIDABLE`) from a dead end into the most actionable thing on screen.

### 3.3 Rendering pipeline & tech stack

- **Library: Apache ECharts.** Since v5.3.0 it renders **zero-dependency server-side
  SVG strings** — no headless browser, no jsdom — via
  `echarts.init(null, null, {renderer:'svg', ssr:true, width, height})` →
  `chart.renderToSVGString()` (with `animation:false`). The *same* `setOption` spec
  runs interactively in a browser. This is the cleanest "static SVG now, interactive
  webapp later, one codebase" story of the candidates. **Vega-Lite** (declarative
  specs + `vl-convert`/`vl2svg`) is the documented fallback if a spec-driven approach
  is later preferred; the `StyledSegment` IR keeps us backend-portable either way.
- **A small TS/Node renderer package** consumes a JSON projection of the profile.
  Which means a prerequisite: the Python core must grow a **`--json` export** of
  quantities + provenance map (it has none today). The boundary is clean — Python
  computes and stamps; the renderer only draws what it's given and may not upgrade a
  provenance.
- **CLI surface:** `cam-analyze <card.json> --charts svg --out dir/` emits one SVG per
  chart; `--charts json` emits the projection for downstream/web use. Default stays the
  Markdown report (no behavior change unless a chart flag is passed).

### 3.4 Seam in current code

`reporting.py` gains a sibling `projection.py` that serializes the already-computed
`CamProfile` quantities + `ProvenanceMap` to the JSON contract. No analysis code
changes. The renderer lives outside `src/cam_analyzer` (a `viz/` TS package) so the
Python import-linter boundaries are untouched, and a chart can never reach *into* the
domain to recompute — it only consumes the projection.

### 3.5 Worked example — the reference cam (Web Cam 81-651, 13.5:1 build)

Intake 0.360″ / 262° adv / 238°@.050″ / CL 109.5°; exhaust 0.360″ / 270° / 246° /
CL 104.5°; LSA 107°; overlap@.050″ 28°. The lift curve is a sine-power fit to those
5 numbers, so:

- **Valve-lift overlay & SVAJ stack:** ramps render `INFERRED` (short-dash), the nose
  and closed regions `EXTRAPOLATED` (long-dash + widening hatched band); the jerk panel
  caption reads "max attainable provenance: EXTRAPOLATED" and is faded by the ceiling.
- **Density gutter:** near-zero across 720° — visibly five thin spikes.
- **Collision view & cut readout:** the minimum-clearance angle lands in the
  extrapolated nose → the readout is **`CUT ? — UNDECIDABLE (min clearance falls in
  EXTRAPOLATED region)`** and the bezel is locked AMBER. *This is the correct, honest
  output and a regression test pins it (§4).*
- **"Go measure THIS":** ranks the one dial-indicator reading over the nose that would
  let the collision view commit a number.

The charts are exactly the "pretty charts like other software" that were asked for —
and they simultaneously, unmissably, say *this is mostly a guess; here's the one
measurement that would change that.*

## 4. Enforcement plan (mechanism, not review)

> Build-status legend: **[DESIGNED]** = planned, not built. Nothing here is built.

- **[DESIGNED]** *Clean partition:* `split_series` over the reference map tiles the
  X-domain gaplessly, each segment's tag equals `prov_map.at(midpoint)`, and the
  segment count is bounded (the anti-confetti guard, §5).
- **[DESIGNED]** *Ceiling from data:* the accel/jerk caption text and opacity are
  computed from `derivative_map(order).weakest()`, never literals — including the
  saturation case where lift is already `EXTRAPOLATED` and velocity cannot step lower.
- **[DESIGNED]** *Refuse-to-draw needs a real signal:* an `UNDECIDABLE`/None sample
  (or band-over-threshold) produces the hatch band, asserted to *not* interpolate.
- **[DESIGNED]** *Crop survival:* render → crop to the plot area → assert the
  cam-card hash and legend still appear (ledger is structural, not optional).
- **[DESIGNED]** *Cross-backend identity:* the ECharts and Vega adapters produce the
  same provenance encoding from one `StyledSegment` list (golden SVG).
- **[DESIGNED]** *The honesty regression that matters most:* on the real 81-651 fit,
  the collision view's min-clearance θ resolves into an `EXTRAPOLATED` interval and the
  cut readout is therefore `UNDECIDABLE` — **not a number.** This test fails loudly the
  day someone "improves" the tool into fabricating a confident fly-cut from a 5-point
  card, which is the exact failure the project exists to prevent.

## 5. Risks & mitigations

- **Segment confetti.** If provenance flips rapidly (or `derivative_map` produces many
  tiny join-induced regions), `split_series` emits dozens of micro-segments and the
  dash language becomes illegible noise. *Mitigate:* a min-arc-width / max-segment-count
  guard that coalesces adjacent same-or-weaker segments (always coalescing *toward* the
  weaker tag, never the stronger), with an adversarial alternating-map test.
- **A fabricated uncertainty band is the same sin, relocated.** §3.1.7's band, and the
  measurement ranking that integrates over it, are *theater* if the half-width is a
  made-up constant — the tool would just move fabricated precision from the verdict into
  the band. *Mitigate:* derive the band from the sine-power fit's **leave-one-out
  residual** across its 5 points × angular distance from a supported point; stamp the
  band's own provenance; until that exists, the band is a labeled `DESIGNED` stub and
  the collision view stays `UNDECIDABLE` rather than drawing a fake band. (Open
  question §7.)
- **The collision zero-point sits on unstamped geometry.** Deck clearance, valve
  protrusion, and pocket depth are *not* on the cam card and *not* in the codebase. If
  they're hardcoded, the gap line draws a crisp `MEASURED`-looking curve whose zero is
  a fabrication. *Mitigate:* these are RFC-0003 `DeckGeometry` `Quantity`s that *refuse*
  to construct as `MEASURED` outside a measurements source; the gap's min-join then
  correctly degrades and trips `UNDECIDABLE`. The chart literally cannot draw a crisp
  zero-line from guessed geometry.
- **Gimmickry over legibility.** The diverge phase produced fun encodings (blur ∝
  uncertainty, "ink budget," sonification) that risk looking like rendering bugs.
  *Mitigate:* ship only the redundant, conventional, print-safe encodings in §3.1.1;
  the exotic ones are parked in §7 / the design appendix, not the v1.
- **Webapp scope creep.** "Maybe a webapp" can swallow the project. *Mitigate:* v1 is
  static SVG + the JSON projection only; the webapp is gated on a real trigger (§7) and
  inherits the identical specs for free.

## 6. Alternatives considered

- **matplotlib (Python-native, no JS).** Keeps everything in one language and renders
  static images fine — but it is a dead end for the webapp path (server-render only),
  so the interactive future would be a rewrite. Rejected for the stated webapp ambition;
  the ECharts spec serves both faces.
- **Hand-rolled SVG.** Zero deps, total control, trivially testable — viable only while
  the chart set is tiny, and it reimplements axes/scales/legends and yields no
  interactivity later. Reasonable bareback fallback if the JS dependency is unwanted;
  recorded, not chosen.
- **Plotly.js.** Feature-rich but window-dependent / effectively client-only — awkward
  for a CLI-first tool. Rejected.
- **Static-only (no provenance grammar, just dashed lines for the extrapolated tail).**
  The "obvious" answer. Rejected: it handles one chart's tail, not the per-region,
  per-derivative, refuse-to-draw reality of this data, and it doesn't survive the
  screenshot-laundering attack. The grammar is the point.

## 7. Open questions

- **Band math.** What exactly is the defensible per-angle uncertainty of a 5-point
  sine-power fit? Leave-one-out residual is the starting hypothesis; a spike should
  validate it against a denser measured lobe before the collision view is allowed to
  draw a band.
- **Webapp trigger.** What concretely promotes this from static SVG to an interactive
  app — the comparison-overlay workflow, or the "go measure THIS" feedback loop (which
  is most compelling when measurements collapse the fog live)? The interactive ideas
  from the design run (fog-of-war provenance meter, measurement "pins," the
  `UNDECIDABLE` "wall" that names its missing input, the timing-clock "seat the pins"
  mechanic) are the webapp's natural backlog.
- **Combustion projection.** The AVL/Kistler chart family (PV / log P–log V, heat
  release, CA10/50/90, MAPO knock, spark-advance map, multi-cycle overlay with COV of
  IMEP) is well-specified and ready to render *the day the tool computes cylinder
  pressure* — but drawing it before then violates refuse-to-draw. Tracked as the next
  RFC's territory, not this one's.
- **Animation.** A 720° valve+piston flipbook (measured frames inked, extrapolated
  frames faint) is a strong webapp asset; out of scope for static v1.
- **Sonification.** Mapping clearance-gap to pitch and provenance to timbre (a clean
  tone for measured, a detuned one for guessed) is a genuinely novel accessibility/alert
  layer — parked as a research provocation, not a v1 feature.

---

## Appendix A — Design provenance (ADHD divergence run, 2026-06-17)

This RFC was produced by a divergent-ideation run: 5 isolated cognitive frames
(regulator, hostile-competitor, midnight-builder, game-designer, 10-year-old) each
generated 6 ideas with no critic; the pool was then scored (novelty/viability/fit),
clustered by underlying angle, traps were pruned, and the top 3 distinct survivors
were deepened against the real code. The three deepened survivors became §3.1
(provenance grammar), §3.2.B collision view, and §3.2.B measurement plan.

**Clusters that shaped the design:** (A) provenance rendered into uncroppable ink;
(B) confidence encoded in the stroke itself + derivative ceiling; (C) show the
sparsity / refuse to draw; (D) quantify how wrong the guess could be; (E) answer the
real piston-vs-valve question; (F) turn refusal into a measurement plan; (G) the
interactive sandbox (→ webapp backlog, §7).

**Traps pruned (kept out of v1):** blur ∝ uncertainty (reads as a render bug);
literal "ink budget" (a principle, not a feature); a single global confidence meter
(flattens the per-region truth the data carries); the physical/sensory metaphors —
wax-lobe, shadow-puppet, sand-tray, xylophone (mined for the *encoding insight*
"guessed = visibly unstable," then discarded as literal features). Sonification and
animation survive only as §7 provocations.
