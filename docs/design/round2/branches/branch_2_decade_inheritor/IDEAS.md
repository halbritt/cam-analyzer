# Divergent Design Ideas: Vantage Frame (decade_inheritor)

**Frame Objective:** Keep the codebase maintainable and alive for ten years after the author quit, with no documentation, without cursing. Design for mechanical self-preservation and zero leakage of architectural boundaries.

Below are 6 short, distinct, non-obvious ideas for the `CamProfile` abstraction boundary.

---

## 1. Self-Enforcing Dependency Linting (AST Startup Audit)
Rather than relying on documentation warning future developers not to leak `CamCard` concepts into analysis modules, the test suite and package initialization statically audit the import graphs. 
- **Mechanism:** The initialization code parses the Abstract Syntax Tree (AST) of the project files. 
- **Enforcement:** If any file in `cam_analyzer/analysis/` imports a class, function, or constant from `cam_analyzer/parsers/` or references raw parsing models, the code raises a fatal exception at boot. This guarantees architectural boundary enforcement (C1) without human code review.

---

## 2. Zero-Laundering `ProvenancedFloat` (Arithmetic Propagation)
To combat the temptation of stripping metadata via `.magnitude` calls (which developers do for convenience), the core quantity types are backed by custom float subclasses (e.g., `ProvenancedFloat`).
- **Mechanism:** These floats override basic python dunder methods (`__add__`, `__mul__`, etc.) to automatically propagate the lowest level of confidence/provenance (`EXTRAPOLATED > INFERRED > MEASURED`) and raise errors on invalid unit/frame combinations.
- **Enforcement:** Downgrading or stripping the metadata requires explicit, ugly type-coercion (e.g., `float(val)`) which stands out clearly in diffs and is easily caught by simple regex tests in CI.

---

## 3. Adversarial Input Perturbation (Fuzzing Curve Assumptions)
Downstream analyses often bake in implicit assumptions about the shape of a camshaft profile (e.g., assuming it is perfectly symmetric, has a single local maximum, or peak lift is exactly at lobe center).
- **Mechanism:** During testing and debug mode, the profile registry automatically wraps profiles in a "PerturbedProfile" decorator. This decorator injects minor, mathematically valid noise, asymmetry, and micro-oscillations into the lift curves within the stated uncertainty bounds.
- **Enforcement:** If an analysis module assumes synthetic smoothness and breaks under realistic noise, the tests fail immediately, forcing the developer to write robust, source-agnostic math.

---

## 4. Living Diagnostic Error Bundles on Refusal
When a query is refused (e.g., trying to run PTV on a profile that lacks measured data), the system returns a detailed `Refusal` exception object.
- **Mechanism:** The exception contains a serialized Markdown/HTML diagnostics package. This package visually plots the missing/untrusted region of the curve, outlines what physical data source would resolve it (e.g., "Need Dial Indicator coordinates for valve-lift chaser zone"), and provides links to the code line where the requirement was defined.
- **Enforcement:** A maintainer ten years from now with zero mechanical domain knowledge can read the error payload and immediately know exactly what input data is required to make the analysis run.

---

## 5. Dual-Channel Parity Testing (Verdict Stability Shadowing)
Since safety verdicts (like PTV clearance or spring float) are discontinuous "cliff functions" of the profile shape, a developer swapping a curve fit ten years later might silently change a "Safe" verdict to "Unsafe" despite clean test runs.
- **Mechanism:** In testing/debug modes, the execution engine runs all calculations twice: once using the high-fidelity candidate profile and once using a boundary-case low-fidelity profile (e.g., a crude piecewise linear approximation).
- **Enforcement:** If the outputs differ significantly or cross safety thresholds between the two runs, the framework issues a loud "Verdict Instability Warning," highlighting that the safety margin is highly sensitive to the current profile's confidence level.

---

## 6. Refusal-First Type Definitions (Three-Valued Logic)
Instead of analysis code querying the profile and receiving raw numbers, the core APIs return a three-valued union type: `Value(T) | Refusal(Reason)`.
- **Mechanism:** The type system (via type hints and static pattern matching) forces any caller to explicitly unpack the result and handle the `Refusal` case.
- **Enforcement:** If a developer writes a new analysis module and neglects the `Refusal` flow, typecheckers like `mypy` flag it immediately. The code cannot compile or run without explicitly defining how it behaves when the profile says "I don't know."
