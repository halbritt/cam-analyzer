# Cam Analyzer — Run Retrospective: `cam_profile_architecture` (round 1, run `0d48ede6…`)

> Auditor: Claude Opus 4.8 (`claude-opus-4-8[1m]`) · Date: 2026-06-16
> Prompt: `~/git/prompts/RUN_RETROSPECTIVE.md` · Process audit only; product correctness out of scope except bounded spot-checks.
> Question answered: *did this run earn confidence in its process gates, or did its provenance create false confidence?*

---

## Process Verdict

**`PROCESS_FRAGILE`** · confidence **medium**

| Dimension | Grade |
|---|---|
| review substance | `not_applicable` (no review/verdict/revision gate; the convergence critic is the sole quality gate and never executed) |
| revision convergence | `not_applicable` (workflow defines no revision loops) |
| lane independence | `strong` (with a model-driven depth-asymmetry finding) |
| synthesis fidelity | `adequate` (only synthesis is the **ungated, out-of-band** `ROUND1_SYNTHESIS.md`; faithful and well-sourced, but bypassed the gate and mixes uncheckable model attributions) |
| decision & escalation hygiene | `strong` |
| provenance completeness | `weak` (back-half expected artifacts absent; terminal state not legible from a status marker) |
| recommendation quality | `not_applicable` (run emitted no next-run recommendations) |

The run completed its **diverge** phase (5 of 5 branch artifacts published and committed) and then **wedged at the diverge→converge fan-in** on a known striatum defect (`#317` `artifact_immutable_byline_mismatch`, with `#302` same-attempt requeue as proximate cause). The operator disclosed the wedge in a schema'd decision artifact, invalidated the wedged branch, and then reproduced convergence and synthesis **entirely outside striatum** via an operator-run `/adhd` pass. The workflow's own quality gates — convergence-critic scoring/trap-detection, the three deepen jobs, and final synthesis — **never executed**, so they left **zero committed gate provenance**. This is disclosed, documented, and the out-of-band substitute (`ROUND1_SYNTHESIS.md`) is faithful to its sources; that disclosure is what keeps the verdict at `PROCESS_FRAGILE` rather than `PROCESS_UNRELIABLE`. But there is no committed evidence that any quality gate examined the diverge output, and the terminal/wedged run state is inferable only from a decision artifact and prose headers, not from a status marker. Confidence is capped at `medium`: exported/live enrichment was not authorized or ingested, and back-half provenance is missing by the wedge.

---

## 0. Provenance Inspected

- **Target:** run `run_0d48ede6844226507e8eb8c7494997d3`, workflow `cam_profile_architecture` (round 1, `workflow_version: 2026-06-16`, `schema_version: striatum.workflow.v1`).
- **Repo:** `/home/halbritt/git/cam-analyzer`, on `master` at HEAD `de615e9`, working tree clean at audit start. Run branch `striatum/cam_profile_architecture` exists. `.striatum/` is git-ignored.
- **Liveness:** all three `run-drive-*.pid` files (`0d48…`, `4366…`, `9f04…`) point to **dead** PIDs; no live run. No daemon queried.
- **Evidence tiers used:**
  - `committed` — `docs/**` (workflow definitions, prompts, roles, `PROBLEM_BRIEF.md`, 5 branch `IDEAS.md`, `ROUND1_SYNTHESIS.md`, decision artifact). Primary tier for every material claim below.
  - `history` — `git log`/`git ls-files`/`--stat` over `docs/` and `.gitignore` (commits `4225140`, `f29e8ee`, `2272fc0`, `f28420d`, `7b84bbc`, `de615e9`).
  - `exported` — local `.striatum/scratch/**` daemon logs (`helper-events.jsonl`, `pty.log`, `sup_*`, `lane-mcp-config-*`) **exist but were not ingested**: exported/live reads require explicit authorization, which was not granted. Their absence does not change the verdict because the wedge mechanism is already documented in committed evidence.
  - `live` — none (not authorized).
