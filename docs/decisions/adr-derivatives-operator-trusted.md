# ADR — Derivative consistency is operator-TRUSTED, not constructed

- **Status:** Accepted
- **Build status:** ASSERTED (author-trusted; no executable witness pins the consistency claim)
- **Date:** 2026-06-17
- **Refines:** [D005 — Single canonical representation (Pillar B)](./decision-log.md)
- **Context:** review finding S3 / Pillar B over-claim

---

## Context

Pillar B (D005) is described as: "the eight queries are *generated* projections —
derivatives differentiate one operator — so **inconsistent derivatives are
unconstructable**." The architecture review (S3) found that the second clause
*over-claims* what the code actually guarantees.

In the shipped code an operator hand-writes **two independent methods**:

- `evaluate(crank_deg) -> float` — the lift value
  (`src/cam_analyzer/sources/cam_card.py:138`)
- `derivative(order, crank_deg) -> float` — the derivative
  (`src/cam_analyzer/sources/cam_card.py:149`)

Nothing in the system differentiates `evaluate` symbolically or numerically to
*check* `derivative`. The two are written by hand and trusted to agree. There is
no construction that makes a *disagreeing* pair impossible to build; a careless
or buggy operator can ship a `derivative()` that is inconsistent with its own
`evaluate()`, and the type system, the conformance corpus, and `mypy --strict`
will all pass it.

What Pillar B *does* structurally guarantee is the narrower, real claim:

- **One backing object.** Every query delegates to a single named operator on one
  immutable `CanonicalLiftModel`; there are no per-method subclass hooks, so two
  *different* operators cannot back the same profile.
- **Sparse-as-continuous is trapped.** An 8-point lookup masquerading as a
  continuous function is rejected — that one *is* executable
  (`tests/test_conformance_traps.py::test_sparse_as_continuous_refuses_eight_point_lookup`,
  corpus trap `sparse_as_continuous`).

The over-claim is specifically about *cross-derivative consistency* (that
`derivative` agrees with the slope of `evaluate`), which is **author discipline,
not construction**.

## Decision

State the honest claim everywhere Pillar B is described:

> **Derivatives are operator-TRUSTED.** An operator supplies `evaluate` and
> `derivative` as independent hand-written methods; the architecture trusts the
> operator author to keep them consistent. It does **not** construct that
> consistency, so it cannot be sold as "inconsistent derivatives are
> unconstructable."

Build-status stamp: **ASSERTED**. The discipline is documented and conventional;
no passing executable witness currently proves any given operator's `derivative`
matches the slope of its `evaluate`.

## Options for strengthening later (not built)

Adding an executable witness would promote the claim toward **VERIFIED**:

1. **Finite-difference consistency trap (recommended).** A conformance trap that,
   for each registered operator, samples `evaluate` around a point, forms a
   central finite difference, and asserts it agrees with `derivative(order=1,
   crank_deg)` to a tolerance over the *supported* (non-refused) regions. This
   makes a `derivative` that lies about its own `evaluate` a test failure rather
   than a reviewer's responsibility. Status: **DESIGNED**.
2. **Single-source derivatives.** Derive `derivative` *from* `evaluate` by
   autodiff or a symbolic operator so the two cannot diverge by construction —
   the strong form of Pillar B's original claim. Larger change; status
   **DESIGNED**.

Until one of these lands, the consistency guarantee remains **ASSERTED**.

## Consequences

- D005, `ARCHITECTURE.md`, `README.md`, and `domain-driven-design.md` are
  corrected to say derivatives are operator-trusted (consistency is the author's
  discipline), keeping only the structurally-true claims (one operator,
  sparse-as-continuous trapped).
- A future finite-difference-consistency trap is recorded as `DESIGNED` in
  [`docs/CLAIMS_LEDGER.md`](../CLAIMS_LEDGER.md) and as a revisit trigger on D005.

## See also

- [`decision-log.md`](./decision-log.md) — D005, D010, D014.
- [`docs/CLAIMS_LEDGER.md`](../CLAIMS_LEDGER.md) — the build-status ledger.
- `src/cam_analyzer/sources/cam_card.py:138`, `:149` — the two independent methods.
