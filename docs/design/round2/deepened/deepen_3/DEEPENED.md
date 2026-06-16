---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: deepener-reviewer-2-001

# Deepen pick 3 — `ProvFloat`: the honest value *is* the convenient value

> **Pick (rank #3, Wt 8.25, 3-family convergence on cluster α):** **B3.3 — `float`
> subclass, silent in math, loud on display**, hybridized as the convergence ledger
> directs with **B2.2 — dunder-propagating `ProvenancedFloat`** (weakest-stamp join
> through arithmetic). Answers round-2 question 1: *ergonomics-as-integrity.*

---

## Sketch — how it would actually work

Every `CamProfile` query (`lift_at`, `velocity_at`, `area_under_curve`, …) returns a
**`ProvFloat`**: a `float` subclass carrying one `Provenance` stamp from the Pillar-A
lattice (`MEASURED > INFERRED > EXTRAPOLATED`), so it is a drop-in number anywhere a
float is accepted and there is *no `.magnitude` field to strip* — the object **is** the
magnitude. Every arithmetic dunder (`__add__`/`__sub__`/`__mul__`/`__truediv__`, their
reflected and in-place forms) returns a fresh `ProvFloat` whose stamp is the lattice-min
of its operands, so a piston-to-valve clearance computed from a single `EXTRAPOLATED`
nose value is *itself* `EXTRAPOLATED` without the analysis author lifting a finger; bare
Python `float`/`int` operands are treated as exact constants (top of lattice) so a literal
like `2.0` never pollutes the join. Only `__repr__`/`__str__`/`__format__` are overridden,
and they **always** print the tag (`0.041" [EXTRAPOLATED]`), so the instant a laundered
low-confidence value reaches a log line, a plot label, a report cell, or a debugger it
announces itself — nothing extra to remember to call. The single sanctioned escape is
`float(x)`, which is explicit, ugly, grep-able, and lint-flagged, so metadata-stripping is
loud in diffs instead of being the silent default. For M1 the cam-card half-sine operator
stamps its nose/ramp samples `INFERRED` (or `EXTRAPOLATED` past Nyquist), measured-lift
operators stamp `MEASURED`, and the PTV/DCR/spring modules never import a parser — they do
ordinary arithmetic and the weakest stamp falls out of the chain for free. The net effect
is the cheapest possible answer to ergonomics-as-integrity: the honest value *is* the
convenient value, so the lie can never be cheaper than the truth, and the per-value stamp
varies per crank-region query — respecting the round-1 "no single-scalar confidence tag"
trap by construction.

## Load-bearing risk — the NumPy / vectorization escape

The scalar pillar quietly dies the moment values enter a `np.ndarray`. Real cam-profile
math is array math: 720 lift samples, `np.gradient` for velocity/accel/jerk, `np.trapz`
for area-under-curve. The instant you call `np.asarray(...)` on `ProvFloat`s, NumPy
discards the subclass and stores raw `float64` — the stamp evaporates **silently**, dunder
propagation never fires, and *no one had to type `float(x)`*. This is the exact "laundry
utility" failure round 1 named as risk #1, merely relocated from `.magnitude` to
`np.asarray`, and it triggers precisely where the safety-critical derivative math lives. So
the guarantee is scalar-only theater unless the honest path is extended to a
provenance-carrying array (child idea #1); without that extension, the pillar protects the
one place provenance *doesn't* matter (hand arithmetic on scalars) and abandons the place
it does. A secondary, milder tension: lattice-`min` is correct but **blunt** — it reports
that *a* weak input touched the result, not *which region or derivative order*, so it can
over-pessimize an aggregate and discards the Pillar-C granularity (child idea #2 restores
it).

## First concrete step a builder would take

Write `provfloat.py` (~40 lines) and its proof test, *before any parser or NumPy*:

1. `class Provenance(IntEnum): EXTRAPOLATED=0; INFERRED=1; MEASURED=2` — so `min()` **is**
   the lattice join.
2. `class ProvFloat(float)` storing `_prov`; override the arithmetic dunders to return
   `ProvFloat(result, min(stamps))`, treating any non-`ProvFloat` operand as `MEASURED`
   (exact constant); override `__repr__`/`__str__`/`__format__` to append `f" [{prov.name}]"`.
3. Back it with a trivial `ConstantProfile` whose `lift_at(deg)` returns
   `ProvFloat(0.0, INFERRED)` — no real interpolation needed to prove the boundary.
4. Write the conformance seed test asserting: `(measured + extrapolated).provenance == EXTRAPOLATED`;
   `repr(x)` and `f"{x:.3f}"` contain the tag; `float(x)` is the *only* operation that drops
   it; and a `grep`/AST test that **fails CI** if `float(` appears anywhere under
   `analysis/`.

That single file + test is the conformance anchor the whole α-pillar grows from, and it is
buildable in the "one hour, no team" budget the source frame demanded.

## Child ideas (variations · hybrids · unlocks)

1. **`ProvArray` — provenance-carrying `ndarray` (the load-bearing unlock).** Subclass
   `np.ndarray` via `__array_ufunc__`/`__array_wrap__`, carrying a parallel `uint8` stamp
   array of identical shape; ufuncs propagate element-wise lattice-min and reductions
   (`sum`, `trapz`, `gradient`) fold the stamps exactly as they fold the values. This
   directly closes the #1 risk above — the 720-sample curve *and* its derivatives keep
   per-sample provenance through real math — and demotes `ProvFloat` to merely the 0-d case.

2. **Element stamp = `(provenance, region_id)` → re-converge with Pillar C / B4.3 (hybrid).**
   Carry not just a provenance level but the physical event that dominated it
   (`SEAT_RAMP | FLANK | NOSE | LASH | EXTRAP`). The join keeps the weakest provenance *and*
   records which region drove it, so a poisoned PTV result can say "`EXTRAPOLATED`,
   dominated by `NOSE`" — restoring the per-region granularity the blunt `min()` loses and
   anchoring it to the safety-critical events runner-up **B4.3** named.

3. **Display-as-audit conformance corpus (unlock toward ζ / B4.6).** Because the stamp is
   *always* in `__repr__`/`__format__`, the adversarial conformance suite can be built purely
   from rendered output: golden-file snapshots of every report cell and plot label that
   **fail** if a known-`EXTRAPOLATED` quantity renders without its tag, or if any cell renders
   a bare `float`. Laundering detection becomes a string-diff test instead of reviewer
   vigilance — the display channel doubles as the audit surface for free.

4. **`float(x)` as recorded custody transfer (hybrid with B1.5).** Replace the bare cast with
   an explicit `release(x, reason=...)` helper that logs `(value, prov, caller, reason)` to a
   custody ledger before returning the naked float. The default path (ProvFloat everywhere)
   stays zero-cost; only the *escape* costs a justification string and an audit row, so the
   rare legitimate strip (handing a number to a third-party solver) still names who took
   custody — folding the δ accountability cluster onto the single point where the guarantee
   leaks.

5. **Two-axis stamp: provenance ⟂ derivative-fitness (unlock wiring PICK 3 → PICK 2).** Widen
   `_prov` to a packed pair `(source, fitness)` — source on `MEASURED>INFERRED>EXTRAPOLATED`,
   fitness on supported-derivative-order — each joined independently by `min` through the
   dunders. A value can then say "`MEASURED` source but velocity-grade fitness only," letting
   PICK 2's derivative-capability gate read fitness straight off the value object instead of
   issuing a separate query, and reviving the round-1 Pillar-A "2-axis lattice (provenance ⟂
   numeric-quality)" unlock.
