author: convergence-critic-reviewer-2-001

# Round 2 Convergence Ledger — Cam Profile Architecture

> **Role:** convergence critic (CRITIC, not generator). Reads all 5 divergence
> branches, scores every idea, clusters by underlying angle, flags traps, selects the
> top-3 for the deepen phase, and records cross-model agreement.
> **Inputs:** `PROBLEM_BRIEF.md` + `branches/branch_{1..5}/IDEAS.md`.
> **Grounding:** `prompt.md`, `Camshaft_Analysis_Spec.md`, `docs/design/ROUND1_SYNTHESIS.md`.

Round 1 already **settled the skeleton** (typed provenance-carrying `CamProfile` = Pillars
A·B·C) and asked round 2 to diverge on exactly two unresolved, high-stakes questions, plus
one provocation:

1. **Ergonomics-as-integrity** — make the provenance-carrying path *strictly more
   convenient* than bare floats, so the guarantee can't be quietly stripped (the
   `.magnitude` escape hatch all three round-1 models named as the #1 risk).
2. **Honesty under discontinuity** — what the boundary owes a consumer when the verdict is
   a *cliff function* of the profile (PTV contact, spring float), where "swap source
   without code change" silently flips safe→unsafe.
3. **(Provocation)** the inverted query: analysis *submits a question with required
   fitness*; the profile answers with a stamped value **or formally refuses**.

`fit` is scored primarily against those three, the `PROBLEM_BRIEF` decision criteria, and
the round-1 hard-constraint traps (which must **not** be re-proposed).

---

## 1. Model-family map (for the cross-model signal)

Branches ran on three different agent lanes, each a different model family:

| Lane | Command | Model family | Branches on this lane |
|---|---|---|---|
| `author` | `codex --yolo` | **OpenAI / Codex (GPT)** | branch_1 (liability_chain_auditor), branch_4 (short_seller) |
| `reviewer_1` | `agy` | **Gemini / Google** (the 3rd round-1 frontier model) | branch_2 (decade_inheritor), branch_5 (hardware_engineer) |
| `reviewer_2` | `claude --model claude-opus-4-8` | **Anthropic / Claude Opus** | branch_3 (extreme_cheap) |

So "independently surfaced across families" = the **same angle appearing on two or more of
{Codex, Gemini, Opus}** via branches that could not see each other. (Gemini-family
attribution of the `agy` lane follows the round-1 record; even if `agy` is mislabeled, it is
demonstrably *neither* the Codex *nor* the Opus lane, so the cross-lane convergence below
still holds as cross-family.)

Idea IDs below use `B<branch>.<idea#>` (e.g. `B3.5` = branch_3 idea 5).

---

## 2. Clusters (by underlying angle, not surface keywords)

- **α — The value object itself resists stripping.** Kill the `.magnitude`/bare-float exit
  by making the honest value *be* the convenient value. `B3.3` (ProvFloat: float subclass,
  loud on display), `B2.2` (ProvenancedFloat: dunder propagation of weakest stamp), `B5.1`
  (bus parity/ECC `Quantity`, gate-arithmetic), `B1.5` (`.magnitude` = custody transfer),
  `B3.1` (lossy precision-as-stamp — **trap**).
- **β — Delete the bare-float exit / refusal-first surface.** The §3 inverted-query
  provocation made concrete: the only way to get a number is a fitness-gated question that
  can refuse. `B4.1` (`Answer|Refusal`, ban `lift_at` in safety modules), `B3.6`
  (getter-less `ask(question, require)`), `B2.6` (refusal-first 3-valued types, mypy-forced),
  `B1.3` (refusal names the missing owner), `B2.4` (rich diagnostic refusal bundle).
- **γ — Honesty under discontinuity via bracketed verdict-agreement.** Don't emit one value;
  run the analysis over the *uncertainty bracket* and publish whether the **verdict** is
  stable. `B3.5` (run-it-twice, publish verdict-agreement), `B2.5` (dual-channel verdict-
  stability shadow), `B5.4` (dual-core lockstep + watchdog), `B2.3` (adversarial
  perturbation of the curve), `B4.4` (persist approx-vs-measured verdict deltas as a report
  section).