- **Expected artifacts (per `workflow.json`) — found / missing:**

  | logical_name | path | placement | required | status |
  |---|---|---|---|---|
  | problem_brief | `docs/design/PROBLEM_BRIEF.md` | git_publication | yes | **present** |
  | branch_1_adversarial_boundary | `…/branch_1_adversarial_boundary/IDEAS.md` | git_publication | yes | **present** |
  | branch_2_remove_assumption | `…/branch_2_remove_assumption/IDEAS.md` | git_publication | yes | **present** |
  | branch_3_short_seller | `…/branch_3_short_seller/IDEAS.md` | git_publication | yes | **present** |
  | branch_4_extreme_cheap | `…/branch_4_extreme_cheap/IDEAS.md` | git_publication | yes | **present** |
  | branch_5_archaeologist_2200 | `…/branch_5_archaeologist_2200/IDEAS.md` | git_publication | yes | **present** (salvaged -001) |
  | convergence_ledger | `docs/design/CONVERGENCE.md` | git_publication | yes | **MISSING** (never produced) |
  | deepen_1/2/3 | `docs/design/deepened/deepen_{1,2,3}/DEEPENED.md` | blob_exhaust | yes | **MISSING** (never produced) |
  | ideation_synthesis | `docs/design/IDEATION_SYNTHESIS.md` | git_publication | yes | **MISSING** (never produced) |

- **Non-expected artifacts present:** `docs/design/ROUND1_SYNTHESIS.md` (out-of-band operator synthesis) and `docs/operator/decisions/branch_5_invalidate.md` (decision artifact). Both are recovery/disclosure artifacts, not workflow-job outputs.
- **Unread / not-ingested:** `.striatum/scratch/**` (exported, unauthorized); the `cam-wr250r.pdf` source; product code (none exists — this run is an ideation run, not a build).
- **Related runs (context only, not deep-audited):** `run_9f04d807…` = `cam_profile_architecture_r2` (round 2), scaffold-only — `git ls-files docs/design/round2/` is empty, no committed artifacts. `run_4366b30e…` = earliest run-drive PID (13:18), no committed design artifacts attributable to it.

---

## 1. Reconstructed Run Shape

From `workflow.json` (`committed`): a single-pass divergent-ideation DAG.

```
frame_problem (author/Claude, synthesis)
   └─▶ diverge ×5  (parallel_group "diverge", max_active_jobs 5, fresh_session_required)
         branch_1 adversarial_boundary   → lane author     (claude-opus-4-8)
         branch_2 remove_assumption       → lane reviewer_1 (codex --yolo)
         branch_3 short_seller            → lane reviewer_2 (claude-opus-4-8)
         branch_4 extreme_cheap           → lane author     (claude-opus-4-8)
         branch_5 archaeologist_2200      → lane reviewer_1 (codex --yolo)
            └─▶ converge (reviewer_2, the CRITIC: score/cluster/trap/cross-model)
                  └─▶ deepen ×3 (parallel_group "deepen", fresh_session_required)
                        └─▶ final_synthesis (reviewer_2)
```

- **Lanes:** `author` = Claude Opus 4.8; `reviewer_1` = Codex (`/home/halbritt/.local/bin/codex --yolo`); `reviewer_2` = Claude Opus 4.8. `require_disjoint_write_scopes: true`, per-job worktree isolation, pty_helper supervision. So the diverge fleet was **3 Claude branches + 2 Codex branches; no Gemini lane in round 1** — a fact that matters for §8.
- **Verdict sequence:** there is none in the conventional sense — this workflow has **no review jobs and no `needs_revision` edges**. Every edge fires on `completed`. The sole quality gate is `converge` (the convergence critic).
- **Terminal state:** the run wedged during the diverge→converge fan-in. Per the committed decision artifact (`dec_65241ecfb1d68487f20f6c717c750127`, owner `human`, outcome `accepted`, `2026-06-16T14:09:04Z`): `branch_5` published `art_92a46` (`-001`), then a `#302` same-attempt requeue occurred; a second session could not republish (artifact immutable), raising `artifact_immutable_byline_mismatch` (`#317`); the `-001` body was "unrecoverable so reseal impossible; no resolve path for this blocker kind." The operator **invalidated branch_5 for a fresh re-run**. The run was not resumed through striatum; the diverge artifacts were instead salvaged by hand (commit `2272fc0`) and convergence+synthesis were reproduced out-of-band.

