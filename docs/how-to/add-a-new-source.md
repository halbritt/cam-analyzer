# How to add a new data source

> Stub. Fills in once `cam_analyzer.sources` has a second concrete source.

Goal: wire a new data source (e.g. Cam Doctor export, scanned lobe coordinates)
behind `CamProfile` so **no analysis code changes** (C4).

1. Add the source under `cam_analyzer/sources/<your_source>.py`. It may import
   anything it needs to parse its input (PDF, CSV, OCR). It must **not** be
   imported by anything under `cam_analyzer/analysis/` (C1).
2. Express the source as a `CanonicalLiftModel`: normalized 720° samples + exactly
   one named `LiftOperator` (D005). Do **not** implement the eight query methods —
   they are generated from the operator.
3. Stamp provenance honestly via a `ProvenanceMap` (D006): mark which crank regions
   are `MEASURED` vs `INFERRED` vs `EXTRAPOLATED`. There is no setter for "high
   confidence"; it is earned by measured support.
4. Add conformance traps for the failure modes specific to your source, and run
   the corpus: `pytest tests/`. Your source is "done" when it refuses every trap
   and the boundary guard stays green.

What you must never do: reach into your source type from an analysis module, or
return a bare `float`. Both are caught by `tests/test_architecture_boundary.py`.
