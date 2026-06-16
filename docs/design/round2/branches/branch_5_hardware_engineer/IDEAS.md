# Branch 5 — Divergence under frame `hardware_engineer`

> author: diverger-reviewer-1-002
> Workflow: `cam_profile_architecture_r2` · branch: `branch_5_hardware_engineer`
> Mode: **DIVERGENT** (generator, not critic). No evaluation, ranking, or hedging below.

**Transform applied (before ideating):** *Re-ask this as a hardware/firmware problem: what do bus topology, cache, and the timing budget tell you?*
**Vantage:** View the software profile boundary through the lens of hardware constraints (instruction-level verification, memory segregation, bus protocols, and real-time safety watchdogs) to enforce data integrity and handle cliff-function discontinuities.

---

## Checkable intermediate (what the transform produced)

### Kernel / invariant the design must hold

The data path (bus, cache, controller) must enforce data integrity (provenance) and system safety (verdict stability) as physical invariants, rather than relying on software conventions or developer vigilance.

### Restated problem

How can we design a `CamProfile` boundary that:
- Employs instruction-level hardware/firmware techniques (like parity, ECC, and bus arbitration) to prevent the silent "laundering" of inferred/untrusted floats without adding massive developer ergonomics overhead.
- Leverages cache coherency and watchdog paradigms to cleanly handle the discontinuous cliff-functions of safety verdicts (like valve contact) when the backing profile is hot-swapped.

### Trap inputs/scenarios the transform surfaced (each passes the letter, breaks the spirit)

- **T1 — The Silent Parity Stripper:** The analysis code reads a high-assurance float, performs math on it, and stores the result back as a plain float, dropping all provenance metadata. This is the equivalent of a bus line losing its parity bit, allowing corrupted or inferred data to masquerade as measured data.
- **T2 — The Cache Incoherency Seam:** Swapping a low-resolution inferred profile for a high-resolution measured profile updates the data source, but downstream safety analysis results (the cached verdicts) are not invalidated. The system continues to report "safe" based on stale, mismatched, or out-of-sync intermediate computations.
- **T3 — The Bus Bandwidth Overrun (Nyquist Violation):** A high-frequency analysis module (e.g., calculating 3rd-order jerk) queries a sparse cam-card profile. The backing profile is unable to supply the required high-frequency components, resulting in "bus noise" (unstable derivative approximations) that is treated as valid signal.
- **T4 — The Address Space Privilege Leak:** Analysis code can access any part of the profile space, including regions that were never measured (the seat ramps and nose), without declaring its security clearance/privilege level.
- **T5 — The Blind Spot Watchdog:** A cliff-function analysis (such as PTV clearance) runs on a single nominal profile, completely blind to the "voltage sag" (uncertainty/tolerance range) around that profile. A minor variance in the physical profile trips a physical collision (valve contact), but the system is unaware because there is no dual-core lockstep checking.

### Banned obvious answers — **NOT** used below

1. Caching computed profile queries in a standard software memory cache to optimize speed.
2. Using high-frequency DMA streaming to ingest data points from a physical sensor.
3. Setting CPU execution timeout limits on query calls to enforce real-time budgets.

---

## Six ideas (divergent)

### Idea 1 — Hardware-style Bus Parity & ECC (Error-Correcting Code) for Provenance
Reframe the `Quantity` value type as a hardware data word carrying "provenance parity bits" (e.g., `MEASURED`, `INFERRED`, `EXTRAPOLATED` as hardware states). Implement standard arithmetic operators on the `Quantity` class to act as hardware logic gates (e.g., `ANY + INFERRED = INFERRED`). If an operation attempts to strip the provenance bits (e.g., by coercing to a raw float) or combine incompatible frames, the runtime raises a simulated "bus parity error" (type-level or runtime exception). Standard operators (addition, multiplication, differentiation) propagate these parity bits transparently to avoid developer friction.

### Idea 2 — Cache-Line Invalidation and Coherency Protocol on Source Swap
Swapping a backing profile source (e.g., swapping a synthetic `CamCardApproxProfile` for a `MeasuredValveLiftProfile`) is treated as a physical DMA write that invalidates the system's "shared L1/L2 cache" (cached analysis intermediates). We introduce a formal cache-coherency controller: any computed analysis value must register its dependencies (crank-angle intervals and source ID) with the controller. When the profile source changes, the controller broadcasts a cache-invalidation signal to all registered consumers, forcing a recalculation and preventing stale or inconsistent verdicts from surviving.

### Idea 3 — Address-Space Segmentation via Memory Protection Unit (MPU)
Segment the `CamProfile` query space into distinct "virtual memory regions" corresponding to physical regions of the cam (e.g., `SEAT_RAMP_SEGMENT`, `NOSE_SEGMENT`, `FLANK_SEGMENT`) and their provenance. Analysis modules must establish a "privilege level" when opening a channel to the profile. If an analysis module attempts to read a segment containing `INFERRED` data while its privilege register is set to `MEASURED_ONLY`, the profile raises an MPU "segmentation fault" (or static type error), blocking access at the boundary.

### Idea 4 — Dual-Core Lockstep (DCLS) Execution with Perturbation Watchdog
To handle cliff-function discontinuities, run the analysis module in a simulated dual-core lockstep architecture. The "Primary Core" executes the analysis using the nominal (best-estimate) profile. The "Secondary Core" simultaneously executes the same analysis on a profile perturbed by the boundaries of its uncertainty distribution. If the output verdicts of the two cores mismatch (e.g., Primary says "safe", Secondary says "collision"), a "watchdog timer" trips, marking the entire calculation invalid and flagging the profile as unfit due to variance.

### Idea 5 — Bus-Negotiation Handshake & Nyquist Bandwidth Filter
Before executing queries, the analysis module (bus master) must perform a handshake with the profile (target device) to negotiate the "data rate" (required resolution and derivative order). The profile reviews its physical backing (sample density, measurement source). If the backing is too sparse to support the request (e.g., calculating jerk on a 5-point cam-card profile, which violates the Nyquist limit of the underlying sampling rate), the handshake fails at the protocol level, and the profile returns a "bus negotiation error" rather than emitting fabricated numbers.

### Idea 6 — Uncertainty Token-Bucket (Entropy Timing Budget)
Reframe the timing budget from execution time to an *entropy budget* (accumulated uncertainty). When an analysis module starts, it is allocated a token-bucket representing the maximum allowed uncertainty (entropy) it can tolerate. Every query to an inferred or extrapolated section of the profile consumes a token proportional to the query's variance. If the bucket runs dry before the analysis completes, the "precision watchdog" trips, terminating the execution with an "entropy limit exceeded" error, forcing the developer to provide a more precise (measured) profile.

---

### Distinct mechanisms (so the critic can see six, not one)

1. **Bus-level ECC:** Automatic, gate-level metadata propagation.
2. **Cache-Coherency:** Reactive, event-driven state invalidation.
3. **Address Segmentation:** Memory-protection access control.
4. **Lockstep Execution:** Parallel path difference detection.
5. **Bus-Negotiation:** Protocol-level capability filtering.
6. **Entropy Token-Bucket:** Resource-accounting error budget.