---

## 2. Process Scorecard

**Lane independence — `strong`.** Five branches, five genuinely distinct cognitive frames, five distinct artifacts with no copied content. Cross-model agreement is visible and real (see §7). Subtracting the mandated skeleton (DIVERGENT mode, 6 distinct ideas, no eval/rank/hedge, "first three obvious banned", branch-blind, publish-at-path), the residual content is fully frame-specific. *Finding:* the two **Codex lanes (branch_2: 16 lines; branch_5: 15 lines)** are markedly thinner than the three Claude lanes (branch_1: 124; branch_3: 71; branch_4: 61). All five satisfied the "6 distinct ideas" letter, so this is not a gate failure — but had `converge` run, the depth asymmetry would have biased novelty/viability/fit scoring against the thin branches, and there is no committed evidence anyone checked for that.

**Decision & escalation hygiene — `strong`.** The wedge was escalated and resolved through a committed, schema-conformant decision artifact with a human owner, an accepted outcome, a precise mechanism in the rationale, and explicit references to the upstream defects (`#302`/`#317`/`#290`/`#296`). `follow_up_required: false` is consistent with the operator's pivot to a fresh round. This is exemplary disclosure hygiene.

**Synthesis fidelity — `adequate` (with a structural caveat).** The only synthesis in the tree is `ROUND1_SYNTHESIS.md`, produced by an operator-run `/adhd` pass (commit `7b84bbc`), **not** by the gated `converge`/`deepen`/`final_synthesis` jobs. Judged purely on synthesis quality it is good: it names its branch inputs by citation (`B1·I2`, `B3·S6`, `B4·I5`, …), clusters into A–E, carries traps with one-line reasons, preserves correct minority findings, stars a non-obvious-but-viable pick (cluster D), and adds a wildcard provocation. But it **bypassed the gate**, and it conflates checkable branch-idea provenance with uncheckable model attributions (§8). Grading the *gate dimension*, the workflow's synthesis path scored nothing because it never ran.

**Provenance completeness — `weak`.** Three required artifacts (`CONVERGENCE.md`, the three `DEEPENED.md`, `IDEATION_SYNTHESIS.md`) are absent. Their absence is *explained* by the wedge, but there is **no committed run-status marker** that says "run `0d48…` wedged at `converge`." The terminal state is reconstructable only by cross-reading the decision artifact and the `ROUND1_SYNTHESIS` header — exactly the legibility gap tracked as striatum `#305`. A reader who saw only `docs/design/` (brief + 5 branches + a synthesis) could mistake a wedged run for a deliberately-scoped diverge-only run.

**Review substance / revision convergence — `not_applicable`.** This workflow declares no review jobs and no revision edges; the convergence critic is a scoring/clustering synthesis, not a verdict-bearing review gate. There is nothing of this kind to grade, and (separately) the critic never executed.

**Recommendation quality — `not_applicable`.** The run produced no next-run recommendations of its own; §10 supplies them.

---

## 3. Findings (ordered by process severity)

**F1 — The workflow's quality gates never executed; an ungated out-of-band synthesis substituted for them (severity: high, disclosed).**
*Mechanism:* the run wedged at the diverge→converge fan-in (`#317`/`#302`). Because the blocker had "no resolve path," the operator invalidated `branch_5` and did not resume the surviving DAG (`converge` → `deepen×3` → `final_synthesis`) through striatum. Convergence and synthesis were instead reproduced by an operator `/adhd` pass.
*Evidence:* missing `CONVERGENCE.md`/`deepened/**`/`IDEATION_SYNTHESIS.md` (`committed`, by absence); `ROUND1_SYNTHESIS.md` header self-identifying as the `/adhd` substitute and "not a committed design decision" (`committed`); decision artifact (`committed`).
*Process consequence:* the convergence critic's scoring, trap-detection, and cross-model-agreement check — the only quality gate in the workflow — produced **no committed provenance**, so an auditor cannot confirm any gate examined the diverge output before it seeded round 2. The trap list and shortlist that *do* exist were authored outside the gated, branch-blind, fresh-session discipline the workflow was built to enforce.
*Smallest next-run fix direction:* this maps cleanly to existing striatum issues — see §"GH Issues". No new issue; the next-run process fix is to ensure the diverge fan-in can complete (serial cap / deferred join) so `converge` actually runs, or to add a striatum-native "resume from salvaged diverge artifacts" path rather than redoing the back half by hand.