- **δ — Accountability / custody chain.** Track the *decision owner*, not just data
  provenance; name who is accountable when the chain breaks. `B1.1` (custody ledger per
  value), `B1.2` (explicit handoff acceptance), `B1.4` (threshold policies own the cliff
  verdict, separate from the curve owner), `B1.6` (reports print the broken chain), `B3.4`
  (append-only audit log — **soft trap**).
- **ε — Capability negotiation / fitness gating before answering.** Refuse queries the
  backing can't legitimately support (esp. high-order derivatives on sparse data). `B4.2`
  (derivative-capability matrix), `B5.5` (bus-negotiation handshake + Nyquist filter), `B5.3`
  (MPU privilege segmentation — **soft trap**), `B5.6` (entropy token-bucket — **trap**).
- **ζ — Boundary enforced by tooling/tests, not vigilance.** `B4.6` (adversarial conformance
  corpus), `B4.5` (generate notebook/CLI/report APIs from one schema — no side door), `B2.1`
  (AST import-graph audit — great as CI test, **soft trap** as boot-time audit).
- **η — Provenance granularity.** `B4.3` (event-local provenance at openings/closings/nose/
  lash, not arbitrary continuous bands).
- **(unclustered traps)** `B3.2` (NaN-poison companion), `B5.2` (cache-coherency
  invalidation protocol).

---

## 3. Scored ledger (all 30 ideas)

Weighted = `0.35·Novelty + 0.40·Viability + 0.25·Fit`. `Novelty` is judged *for round 2*
(round 1 already settled A·B·C and named the problems, so restating them scores lower).
Sorted by weighted score. ✅ = top-3 pick · 🔴 = trap · 🟡 = soft trap.

