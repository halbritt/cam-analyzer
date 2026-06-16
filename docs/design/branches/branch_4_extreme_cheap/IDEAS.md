# Branch: extreme_cheap — Divergent Ideas

author: diverger-author-002

**Frame:** No money, no team, one hour. What is the crudest version that still
does the load-bearing thing — namely, that every downstream module talks to a
source-agnostic `CamProfile`, measured values are distinguishable from inferred
ones, and a crude cam-card profile can later be swapped for measured lift data
without touching analysis code?

---

## Idea 1 — The interface is a file format, not a class

A `CamProfile` is a 720-row text file: one lift value per crank degree, plus a
header line marking each value `measured` or `inferred`. Every "source" is just
a tiny script that emits this file (one from the cam card, one from a dial-gauge
log). Every analysis module only opens and reads the file. The source-agnostic
seam lives in the format on disk, so there are no base classes, no imports
between source and consumer, and "swap the source" means "regenerate the file."

## Idea 2 — A half-sine lobe from four numbers

`CamCardApproxProfile` is one function: feed it peak lift, duration, lobe center,
and lash, and it returns `peak * sin²` shaped over the duration window, zero
elsewhere. It is continuous, integrable, and differentiable on the spot. One
hour from cam card to a queryable lift curve, no fitting, no data points — the
whole milestone-1 path (card → profile) is a dozen lines.

## Idea 3 — Borrow one published lift shape and rescale it

Steal a single normalized 4-valve lift curve (≈30 points, lift fraction vs
duration fraction) from any published cam plot, hardcode it once, and stretch it
to each cam's peak lift and duration. One canonical "shape" serves every cam.
No lobe geometry, no modeling — just multiply a stored template. Measured data
later replaces the template for that one cam; everything downstream is unchanged.

## Idea 4 — Derivatives are a free universal wrapper

No profile implements `velocity_at`, `acceleration_at`, or `jerk_at`. Each
source supplies only `lift_at`. A single shared finite-difference helper wraps
*any* profile and derives the other three by central differences on demand. Four
of the eight interface methods collapse into one obligation, so a new source
costs exactly one function to be a complete `CamProfile`.

## Idea 5 — Provenance rides inside the value

There is no profile-level confidence metadata. Every sample a profile returns is
a tuple `(lift, "measured" | "inferred", confidence_0_to_1)`. Analysis code that
wants a bare float must unwrap the tag explicitly, so it can never silently treat
an inferred number as measured. The measured-vs-inferred requirement becomes a
property of every single value for free, with no extra structure.

## Idea 6 — The architectural rule is a three-line grep

The load-bearing guarantee — "no analysis module depends on a cam card, parser,
CSV, or source" — is enforced by a grep in a pre-commit hook: fail if any file
under `analysis/` imports anything from `sources/`. No dependency injection, no
ports-and-adapters framework, no abstract registry. The boundary is policed by a
one-line search that anyone can read, and it fails loudly the moment leakage
appears.
