author: diverger-author-001

# Branch 4: Short Seller

1. Bull thesis: A provenance-carrying `CamProfile` makes honest analysis the default once downstream code consumes only profile queries. Voiding assumption: consumers can get the scalar they want without first proving query fitness. Cheap bet: make every safety-facing call return `Answer | Refusal` and ban `lift_at()` from clearance/spring modules.

2. Bull thesis: One canonical operator prevents cam-card assumptions from leaking into analysis implementations. Voiding assumption: the operator's generated derivatives are numerically trustworthy enough to survive report screenshots. Cheap bet: require every operator to publish a derivative capability matrix before `velocity_at`, `acceleration_at`, or `jerk_at` can answer.

3. Bull thesis: Per-region provenance maps tell the truth about measured, inferred, and extrapolated zones. Voiding assumption: crank-angle intervals are the right shape for every uncertainty source. Cheap bet: add event-local provenance around openings, closings, nose, and lash take-up instead of only continuous angle bands.

4. Bull thesis: Replacing an approximate profile with measured data leaves analysis code unchanged while improving truth. Voiding assumption: "unchanged code" is the property users actually need when verdicts flip. Cheap bet: persist paired approximate-vs-measured verdict deltas as first-class report sections, not debug comparisons.

5. Bull thesis: The honest path can be made more ergonomic than bare floats with typed quantities and generated projections. Voiding assumption: ergonomics lives inside the Python API. Cheap bet: generate notebook, CLI, and report APIs from the same query schema so there is no lower-friction side door for demos.

6. Bull thesis: A conformance corpus can freeze the abstraction boundary and catch future source leakage. Voiding assumption: static traps catch failures that arise from plausible but wrong curves. Cheap bet: add adversarial curve families that preserve published cam-card events while moving area, nose shape, or jerk across safety thresholds.