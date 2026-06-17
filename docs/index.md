# cam-analyzer documentation index

Every doc, one line each. Diátaxis layout: explanation (why), reference (what),
how-to (task), tutorials (learning).

## Start here
- [`../README.md`](../README.md) — what cam-analyzer is and the CamProfile boundary.
- [`../ARCHITECTURE.md`](../ARCHITECTURE.md) — the navigable map: layers, pillars, boundary contract.

## Explanation (why it is this way)
- [`explanation/domain-driven-design.md`](explanation/domain-driven-design.md) — what is load-bearing; bounded context, aggregate roots, value objects.
- [`explanation/dcr-report-wr250r-webcam-81-651.md`](explanation/dcr-report-wr250r-webcam-81-651.md) — a published `cam-analyze --reference` run: DCR ≈ 11.272 (INFERRED), with PTV/spring UNDECIDABLE by design.

## Reference (what it is, precisely)
- [`reference/ubiquitous-language.md`](reference/ubiquitous-language.md) — the canonical glossary; code must agree with it.
- [`reference/spec.md`](reference/spec.md) — pointer to the product boundary and the reference cam-card numbers.

## Decisions (the boundary, and why)
- [`decisions/decision-log.md`](decisions/decision-log.md) — the architecture decision record (ADR table).

## RFCs (proposed designs, pre-decision)
- [`rfc/0001-honest-typed-boundary.md`](rfc/0001-honest-typed-boundary.md) — make C3/C6 mechanism-not-convention: sealed mints + phantom-typed units/frames + ergonomic inversion (resolves the round-2 "ergonomics-as-integrity" problem; addresses #5/#6/#8).

## How-to (tasks) — stubs
- [`how-to/add-a-new-source.md`](how-to/add-a-new-source.md) — wire a new data source behind CamProfile without touching analysis.

## Tutorials (learning) — stubs
- [`tutorials/cam-card-to-profile.md`](tutorials/cam-card-to-profile.md) — Milestone 1: a cam card in, a CamProfile out.

## Design provenance (how the architecture was produced)
- [`design/PROBLEM_BRIEF.md`](design/PROBLEM_BRIEF.md) — the framed question and the C1–C6 invariants.
- [`design/ROUND1_SYNTHESIS.md`](design/ROUND1_SYNTHESIS.md) — the round-1 pillars (A/B/C + D) and traps.
- [`design/branches/`](design/branches/) — the five divergence branches.
- [`operator/`](operator/) — the striatum workflow definitions and operator decisions.
