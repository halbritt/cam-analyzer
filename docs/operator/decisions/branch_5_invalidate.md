---
schema_version: striatum.decision.v1
decision_id: "dec_65241ecfb1d68487f20f6c717c750127"
run_id: "run_0d48ede6844226507e8eb8c7494997d3"
artifact_kind: decision
owner: human
outcome: accepted
follow_up_required: false
title: "Invalidate wedged branch_5 (artifact_immutable_byline_mismatch, #317) for fresh re-run"
created_at: "2026-06-16T14:09:04Z"
---

# Invalidate wedged branch_5 (artifact_immutable_byline_mismatch, #317) for fresh re-run

Decision ID: `dec_65241ecfb1d68487f20f6c717c750127`
Run ID: `run_0d48ede6844226507e8eb8c7494997d3`
Outcome: `accepted`

## Rationale

branch_5 wedged: first session published art_92a46 (-001) then #302 requeue on same attempt; second session could not republish (immutable), raised artifact_immutable_byline_mismatch blocker. -001 body unrecoverable so reseal impossible; no resolve path for this blocker kind. Invalidate to allow a clean re-run on a fresh attempt.