| Rank | Idea | Cluster | Family | N | V | F | **Wt** | Note |
|---|---|---|---|---|---|---|---|---|
| 1 | **B3.5** run-it-twice, publish only verdict-agreement | γ | Opus | 8 | 9 | 10 | **8.90** | ✅ PICK 1 |
| 2 | **B4.2** derivative-capability matrix before v/a/jerk | ε | Codex | 7 | 9 | 9 | **8.30** | ✅ PICK 2 |
| 3 | **B3.3** ProvFloat: silent in math, loud on display | α | Opus | 8 | 8 | 9 | **8.25** | ✅ PICK 3 |
| 4 | B4.1 `Answer\|Refusal`, ban `lift_at` in safety modules | β | Codex | 6 | 9 | 9 | 7.95 | runner-up |
| 5 | B2.5 dual-channel verdict-stability shadow | γ | Gemini | 7 | 8 | 9 | 7.90 | reinforces PICK 1 |
| 5 | B1.4 threshold policies own the cliff verdict | δ | Codex | 7 | 8 | 9 | 7.90 | underrated |
| 5 | B4.3 event-local provenance (nose/seat/lash) | η | Codex | 7 | 8 | 9 | 7.90 | refines Pillar C |
| 5 | B2.2 ProvenancedFloat: dunder propagation | α | Gemini | 7 | 8 | 9 | 7.90 | twin of PICK 3 |
| 9 | B3.6 getter-less `ask(question, require)` | β | Opus | 8 | 7 | 9 | 7.85 | boldest provocation |
| 10 | B1.3 refusal names the missing owner | β | Codex | 7 | 8 | 8 | 7.65 | |
| 10 | B2.3 adversarial curve perturbation | γ | Gemini | 7 | 8 | 8 | 7.65 | test-time |
| 12 | B2.6 refusal-first 3-valued types (mypy) | β | Gemini | 6 | 8 | 9 | 7.55 | |
| 12 | B4.6 adversarial conformance corpus | ζ | Codex | 6 | 8 | 9 | 7.55 | round-1 ★, now adopted |
| 12 | B4.4 persist approx-vs-measured verdict deltas | γ | Codex | 6 | 8 | 9 | 7.55 | report face of PICK 1 |
| 15 | B5.5 bus-negotiation handshake + Nyquist filter | ε | Gemini | 7 | 7 | 9 | 7.50 | reinforces PICK 2 |
| 15 | B4.5 generate all surfaces from one schema | ζ | Codex | 7 | 7 | 9 | 7.50 | closes the demo side-door |
| 17 | B1.5 `.magnitude` = custody transfer | α | Codex | 7 | 7 | 8 | 7.25 | reinforces PICK 3 |
| 18 | B5.4 dual-core lockstep + perturbation watchdog | γ | Gemini | 6 | 7 | 9 | 7.15 | reinforces PICK 1 |
| 19 | B1.1 custody ledger per returned value | δ | Codex | 8 | 6 | 7 | 6.95 | rich but heavy |
| 20 | B5.1 bus parity/ECC `Quantity` gate-arithmetic | α | Gemini | 6 | 7 | 8 | 6.90 | reinforces PICK 3 |
| 20 | B1.6 reports print the broken chain | δ | Codex | 6 | 7 | 8 | 6.90 | needs B1.1/B1.2 |
| 22 | B2.4 rich diagnostic refusal bundle | β | Gemini | 7 | 6 | 8 | 6.85 | scope risk in M1 |
| 23 | B1.2 handoffs require explicit acceptance | δ | Codex | 7 | 6 | 7 | 6.60 | ceremony at each seam |
| 24 | 🟡 B2.1 AST import-graph audit *at boot* | ζ | Gemini | 6 | 6 | 8 | 6.50 | do it as a CI test, not boot |
| 25 | 🟡 B3.4 append-only audit log (out-of-band truth) | δ | Opus | 7 | 6 | 5 | 6.10 | bypassable side channel |
| 26 | 🟡 B5.3 MPU privilege segmentation | ε | Gemini | 6 | 5 | 7 | 5.85 | ceremony duplicating C+β |
| 27 | 🔴 B3.2 NaN-poison companion | α | Opus | 7 | 4 | 4 | 5.05 | trap |
| 28 | 🔴 B3.1 lossy precision-as-stamp | α | Opus | 8 | 3 | 4 | 5.00 | trap |
| 29 | 🔴 B5.6 entropy token-bucket | ε | Gemini | 7 | 3 | 5 | 4.90 | trap |
| 30 | 🔴 B5.2 cache-coherency invalidation protocol | — | Gemini | 5 | 4 | 5 | 4.60 | trap |

---

## 4. Traps (attractive but hidden cost / false economy / won't scale)

- 🔴 **B5.2 — Cache-coherency invalidation protocol.** Re-proposes round-1's explicitly
  shelved "reactive invalidation graph" (Cluster E) — premature for M1. Profiles are
  immutable and recomputation is cheap, so a dependency-registering coherency controller is
  pure infrastructure tax solving a problem that barely exists yet.
- 🔴 **B3.1 — Lossy precision-as-stamp.** Encoding provenance by *throwing away digits*
  corrupts real numeric information, collides with genuinely round measured values, breaks
  reproducibility, and conflates "inferred" with "low-precision" — an inferred value may be
  needed at full precision for downstream integration. False economy: it damages the math to
  carry a flag a single byte could carry.
- 🔴 **B3.2 — NaN-poison companion.** Elegant, but `nan` propagates everywhere and is trivially
  laundered (`np.nan_to_num`, `if x:` guards, `max()` skipping nan), `>=` comparisons silently
  go `False`, and — fatally — it **discards the reason for refusal**, converting honest
  "I don't know" into a mysterious blank. The opposite of what the decade-inheritor needs.
- 🔴 **B5.6 — Entropy token-bucket.** Charging "variance tokens" per query needs a calibrated
  uncertainty model M1 does not have, and the bucket size is an arbitrary *global* knob —
  smuggling back the single-global-budget smell round 1 killed. High mechanism, speculative
  payoff.
