---
author: diverger-reviewer-1-002
---

# Branch 2 - Remove Assumption Ideas

Vantage frame: remove_assumption

Thing treated as fixed: a single stable, synchronous, object-shaped `CamProfile` inside one application boundary.

1. Remove fixed object shape: make `CamProfile` a content-addressed profile document plus evaluator contract; analysis calls the contract while provenance, coefficients, samples, and confidence live beside it.
2. Remove single-truth profiles: let one `CamProfile` expose an ensemble of feasible lift curves - nominal, pessimistic PTV, spring-worst, and measured-only - under the same downstream interface.
3. Remove crank-angle-only thinking: represent lift as a family over crank angle, RPM, lash, temperature, and follower compliance; the cam-card milestone is just the default slice through that family.
4. Remove one-time import: keep cam cards, OCR text, dial readings, Cam Doctor rows, and lobe coordinates as live evidence nodes that can rederive `events_at_lift` instead of freezing imported numbers.
5. Remove request-response analysis: maintain an invalidation graph where source changes regenerate profile snapshots, timing maps, PTV windows, spring margins, and reports without an explicit calculator call.
6. Remove sidecar confidence: make quality a curve over crank angle and derivative order, so lift, velocity, acceleration, and jerk can carry different known/unknown regions through every analysis module.