**F2 — Terminal/wedged run state is not legible from committed provenance (severity: medium, disclosed).** Reconstructing "this run wedged" required the decision artifact plus a synthesis-header sentence; no status marker exists in the committed tree. This is striatum `#305`.

**F3 — Model-driven lane-depth asymmetry in heterogeneous-model divergence (severity: low).** The two Codex branches (15–16 lines) are an order of magnitude thinner than the Claude branches (61–124 lines) under the identical diverger skeleton. Not a gate failure, but a quality signal the (un-run) convergence critic was the only thing positioned to catch.

**F4 — The `diverge` task prompt shipped as an unfilled template stub (severity: low, workflow-authoring).** `prompts/diverge.md` reads "Replace this stub with the frame's vantage from your objective." The four other prompts (`frame_problem`, `converge`, `deepen`, `final_synthesis`) are properly authored. The diverge lanes still functioned because each branch's frame is fully specified in its job `objective`, but the committed prompt is a non-actionable placeholder. This is operator/workflow-authoring hygiene, not a striatum daemon defect.

**F5 — Inconsistent artifact front matter across diverge lanes (severity: low).** branch_2 uses YAML front matter (`--- author: … ---`); branch_1/3/4 use a `> author:` blockquote or a bare `author:` line; branch_5 a bare line. This mirrors the pattern tracked (for deepen artifacts) in striatum `#307` (closed); it persists here for diverge artifacts.

---

## 4. Review Substance

The mandatory review table is **not applicable**: `cam_profile_architecture` declares no review jobs, no verdicts, and no `needs_revision` edges. Its single quality gate, `converge` (the convergence critic), is a scoring/clustering synthesis that **never executed** (the run wedged before reaching it). There is therefore no review artifact to grade for cited specifics, falsifying scenarios, reviewed-target correctness, or severity consistency. No wrong-target review risk exists because no review ran. Bounded product spot-checks were unnecessary: no review made product claims to verify.

The closest thing to "review" that exists is the trap list inside the out-of-band `ROUND1_SYNTHESIS.md`. Treated as data (not as a gate output), its traps are well-grounded — e.g. "confidence-as-a-single-scalar-tag is dead — refuted independently by 3 branches" checks out against branch_1 Idea 3, branch_3 Short 3, branch_2 Idea 6, and branch_5's "confidence rings" bullet (`committed`). But it carries no gate authority.

---

## 5. Revision Convergence

Not applicable. The workflow defines no repair/revision loops. The one repair event in the run was **branch invalidation**, not a `needs_revision` cycle: `branch_5` wedged, the operator invalidated it (decision `dec_65241ecf…`), and the intended "fresh re-run on a new attempt" never occurred within round 1 — the operator pivoted to the `/adhd` synthesis and round 2 instead. There is no finding→change→re-review→closure mapping to grade, and no unresolved *revision* loop; the unresolved item is the wedge itself, which the operator closed by abandoning the back half of the run.

---

## 6. Lane Independence

Strong, after subtracting the mandated skeleton. Each branch applied a distinct frame and produced non-overlapping content:

