# Project Instructions

cam-analyzer is a Python camshaft analysis toolkit built around one
load-bearing boundary: every analysis consumes only `CamProfile`, never the
source that produced it. A profile must never silently pass off an inferred
curve as a measured one.

The repository is currently an architecture / DDD skeleton. The docs and typed
package structure are real; most numerics are intentionally not implemented yet.

## Start Here

For ordinary repo work, read these first, in order:

1. `README.md`
2. `ARCHITECTURE.md`
3. `docs/index.md`
4. `docs/reference/spec.md`
5. `docs/reference/ubiquitous-language.md`
6. `docs/decisions/decision-log.md`
7. The touched module and its nearest test.

For source-ingest work, also read `docs/how-to/add-a-new-source.md`.

For round-2 design direction, read
`docs/design/round2/IDEATION_SYNTHESIS.md` before changing the value,
derivative, refusal, or safety-verdict model.

## Product Boundary

- Milestone 1 is `cam card -> CamProfile`, not `cam card -> DCR` or any other
  downstream analysis result.
- The fixed dependency rule is `sources -> profile <- analysis`.
  `cam_analyzer.analysis` must not import `cam_analyzer.sources` or source
  types such as `CamCard`.
- Analyses speak the `CamProfile` query surface only:
  `lift_at`, `velocity_at`, `acceleration_at`, `jerk_at`,
  `events_at_lift`, `duration_at_lift`, `max_lift`, and
  `area_under_curve`.
- Measured, inferred, and extrapolated values are distinct at the value level.
  Do not erase provenance to make analysis code easier to write.
- Units and frames are explicit at the boundary. Do not introduce bare floats
  for lift, angle, velocity, acceleration, jerk, clearance, or area where a
  typed/stamped value is required.
- Swapping a cam-card approximation for measured data must not require analysis
  code changes. It may change the answer; C4 is code-stability, not
  verdict-stability.
- `docs/reference/spec.md`, `Camshaft_Analysis_Spec.md`, `prompt.md`, and the
  accepted decisions in `docs/decisions/decision-log.md` are the durable product
  sources. If docs and implemented behavior disagree, surface the drift and fix
  the stale side in the same change when the scope allows.

## Working With Striatum Artifacts

This repo contains Striatum-generated design provenance under `docs/operator/`
and ignored live scratch under `.striatum/`.

- Treat `docs/operator/workflows/` and `docs/design/` as provenance unless the
  current task explicitly asks to run or modify a workflow.
- Do not commit `.striatum/`, caches, transcripts, lane scratch, private
  diagnostics, or generated runtime state.
- If the user says "you're an operator" or starts operator-style Striatum work,
  run `striatum operator bootstrap --markdown` first from the repository root
  and follow the packet's `next_actions` and `reading_plan`. If bootstrap or
  doctor reports problems, surface them instead of guessing from repository
  files alone.
- If you are actually running inside a Striatum workflow, follow the workflow
  packet, write-scope, artifact, and state-transition instructions from that
  packet. Do not advance workflow state by editing repo files directly unless
  the packet permits it.

## Development

Set up the package and dev tools with:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[dev]'
```

Useful checks:

```bash
pytest tests/test_architecture_boundary.py
pytest tests/
mypy
ruff check src tests
lint-imports
```

`tests/test_architecture_boundary.py` is load-bearing. It enforces C1 so
analysis cannot import the source layer. Keep it green.

## Change Discipline

- Add or update tests for behavior changes, especially boundary, provenance,
  refusal, and import-direction behavior.
- Keep docs aligned with code when changing the boundary, decisions, safety
  semantics, or milestone scope. Update `docs/decisions/decision-log.md` for
  product or architecture decisions.
- Do not re-propose ideas already rejected in the decision log unless new
  evidence changes the tradeoff.
- Prefer repository-relative paths in docs and fixtures. Avoid hardcoded
  home-directory paths.
- Commit and push to `master` (the default branch) at the end of every turn;
  never leave a dirty working tree. Prefer small commits that leave the branch in
  a runnable state, and commit/push after each coherent, validated slice rather
  than batching. If push or credentials are blocked, record the exact blocker
  instead of leaving local work silently stranded.
- Keep new source-specific parsing under `cam_analyzer.sources`; express every
  source as a `CanonicalLiftModel` plus one named operator, then expose it
  through `CanonicalCamProfile`.
- Keep analysis modules source-blind. If analysis needs a fact that only a
  source knows, route that need through the profile boundary or record the
  boundary gap as a design issue.
- New durable Markdown artifacts should identify their status and source of
  authority. Design provenance is not automatically an accepted decision.

## Historical Material

`docs/design/branches/`, `docs/design/round2/branches/`, and
`docs/operator/workflows/` preserve how the architecture was produced. They may
contain branch-specific or rejected ideas. Do not treat them as current
instructions without checking the synthesis docs and decision log.

<!-- BEGIN PROXIMAL PLANE TRACKING -->
## Plane Tracking

This repository is represented in the local/private Plane workspace `Proximal`.

- Plane project: `Cam Analyzer` (`CAMANA`)
- Issue tracker: Plane (`Proximal` workspace), project `Cam Analyzer` (`CAMANA`).
- Plane URL: `https://proximal.tail0ecc2e.ts.net:10000/`
- GitHub repo: `https://github.com/halbritt/cam-analyzer`
- GitHub Issues: deprecated; use Plane work items for new issue tracking, claims, reviews, and issue-state changes.
- Use Plane work items for multi-agent planning, claims, submitted artifacts, reviews, and acceptance decisions.
- When updating Plane, include the repo, branch/worktree, `run_id`, `base_sha`, artifact links, verification evidence, and authority scope in the work item description or comments.
- Do not commit Plane API tokens. Local tokens and MCP env files live outside git under `~/.config/plane/`.
<!-- END PROXIMAL PLANE TRACKING -->
