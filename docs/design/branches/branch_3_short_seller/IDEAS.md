# Branch 3 — Divergent Ideation under frame: `short_seller`

author: diverger-reviewer-2-001

**Vantage.** For each idea: state the architecture's bull thesis in one sentence,
name the single assumption whose falsity voids it, then take the cheap position
against it *before consensus notices*. Generator mode — six distinct shorts, no
ranking, no hedging.

Banned obvious answers (not used below): "the interface will leak," "cam-card
inputs are inaccurate," "sparse → profile is mathematically underdetermined."

---

## Short 1 — The interface is over-sold as one width

**Bull thesis:** One `CamProfile` interface serves all eight analysis modules equally well.

**Voiding assumption:** Every consumer needs the same representation and resolution. It doesn't — DCR needs one scalar (lift near IVC), PTV needs the curve plus derivatives only inside the chase window, jerk analysis needs C³ continuity the cam-card source can never supply.

**Cheap short:** Ship a one-line method-usage decorator that logs which methods each module calls and at what crank resolution. The trace will show most consumers touch a sliver of the interface; the "universal interface" stops being a moat the day that log exists.

---

## Short 2 — "Swap without changing code" is not "swap without changing the verdict"

**Bull thesis:** You can replace an approximate profile with measured lift later without touching downstream analysis.

**Voiding assumption:** Downstream outputs vary continuously with the profile. PTV-contact and spring-float are cliff functions — a plausible measured curve flips a "safe" verdict to "contact" discontinuously, while the code stays byte-identical.

**Cheap short:** Precompute ∂verdict/∂profile at the cam-card profile and publish a single WR250R example where cam-card says PTV-safe and a realistic measured nose says interference. One counterexample retires the "seamless swap" story the project is implicitly selling.

---

## Short 3 — Confidence-as-a-tag is a lie that travels

**Bull thesis:** A confidence/quality tag on each profile lets users trust the right numbers.

**Voiding assumption:** Confidence is a property of the *profile*. It is a property of *each query at each crank angle* — a cam-card profile is near-certain at its four timing anchors and fabricated everywhere between, yet a profile-level tag reports a single "medium" across all of it.

**Cheap short:** Make `lift_at()` return value + local interval and plot the interval vs crank: ~0 at the anchors, enormous over the nose. The plot makes the scalar tag indefensible before anyone builds a UI around it.

---

## Short 4 — Milestone 1 is the disposable part, sold as the keystone

**Bull thesis:** "Cam card → CamProfile" is the safe, valuable first milestone.

**Voiding assumption:** The reconstruction math is the durable asset. It is the highest-churn code in the repo — deleted the moment real lift data arrives — while the source-independent kinematics core (crank-slider, valvetrain ratio, PTV sweep) is what actually survives.

**Cheap short:** Tag modules now and bet on deletion rate: `CamCardApproxProfile` math churns hardest over the project life. Position by funding the kinematics core and labeling the approximation explicitly as throwaway scaffolding, not a deliverable.

---

## Short 5 — CompositeProfile manufactures cam features that aren't there

**Bull thesis:** `CompositeProfile` blends measured and inferred regions seamlessly.

**Voiding assumption:** A blend seam can be made invisible to derivative-hungry consumers. The join injects a phantom acceleration/jerk spike, and the spring-safety module then "discovers" a float risk that is an interpolation artifact, not a cam property.

**Cheap short:** Feed CompositeProfile two identical halves with a deliberate seam and call `jerk_at()` across it. A spike on identical data proves the blend leaks artifacts straight into the safety analysis it was meant to serve.

---

## Short 6 — The real leak is conventions, not data sources

**Bull thesis:** Routing everything through `CamProfile` keeps cam-card assumptions out of analysis code.

**Voiding assumption:** Assumptions leak only through the data source. They leak through the silent convention contract the interface fixes — inches vs mm, crank vs cam degrees, lift-at-valve vs lift-at-lobe × rocker ratio, gross vs lash-subtracted, TDC reference — which every implementation must honor and none will document.

**Cheap short:** Run two implementations (cam-card in inches-at-valve, measured in mm-at-lobe) through the *same* downstream module and show the answers diverge by exactly the rocker ratio. The discrepancy is a silent frame bug the "clean" interface invited; the cheap hedge is a typed Quantity/Frame at the boundary now, before conventions calcify.