- **branch_1 / adversarial_boundary** (Claude/author, `diverger-author-001`): supplied the required "checkable intermediate" (the `well-typed ⟹ physically-coherent ∧ honestly-labeled` implication), six trap inputs T1–T6, six mechanism-distinct ideas, and an explicit "banned obvious answers" section. The richest branch.
- **branch_3 / short_seller** (Claude/reviewer_2, `diverger-reviewer-2-001`): six "bull thesis / voiding assumption / cheap short" shorts; independently surfaces the cliff-function and CompositeProfile-seam risks.
- **branch_4 / extreme_cheap** (Claude/author, `diverger-author-002`): six crude-but-load-bearing ideas (file-as-interface, half-sine lobe, finite-difference wrapper, value-carried provenance, grep-as-rule).
- **branch_2 / remove_assumption** (Codex/reviewer_1, `diverger-reviewer-1-002`): six terse "remove the fixed thing" ideas (content-addressed document, ensemble curves, invalidation graph, quality-as-curve).
- **branch_5 / archaeologist_2200** (Codex/reviewer_1, `diverger-reviewer-1-001`): six terse excavation-metaphor bullets (provenance strata, confidence rings, swap scars).

**Genuine cross-model convergence (a real confidence signal the workflow was designed to detect):** "confidence is not a scalar" appears independently in branch_1 (Claude), branch_3 (Claude), branch_2 (Codex), and branch_5 (Codex) — i.e. across both model families. "Type the boundary value (unit·frame·provenance), no setter" appears in branch_1 and branch_4 (Claude) and is echoed by branch_3 Short 6. No copied blind spots are evident. The one independence-adjacent weakness is depth (F3), not convergence-by-imitation. Because `converge` never ran, this cross-model signal was harvested only by the out-of-band synthesis, not by the gate built to record it.

---

## 7. Synthesis And Decisions

**Source fidelity (out-of-band synthesis).** `ROUND1_SYNTHESIS.md` cites specific branch ideas for each cluster, preserves the minority/maximalist cluster E while explicitly marking it premature, and resolves the A/B/C relationship (not competitors but three facets) with stated reasoning. Its five traps each carry a one-line justification and are flagged "do NOT re-propose in round 2", which is correctly carried forward as round-2 constraints. As a synthesis it does not launder or contradict its sources.

**Decisions / escalations.** One committed decision (`dec_65241ecf…`): invalidate wedged `branch_5`. Disclosed, justified, human-owned, accepted. The wedge is also disclosed in the synthesis header. No forced verdicts, no undisclosed overrides.

**Downstream reflection.** The synthesis explicitly seeds round 2 (`cam_profile_architecture_r2`), and round 2's `workflow.json` lists `docs/design/ROUND1_SYNTHESIS.md` as a required context doc — the handoff is wired. Round 2 also changed the fleet (author→Codex, reviewer_1→`agy`/Gemini, reviewer_2→Claude) and set `max_active_jobs: 1` (a serial-execution mitigation for the fan-out wedge). *Caveat for the operator, context-only:* round 2 is exposed to striatum `#322` (run-drive may ignore `max_active_jobs`, so the serial cap may not actually hold) and `#311` (the `agy`/Gemini reviewer lane has wedged whole runs); the round-1 fan-in fragility is not yet demonstrably mitigated.

---

## 8. Unknowable / Uncheckable From This Provenance

- **Model attributions in the synthesis are partly uncheckable.** `ROUND1_SYNTHESIS.md` attributes "Pillar C · per-region fitness — *Gemini*" and claims the deepen "drew genuine input from all three frontier models." But **no Gemini lane ran in round 1** (the diverge fleet was 3 Claude + 2 Codex per `workflow.json`). The *idea* behind Pillar C has real committed branch provenance (branch_1 Idea 4, branch_3 Short 3, branch_2 Idea 6, branch_5), so it is not fabricated — but the "Gemini deepened it" attribution refers to the out-of-band `/adhd` pass, which left no committed transcript. Treat the per-model deepen attributions as `claimed, uncheckable`.
- **Session freshness, exact timings, the requeue sequence, lease/recovery events, and the `art_92a46` byline collision** are knowable only from `.striatum/scratch/**` (exported) or the daemon (live), neither ingested/authorized. The committed decision narrates them but is itself a durable claim.
- **Whether `branch_5`'s invalidated fresh re-run was ever attempted** before the operator pivoted is not legible from committed provenance.
- **What `run_4366b30e…` was** (an earlier round-1 attempt? a scaffold dry-run?) is not determinable from committed artifacts.

---

## 9. GH Issues — Dupe Check Result

