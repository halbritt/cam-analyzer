# Branch 3 — Diverge under frame: `extreme_cheap`

author: diverger-reviewer-2-001
frame: **No money, no team, one hour — what is the crudest version that still does the load-bearing thing?**
mode: DIVERGENT (generator, not critic)

Load-bearing things this round must still hold even in the crudest build:
ergonomics-as-integrity (the honest path beats bare floats), honesty-under-discontinuity
(PTV / spring-float cliff verdicts), and the option of inverted queries.

Banned obvious answers (not used below): a dataclass with a `provenance` field; a
CI grep/lint that flags `.magnitude`; a dict returning `{value, confidence}`.

---

## Idea 1 — Lossy-by-provenance floats (precision *is* the stamp)

Inferred values are quantized to coarse precision at the moment they are created
(e.g. cam-card-inferred lift snapped to 0.01", measured lift kept full). There is no
metadata object at all — the provenance lives in the surviving significant digits.

- **Crude build (1 hr):** one `infer(x)` helper that rounds to a coarse grid; measured
  data passes through untouched.
- **Load-bearing thing:** laundering is structurally impossible — you cannot recover
  digits that were thrown away, so an inferred value can never *masquerade* as a precise
  measured one, and a report visibly shows jagged inferred numbers beside crisp measured
  ones.

## Idea 2 — NaN-poison companion function

A profile is two plain lambdas: `lift(deg)` and `support(deg)`. `support` returns `1.0`
inside measured/credible range and `float('nan')` outside it. The only sanctioned read is
`lift(deg) * support(deg)`.

- **Crude build (1 hr):** two functions and a 3-line `sample()` wrapper.
- **Load-bearing thing:** IEEE-754 does the provenance propagation for free — any verdict
  computed downstream from an extrapolated region comes out `NaN`, so the report
  *cannot print a fake "safe" number*. Honesty under discontinuity costs zero
  infrastructure; the cliff value self-destructs through arithmetic.

## Idea 3 — `float` subclass: silent in math, loud on display

The returned value subclasses `float`, so it behaves as an ordinary number everywhere
(drop-in, zero ergonomic tax, no `.magnitude` accessor exists to launder because the
object *is* the magnitude). Only `__repr__` / `__format__` / `__str__` are overridden to
always emit the provenance tag.

- **Crude build (1 hr):** ~15-line `class ProvFloat(float)` overriding three dunders.
- **Load-bearing thing:** convenience and honesty are the *same object* — the moment a
  laundered EXTRAPOLATED value reaches any print, log, plot label, or report cell it
  announces itself, with nothing extra to remember to call.

## Idea 4 — Append-only audit log as the side-channel truth

Query methods return naked floats (maximally ergonomic — analysis authors learn nothing
new). Each query silently appends `(deg, value, provenance, caller_line)` to a flat
append-only file. Truth lives *out of band*.

- **Crude build (1 hr):** one decorator that writes a CSV line per call; a 20-line
  report pass that replays the log.
- **Load-bearing thing:** integrity is reconstructed post-hoc — any verdict whose input
  rows touched a non-measured region gets flagged at report time, even though the analysis
  code never saw a special type. The honest record is unfalsifiable without editing a log
  nobody's analysis code writes to.

## Idea 5 — Run-it-twice, publish only verdict-agreement

Never emit one curve. Hand-build two crude curves — earliest-plausible and
latest-plausible seat timing — and run *every* analysis on both. The only published
output per check is whether the **verdict** matches. A flip emits
`UNDECIDABLE FROM CAM CARD` instead of a number.

- **Crude build (1 hr):** wrap the existing analysis call in a 2-element loop and diff the
  two verdicts.
- **Load-bearing thing:** the cliff-function lie is killed by construction with no
  provenance machinery — bracketing the input and comparing *verdicts* (not values)
  directly answers "does swapping the source change the answer?"

## Idea 6 — Getter-less profile: one `ask(question, require)` and a refusal string

The profile object exposes exactly one method, `ask(question, require)`, dispatched by a
flat `if/elif` over a hand-written question table. If the required fitness isn't met it
returns the literal string `"REFUSED: need measured nose data"` (or what would fix it).
There are no `lift_at` / `velocity_at` getters — they are physically deleted.

- **Crude build (1 hr):** one method, a dict of ~8 canned questions, refusal strings.
- **Load-bearing thing:** the bare-float exit *does not exist* — there is no attribute or
  getter to drop to, so laundering has nowhere to go, and refusal is a first-class,
  unmissable result rather than a silently-fabricated value.