- 🟡 **B5.3 — MPU privilege segmentation** (soft). The privilege-register ceremony mostly
  duplicates what per-region provenance (Pillar C) + refusal-gating (β/ε) already provide,
  with more machinery. Fold the *intent* into β/ε rather than building an MPU.
- 🟡 **B3.4 — Append-only audit log** (soft). Returning naked floats and reconstructing truth
  post-hoc *concedes* the laundering and patches it out-of-band — honesty then depends on a
  report pass and a log no analysis code reads. Bypassable; contradicts the ergonomics-as-
  integrity goal.
- 🟡 **B2.1 — AST import-graph audit** (soft, *boot-time framing only*). Parsing the whole tree
  on every startup is a runtime tax and fragile. The underlying intent (block analysis→parser
  imports) is excellent **as a CI/import-linter test** (round-1 Cluster D), not as a fatal
  boot audit.

> No branch re-proposed the dead "single-scalar confidence tag," and γ correctly treats the
> cliff-function trap as the *thing to expose* rather than selling swap-stability — both good.

---

## 5. Cross-model signal (independent convergence across families) — confidence boost

Four of round-1's facets were **re-derived independently across model families**, by branches
running different vantage frames that could not see each other. This is the strongest signal
in the run:

1. **★★★ Bracketed verdict-agreement (cluster γ) — 3 families.**
   Opus `B3.5` ("run every analysis on earliest- & latest-plausible curves; publish only
   whether the *verdict* matches") + Gemini `B2.5`/`B5.4` (verdict-stability shadow / dual-core
   lockstep) + Codex `B4.4` (persist approx-vs-measured verdict deltas). Three families, three
   frames, one mechanism → **directly answers round-2 question 2** and validates **PICK 1**.

2. **★★★ Make the value itself un-strippable / kill `.magnitude` (cluster α) — 3 families.**
   Opus `B3.3` (subclass `float`, so there *is* no `.magnitude` to launder) + Gemini
   `B2.2`/`B5.1` (dunder-propagating / parity-bit value) + Codex `B1.5` (`.magnitude` becomes a
   recorded custody transfer). Three families converge on "the honest value must be the
   convenient value" → **answers round-2 question 1** and validates **PICK 3**.

3. **★★★ Refusal-first surface / delete the bare-float exit (cluster β) — 3 families.**
   Opus `B3.6` (getter-less `ask(question, require)`) + Codex `B4.1` (`Answer|Refusal`, ban
   `lift_at`) + Gemini `B2.6` (mypy-forced 3-valued types). Three families independently land
   the §3 inverted-query provocation — strong endorsement even though no single β idea cracked
   the top-3.

4. **★★ Refuse derivatives the backing can't support (cluster ε) — 2 families.**
   Codex `B4.2` (derivative-capability matrix) + Gemini `B5.5` (Nyquist bus-negotiation). Two
   families converge on "publish/negotiate supported derivative order before answering jerk"
   → kills the Pillar-B "smooth half-sine emits authoritative fiction jerk" risk and validates
   **PICK 2**.

**Single-family angles (lower convergence confidence):** the accountability/custody-chain
angle (cluster δ) was almost entirely **Codex-only** (branch_1) — genuinely novel framing
(`B1.4` especially) but unconfirmed by other families. The heavy hardware-infra mechanisms
(cache-coherency, MPU, entropy bucket — the trap cluster) were **Gemini-only** (branch_5);
that branch over-reified its metaphor into premature infrastructure. Opus's `extreme_cheap`
frame produced the cheapest *and* highest-scoring ideas (B3.5, B3.3), suggesting the crude-
build constraint was the most generative frame this round.

---

## 6. Top-3 picks (by weighted score, traps excluded)

The three picks are deliberately **orthogonal** — one per round-2 question plus the
derivative-fitness facet — and each carries cross-family convergence.

