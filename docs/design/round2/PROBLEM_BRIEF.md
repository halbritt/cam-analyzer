author: problem-framer-author-001

# Round 2 Problem Brief

## Open Question

Given that `CamProfile` should be the durable boundary between source-specific cam data and analysis modules, how should the application make provenance-preserving profile use the easiest path while staying honest when uncertain profile details can flip safety verdicts?

## Context

The first milestone is cam card input to generated `CamProfile`. It is not cam card input to dynamic compression ratio, piston-to-valve clearance, or any other downstream analysis result. The architecture must start from the Yamaha WR250R Web Cam 81-651 cam card while remaining replaceable by measured valve-lift curves, Cam Doctor exports, scanned lobe profiles, and later valvetrain-dynamics models.

Round 1 settled the broad skeleton: downstream modules consume only `CamProfile`; profile values carry unit, frame, provenance, and quality; one canonical representation generates query results; and confidence or fitness is local to the crank region, query, and derivative order rather than a single global tag.

## Constraints

- Analysis modules must not depend on `CamCard`, PDF parsing, CSV import, OCR, Cam Doctor formats, lobe coordinate files, or other source-specific structures.
- Sparse cam-card approximations must be distinguishable from measured data at every profile query result that can affect an analysis decision.
- Query results for lift, velocity, acceleration, jerk, events, duration, max lift, and area must preserve enough metadata for consumers and reports to explain what is known, inferred, extrapolated, or unsupported.
- Safety-related analyses, especially piston-to-valve clearance and valve spring behavior, must not treat weak or fabricated high-order profile detail as equivalent to measured evidence.
- The design must account for discontinuous verdicts: replacing an approximate profile with measured data may change a result from safe to unsafe without any downstream code change.
- Any eventual composite or stitched profile must not hide derivative discontinuities that would create false acceleration or jerk conclusions.
- Milestone 1 should remain small enough to build and test from cam-card data, while preserving a credible path to measured profiles.

## Goals

- Frame the guarantees that `CamProfile` must provide before implementation details are chosen.
- Identify how ergonomics can protect integrity: the normal analysis path should retain provenance and quality metadata instead of encouraging bare numeric shortcuts.
- Define how analysis consumers should recognize when a profile is insufficient for a question, especially for safety margins and high-order derivatives.
- Preserve source replaceability without implying verdict stability.
- Make the boundary testable through adversarial examples that catch source leakage, metadata stripping, frame/unit mistakes, and overconfident inferred values.
- Ensure reports can communicate confidence, data gaps, and source sensitivity clearly enough for practical camshaft decisions.

## Non-Goals

- Do not choose a concrete package structure, class hierarchy, interpolation method, storage format, or parser implementation in this round.
- Do not design the dynamic compression, piston-to-valve, spring, report, or sensitivity modules in detail.
- Do not optimize for full valvetrain dynamics before the cam-card-to-profile milestone exists.
- Do not promise that measured data can replace inferred data without changing analysis outcomes.
- Do not reduce provenance or confidence to a single file-level or profile-level label.

## Decision Criteria

A successful round-2 proposal should be judged by whether it:

- keeps source-specific assumptions out of downstream analysis code;
- makes metadata-preserving profile operations easier than metadata-stripping numeric shortcuts;
- represents measured, inferred, extrapolated, and unsupported profile regions without ambiguity;
- prevents insufficient evidence from being silently interpreted as a safe result;
- remains practical for the first cam-card milestone;
- can evolve to measured lift and richer valvetrain data without breaking the `CamProfile` boundary;
- gives tests and reports enough hooks to expose the important failure modes.