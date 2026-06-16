---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: deepener-reviewer-1-001

# Deepening Pick 2 — Derivative-Capability Matrix & Fitness Gating

## 1. Architectural Sketch

The derivative-capability matrix is implemented as a structured map on each `LiftOperator` that maps crank angle intervals to the maximum supported derivative order (e.g., lift=0, velocity=1, acceleration=2, jerk=3) that the backing data can physically and mathematically justify. Before the public `CamProfile` facade evaluates `velocity_at`, `acceleration_at`, or `jerk_at` at a given crank angle, it queries this matrix to verify if the backing operator supports the requested order in that specific region. If the check passes, the facade returns a `ProvFloat` carrying the numeric value and the region's provenance metadata. If the check fails, the query is formally refused, returning a structured `Refusal` object that details the resolution limits of the backing data and suggests what inputs would be required to resolve the query. This prevents downstream safety modules from consuming high-order derivatives that are mathematical fiction, such as smooth jerk curves derived from sparse, low-resolution cam cards.

```mermaid
graph TD
    Client[Client Code / Safety Module] -->|jerk_at crank_deg|
    Facade[CamProfile Facade] -->|Check capability| Matrix[Derivative Capability Matrix]
    Matrix -->|Order 3 NOT supported| Refuse[Return Refusal Object]
    Matrix -->|Order 3 supported| Evaluate[Delegate to LiftOperator]
    Evaluate -->|Compute jerk| Val[Return ProvFloat]
    Refuse --> Client
    Val --> Client
```

## 2. Load-Bearing Risk

The primary load-bearing risk is **premature over-restriction leading to developer bypass**. If the capability matrix is too rigid or difficult to configure, developers writing downstream analysis code (or users attempting quick sensitivity runs) will find the formal `Refusal` handling tedious. This friction could incentivize them to bypass the `CamProfile` facade entirely, write unchecked helper functions that strip the `Refusal` types, or falsely inflate the capability entries in the operator's matrix to silence compile-time or runtime errors. 

### Mitigation Strategies:
- Provide an explicit, grep-able, and lint-flagged `.approximate_anyway()` escape hatch on `Refusal` objects to allow prototyping while keeping the codebase searchable for integrity violations.
- Structure the `Refusal` object to return clear, actionable diagnostics, showing exactly what resolution of backing data would be required to unlock the requested analysis.

## 3. First Concrete Step

Define the core structures `DerivativeCapabilityMatrix` and `Refusal` in a new file, `capability.py`. Add the capability check protocol to the `LiftOperator` base class, implement a basic `HalfSineCamCardOperator` that publishes a matrix limiting capabilities to velocity (1st-order) only, and write a unit test verifying that querying `acceleration_at` on a facade wrapping this operator returns a `Refusal` while `velocity_at` succeeds.

```python
# docs/design/round2/deepened/deepen_2/capability.py (Conceptual implementation sketch)

from enum import IntEnum
from dataclasses import dataclass
from typing import Dict, Tuple, Union

class Provenance(IntEnum):
    EXTRAPOLATED = 1
    INFERRED = 2
    MEASURED = 3

@dataclass(frozen=True)
class Refusal:
    requested_order: int
    crank_deg: float
    max_supported_order: int
    reason: str
    remedy: str

@dataclass(frozen=True)
class ProvFloat:
    value: float
    provenance: Provenance

class DerivativeCapabilityMatrix:
    def __init__(self, intervals: Dict[Tuple[float, float], int]):
        # Map of (start_deg, end_deg) -> max_supported_order
        self.intervals = intervals

    def max_supported_order_at(self, crank_deg: float) -> int:
        normalized_deg = crank_deg % 720.0
        for (start, end), max_order in self.intervals.items():
            if start <= normalized_deg <= end:
                return max_order
        return 0 # Default to lift-only (0) if no interval matches
```

## 4. Child Ideas (Variations, Hybrids, Unlocks)

### Child Idea 1: Nyquist-Shannon Sampling Estimator
Instead of statically declaring the capability matrix, a discrete-data operator (e.g. reading from a CSV or dial-indicator log) dynamically calculates its own capability boundaries. By parsing local sample spacing ($\Delta\theta$) and executing a local Signal-to-Noise Ratio (SNR) estimation, the operator dynamically caps the maximum differentiable order. For instance, a degree-wheel dataset with $10^\circ$ increments is automatically capped at 1st-order (velocity) to prevent the amplification of measurement noise from generating fictitious acceleration spikes.

### Child Idea 2: Filter-Smoothed Fallback Operator
Introduce a fallback path where an operator exceeding its raw capability limit (due to noise in high-resolution data) can construct a smoothed derivative estimator (e.g. using a Savitzky-Golay filter or cubic smoothing spline). The operator returns a valid result, but the returned `ProvFloat`'s provenance is downgraded from `MEASURED` to `INFERRED`, carrying audit metadata that details the smoothing filter parameters applied to make the high-order derivative calculable.

### Child Idea 3: Cascade Batch Evaluator
Safety modules (such as spring dynamics calculators) often require evaluating multiple derivatives across a range of angles. To avoid handling nested `Refusal` objects for every single angle step, introduce a batch evaluator: `profile.evaluate_batch(orders=[1, 2, 3], angles=[...]) -> Union[BatchResult, Refusal]`. If any single query in the batch violates the capability matrix, the evaluator returns a single, consolidated `Refusal` outlining the weakest link in the data.

### Child Idea 4: Capability-Gated UI & Report Generation
Use the capability matrix to dynamically customize user-facing outputs. The report generator and graphical user interface can query the capability matrix of the loaded profile to automatically enable or disable specific analysis tabs (e.g. grey out "Valve Spring Float Analysis" if the active profile only supports up to 1st-order derivatives), replacing empty plots with a helpful guide on what data source is required to unlock them.