### ✅ PICK 1 → `deepen_1` · **B3.5 — Bracketed verdict-agreement** (8.90, Opus)
*"Never emit one curve. Build earliest- and latest-plausible curves, run every analysis on
both, and publish only whether the **verdict** agrees; a flip emits `UNDECIDABLE FROM CAM
CARD` instead of a number."* The cheapest possible answer to **honesty-under-discontinuity**
(question 2): a 2-element loop comparing *verdicts*, not values, with zero provenance
machinery. Respects the round-1 "swap ≠ verdict-stable" trap by construction. **3-family
convergence (γ).** Deepen toward: how the bracket is constructed (seat-timing tolerance,
lash, install offsets), and how `B4.4`/`B1.4` surface the delta and own the threshold.

### ✅ PICK 2 → `deepen_2` · **B4.2 — Derivative-capability matrix / fitness gating** (8.30, Codex)
*"Require every operator to publish a derivative-capability matrix before `velocity_at`,
`acceleration_at`, or `jerk_at` can answer."* Kills the fabricated-jerk failure mode (Pillar
B's named risk): a sparse cam-card backing must refuse 3rd-order queries (Nyquist) rather than
emit authoritative-looking fiction. Highly viable, source-agnostic. **2-family convergence
(ε)** with Gemini's `B5.5` Nyquist handshake (fold its Nyquist test in; drop the bus-protocol
ceremony). Deepen toward: what the matrix declares (max supported order × crank region) and
how refusal composes with PICK 3's value type.

### ✅ PICK 3 → `deepen_3` · **B3.3 — Honest value object: `ProvFloat`** (8.25, Opus)
*"Return a `float` subclass that behaves as an ordinary number everywhere (no `.magnitude`
accessor exists to launder, because the object **is** the magnitude); override only
`__repr__`/`__format__`/`__str__` to always emit the provenance tag."* The purest answer to
**ergonomics-as-integrity** (question 1): convenience and honesty are the *same object*, so a
laundered value announces itself the moment it reaches any print/log/plot/report cell.
**3-family convergence (α).** Load-bearing gap to close in deepening: repr-only tagging means
a *computed* result loses its stamp — **hybridize with `B2.2`'s dunder propagation** (weakest-
stamp join through arithmetic) so the tag survives math, not just display. That hybrid
(`B3.3 + B2.2`) is the recommended deepen target.

---

## 7. Runners-up worth carrying into deepen / final synthesis

- **B4.1** (β, 7.95) — `Answer|Refusal` at every safety-facing call + ban `lift_at` in
  clearance/spring modules. The pragmatic surface that *operationalizes* the inverted-query
  provocation; pairs tightly with PICK 2 and PICK 3. Top non-pick by score.
- **B1.4** (δ, 7.90) — separate the **curve-region owner** from the **threshold policy** that
  converts a continuous value into safe/unsafe. Sharpens PICK 1's cliff semantics (who decided
  the cliff) and is the most viable idea from the otherwise single-family custody cluster.
- **B4.3** (η, 7.90) — anchor provenance to **physical events** (seat ramp, nose, lash take-up),
  not arbitrary angle bands, because uncertainty concentrates exactly at the safety-critical
  zones. A direct, cheap refinement of Pillar C.
- **B4.6** (ζ, 7.55) + **B4.5** (ζ, 7.50) — the durable conformance corpus (round-1's ★) and
  "generate every surface from one schema so there is no lower-friction demo side-door." Keep
  as adopted infrastructure, not re-debated.

---

## 8. Handoff note to the deepeners

- `deepen_1` = **B3.5**, `deepen_2` = **B4.2**, `deepen_3` = **B3.3 (hybridized with B2.2)**.
- Treat round-1's traps as hard constraints; do **not** re-open single-scalar confidence,
  naive `CompositeProfile` blending, or the premature reactive-invalidation graph (cluster E /
  `B5.2`).
- All three picks share one spine: **a value can only leave the boundary if its fitness is
  proven, and the moment it can't be, the boundary says so loudly** — across math (B3.3+B2.2),
  across queries (B4.2), and across verdicts (B3.5).