The user asked to file any needed striatum issues after checking for dupes. **Every failure mode this run exhibited is already tracked on `halbritt/striatum`. No new issue is warranted — filing one would duplicate.** Mapping (verified via `gh issue view`):

| This run's symptom | Existing issue | State |
|---|---|---|
| branch_5 same-attempt requeue of an already-published job → `artifact_immutable_byline_mismatch`, no automated recovery | **#317** | open |
| recovery sweep won't reclaim a `tmux_pane_dead`/`lost_candidate` session that stays `active`, wedging the lane | **#302** | open |
| parallel fan-in strands sibling artifacts / fan-out wedges (root of the diverge fan-in fragility) | **#290** (+ #319, #327) | closed (+open follow-ups) |
| `max_active_jobs` serial cap unenforceable (round-2 mitigation may not hold) | **#322** | open |
| terminal/wedged run state not legible from committed provenance (F2) | **#305** | open |
| diverge ideas blob-routed → convergence inputs unauditable (mitigated here via `git_publication`) | **#306** | open |
| inconsistent artifact front matter across lanes (F5) | **#307** | closed |
| `agy`/Gemini reviewer lane wedges whole run (round-2 exposure) | **#311** | open |
| codex lane MCP endpoint goes stale (referenced in the decision) | **#296** | closed |

The decision artifact itself already references `#302`/`#317`/`#290`/`#296`, and the round-1 synthesis header references `#302`/`#317`/`#290`/`#296`. Findings F3 (lane-depth asymmetry) and F4 (unfilled diverge prompt stub) are **workflow-authoring / model-behavior observations, not striatum daemon defects**, and are not issue-worthy against the striatum repo.

*Optional, not done:* the most useful tracker action would be a corroborating comment on **#317** and/or **#305** adding this run's concrete evidence (run `0d48ede6…`, decision `dec_65241ecf…`, and the fact that the only viable recovery was a hand-salvage via git plus an out-of-band `/adhd` synthesis, because the daemon offered no resolve path). Posting a comment is an outward-facing write, so it is left for operator confirmation rather than done unilaterally.

---

## 10. Recommendations For The Next Run

Each is tied to an observed process failure and scoped to workflow/prompt/role/gate/operator-process — no product design changes.

1. **Make the diverge→converge fan-in completable before relying on the gate (F1).** The single most consequential process failure is that the quality gate never ran. Until striatum `#322`/`#302`/`#319` land, run divergent-ideation **serially in practice** (confirm the serial cap is actually enforced, not merely declared — `#322`), or stage diverge and converge as separate runs so a diverge wedge cannot strand the entire synthesis half.
2. **Do not let an out-of-band synthesis silently replace the gate (F1).** If the operator must synthesize by hand after a wedge, capture the convergence ledger and synthesis at the workflow's expected paths (`CONVERGENCE.md`, `IDEATION_SYNTHESIS.md`) with a header that marks them operator-produced and ungated — so the next auditor sees the gate was bypassed without cross-reading a decision artifact. (Complements `#305`.)
3. **Emit a committed terminal-state marker on wedge/cancel (F2).** A one-line committed status file ("run `0d48…` wedged at `converge`, see `dec_…`") would make the run shape self-evident. Tracked as `#305`; surface it to that issue.
4. **Fill the `diverge` task prompt (F4).** Replace the "Replace this stub…" placeholder with the actual frame text, or delete the prompt file if the `objective` is authoritative — a committed placeholder prompt is a latent trap for any future lane that reads the prompt instead of the objective.
5. **Counter model-driven depth asymmetry in heterogeneous divergence (F3).** Either set a per-branch substance floor in the diverger objective (e.g. "each idea ≥2 sentences with its load-bearing mechanism"), or assign the terser model family to frames that reward terseness, so the convergence critic scores comparable artifacts.
6. **Verify round-2 fleet exposure before launch (context).** Round 2 routes `reviewer_1` through `agy`/Gemini (`#311`) and depends on a serial cap that may not hold (`#322`). Confirm both are mitigated, or the round-2 fan-in will likely reproduce the round-1 wedge.

---

*End of retrospective. Read-only audit; no provenance, workflow, source, or issue state was modified.*
