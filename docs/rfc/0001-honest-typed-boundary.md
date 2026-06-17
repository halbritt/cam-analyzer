# RFC 0001 — The Honest Typed Boundary

- **Status:** Draft / Proposed
- **Date:** 2026-06-17
- **Addresses:** [#5](https://github.com/halbritt/cam-analyzer/issues/5) (typed boundary enforces C3/C6 by convention, not mechanism), [#6](https://github.com/halbritt/cam-analyzer/issues/6) (Protocol pitfalls), [#8](https://github.com/halbritt/cam-analyzer/issues/8) (cleanup)
- **Resolves:** the round-2 *"ergonomics-as-integrity"* open problem from `docs/design/round2/IDEATION_SYNTHESIS.md` (flagged independently by all three frontier models)
- **Provenance:** produced via a `/adhd` divergent-ideation run — 5 isolated cognitive frames (regulator, attacker, remove-the-assumption, hardware/dimensional, biology) × 6 ideas, converged, then the top 3 clusters deepened.

---

## 1. Summary

cam-analyzer's whole value proposition is that an analysis can *trust* a number because the boundary tells it whether the number was **measured** or **inferred**, and in **what unit/frame**. Today those guarantees (invariants **C3** measured≠inferred and **C6** unambiguous units/frames) are upheld by *convention* — docstrings that say "unconstructable" / "a type error" about things the code does not actually prevent. This RFC makes them **mechanism**:

1. **Sealed construction** — provenance is *conferred by acquisition*, never passed as an argument. `MEASURED` is unconstructable outside the source layer.
2. **Phantom-typed units & frames** — `Quantity[Unit]` and `Angle[Frame]` carry unit/frame in the *type*, so mm-as-inch and cam-as-crank are **mypy errors**, not runtime hope.
3. **Ergonomic inversion** — there is no bare `.magnitude`; the honest typed path is *shorter* than the one raw-float exit (`unsafe_strip(reason=…)`), which is greppable, lint-failed, and audited.

A enforces honesty at **origination**, B at **propagation**, D removes the incentive to **bypass**. None requires crypto, a metaclass, or a runtime DAG — it's ordinary Python 3.12 + mypy + one small ruff rule.

## 2. Motivation

The code review of the Milestone-1 implementation found the boundary's central claims overstated (issue #5):

- `Quantity(x, "inch", "valve_side", Provenance.MEASURED)` **fabricates** a measured reading from nothing; reconstructing a value **raises** its provenance. The min-join "can only descend / relabeling is unconstructable" rule only governs `+`/`-`, not construction.
- `unit` is a `Literal[str]` *label*, so a millimetre magnitude tagged `"inch"` type-checks fine — C6 unenforced.
- `Angle` is a single dataclass with a runtime `frame` field, so a cam angle passed where a crank angle is required is **not** a type error.

And the round-2 synthesis already named the deeper trap: a provenance-carrying value layer only stays honest if the **honest path is strictly more ergonomic than reaching for the raw float** — otherwise developers strip the metadata (`q.magnitude * 25.4` and re-wrap) and the guarantees evaporate. All three frontier models independently flagged this as *the* load-bearing risk.

**Goal:** make fabrication / mislabeling structurally impossible (or loud and traceable), while making the honest path the path of least resistance.

### Non-goals

- Cryptographic attestation of readings (HMAC receipts, signed provenance). Rejected — see §7; this is a single-process offline analysis library whose threat is *developer mistakes*, not a malicious runtime forging values in memory.
- A full integer-exponent dimensional algebra. Rejected as premature — cam-analyzer has a handful of dimensions (length, angle, a couple of rates); named tags + a few explicit conversions are far less machinery and read better in tracebacks.
- Changing the analysis math or the `CamProfile` query surface (C5) — this RFC is about the *value layer* those queries return.

## 3. Design

### Pillar A — Sealed construction (origination): provenance is conferred, not declared

`Quantity.__init__` refuses any caller lacking a module-private *mint key*. The only ways to obtain a `Quantity` are (1) **source factories** in `cam_analyzer.sources` that stamp provenance themselves (acquisition confers it), and (2) **combinators** (arithmetic/transform) that copy-and-**descend** provenance from their operands via the existing `Provenance` min-join. No public surface anywhere accepts a `provenance=` argument.

```python
_MINT: Final = object()  # module-private; never exported

@dataclass(frozen=True, slots=True)
class Quantity:
    _canon: float                 # canonical magnitude (SI base) — see Pillar B
    provenance: Provenance
    _key: object = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if self._key is not _MINT:
            raise TypeError("Quantity is sealed; mint via a source factory")

    @classmethod
    def _mint(cls, canon: float, prov: Provenance) -> "Quantity":
        return cls(canon, prov, _MINT)

    def _combine(self, other: "Quantity", canon: float) -> "Quantity":
        return Quantity._mint(canon, Provenance.join(self.provenance, other.provenance))  # descend
```

```python
# cam_analyzer/sources/ — the ONLY place a provenance literal appears:
class MeasuredLift:
    @staticmethod
    def from_dial_indicator(mm_value: float) -> Quantity:
        return Quantity._mint(mm_value * Mm.to_si, Provenance.MEASURED)   # acquisition confers MEASURED

class CamCardApprox:
    @staticmethod
    def declare(value: float, unit: Unit, *, extrapolated: bool = False) -> Quantity:
        prov = Provenance.EXTRAPOLATED if extrapolated else Provenance.INFERRED
        return Quantity._mint(value * unit.to_si, prov)
```

"Fabricate `MEASURED`" now requires forging `_MINT` (not importable); "raise provenance by reconstructing" requires a constructor that accepts `provenance` (none exists publicly). This makes **C3 a property of the API surface**, not a rule reviewers must remember.

**Provenance-descent semantics (Cluster C):** every combinator returns `Provenance.join(...)` of its inputs and *no public signature returns a provenance higher than any input*. "Relabel inferred→measured" is unconstructable because **no function in the module produces that arrow.**

### Pillar B — Phantom-typed units & frames (propagation): C6 at compile time

Make unit and frame **type parameters**, not runtime strings. Tags are empty marker classes that exist only at the type level; the runtime stores **one canonical magnitude** (SI base) so arithmetic is plain float math. mypy then enforces that you can only add like-with-like and can only cross frames through an explicit witness.

```python
@final
class Mm: to_si = 0.001
@final
class Inch: to_si = 0.0254
class Crank: ...
class Cam: ...

U = TypeVar("U"); F = TypeVar("F"); A = TypeVar("A"); B = TypeVar("B")

@dataclass(frozen=True, slots=True)
class Quantity(Generic[U]):
    _canon: float                 # canonical (SI); the phantom U is the unit
    provenance: Provenance
    def __add__(self, other: "Quantity[U]") -> "Quantity[U]": ...   # same-U only → mismatch is a mypy error

def mm(x: float) -> Quantity[Mm]:     return Quantity._mint(x * Mm.to_si,   Provenance.MEASURED)
def inch(x: float) -> Quantity[Inch]: return Quantity._mint(x * Inch.to_si, Provenance.MEASURED)

@dataclass(frozen=True, slots=True)
class Angle(Generic[F]):
    degrees: float

@dataclass(frozen=True)
class Transform(Generic[A, B]):            # the witness that records a sanctioned frame change
    rocker_ratio: float
    def __call__(self, a: "Angle[A]") -> "Angle[B]": ...

def to_crank(a: Angle[Cam], t: Transform[Cam, Crank]) -> Angle[Crank]: ...
def lift_at(theta: Angle[Crank]) -> Quantity[Inch]: ...
```

**What mypy *can* enforce:** `mm(5) + inch(1)` is an error; `lift_at(some_cam_angle)` is an error; a frame crossing is only legal through a `Transform` value obtained from the kinematic model. **What it *cannot*:** synthesize dimensional algebra (no auto `Quantity[Mm] / Quantity[Sec] -> Quantity[MmPerSec]` without hand-written overloads), and it cannot stop a *direct* `Quantity(...)` from minting a wrong-tagged value — that **origination gap is exactly what Pillar A's seal closes.** This is why A and B are one design, not two.

### Pillar D — Ergonomic inversion (bypass): honest is shorter than dishonest

There is **no `.magnitude`**. The value stores one private canonical magnitude; the public exits are *typed* and one-call:

```python
class Quantity(Generic[U]):
    # honest, short exits:
    @property
    def inch(self) -> float: return self._canon / Inch.to_si      # for I/O / rendering only
    @property
    def mm(self) -> float:   return self._canon / Mm.to_si
    def to(self, unit: type[U2]) -> "Quantity[U2]": ...           # Quantity → Quantity, keeps provenance
    def __format__(self, spec: str) -> str: ...                   # f"{q:.3f inch}" with no float grab

    # the one ugly door (long path):
    def unsafe_strip(self, reason: str) -> float:
        if not reason.strip():
            raise ValueError("unsafe_strip requires a non-empty reason")
        _audit.warning("unsafe_strip canon=%s reason=%r at %s", self._canon, reason, _caller())
        return self._canon
```

Keystroke math is the proof: honest `q.inch` / `q.to(Mm)` is ~7 chars and stays typed; dishonest `q.unsafe_strip("…")` is 20+ chars, needs a justification, logs an audit record, and **fails lint** unless allow-listed. The dishonest path is literally more work and visibly marked.

**Enforcement wiring (least-friction):** a ~40-line ruff/flake8 AST rule **`CAM001`** flags every `unsafe_strip` call; an `allowlist.toml` keyed by `file:line:reason` (with a reaper test that fails on stale entries) gates CI. A second rule **`CAM002`** catches the launder-through-the-legit-door pattern — feeding a boundary accessor result straight back into a constructor (`Quantity(q.inch, …)` round-trips).

## 4. How the three compose

| Invariant | Enforced at | By |
|---|---|---|
| C3 — measured≠inferred, no fabrication / no raise | **origination** | Pillar A (sealed mint) + C (descent semantics) |
| C6 — units/frames unambiguous | **propagation** | Pillar B (phantom types), mypy `--strict` |
| C6 — origination of a wrong tag | **origination** | Pillar A seal (smart constructors are the only mint) |
| Round-2 ergonomics / un-strippable | **bypass** | Pillar D (no `.magnitude`, `CAM001`/`CAM002`, audit) |

## 5. Enforcement plan (mechanism, not review)

- `mypy --strict` in CI — proves the phantom-type propagation (Pillar B).
- `ruff` custom rules `CAM001` (`unsafe_strip` sites) and `CAM002` (accessor→constructor round-trips) + `allowlist.toml` + stale-entry reaper test (Pillar D).
- A lint/AST test that **no `Provenance.MEASURED`/`INFERRED` literal appears outside `cam_analyzer/sources/`** (moves Pillar A's invariant into CI; child idea from the deepen).
- A conformance trap that asserts **no public callable accepts a `provenance=` parameter** (`inspect.signature` sweep) and that `Quantity(...)` without the key raises — extends the existing `tests/test_conformance_traps.py` corpus (`fabricated_nose_as_measured`, `mm_labeled_as_inch`).
- Fixes #6 in passing: replace Protocol *subclassing* with `abc.ABC`/composition so a missing method fails at construction (sealed mints already push concrete profiles toward factories).

## 6. Risks & mitigations

- **Python privacy is friction, not a wall (Pillar A).** `Quantity._mint` / `_MINT` are reachable by reflection. This is honesty-by-friction: the dishonest path requires obviously-out-of-band reflection a reviewer and `CAM001`-style lint catch, instead of an innocent `provenance=` kwarg. *Mitigate:* lint the literal-provenance rule; forbid a custom `__reduce__`; override `dataclasses.replace`/pickle to route through the keyed mint. The real failure mode is a teammate "helpfully" exposing a public `Quantity.create(provenance=…)` — guard it with the signature-sweep conformance test.
- **mypy guards propagation, not origination (Pillar B).** A direct `Quantity(0.36)` mislabels silently. *Mitigate:* this is precisely what Pillar A's seal closes — that's why they ship together.
- **Incomplete typed surface re-opens the escape (Pillar D).** If `Quantity` lacks an op a dev needs (trig, `numpy`, `%` formatting), `unsafe_strip` becomes the path of least resistance and the allowlist rubber-stamps. *Mitigate:* **first step below** — audit real `.magnitude` usage to size the minimum API before rollout; add `__format__` and a `QuantityArray`/`__array_ufunc__` shim for numpy interop.

## 7. Alternatives considered (and why rejected)

- **Cryptographic receipts / HMAC-signed `MEASURED` (regulator frame), MHC-credential presentation (biology).** Elegant, but over-engineered for a single-process offline tool where values aren't crossing a trust boundary at runtime — the threat is a developer typo, not an in-memory forger. Keep crypto out; sealed mints + lint give the same practical guarantee at ~1% of the complexity.
- **Provenance as an external append-only ledger / derivation DAG queried via capability token (remove-assumption, regulator).** Strong auditability, but heavy machinery and a second object to thread everywhere. *Keep as an optional escalation* (Pillar A's `_combine` can carry a `derivation: tuple[...]` lineage for audit **without** raising provenance) if reporting later needs full chain-of-custody.
- **"Allergenic `.magnitude`" / apoptosis — accessing the float poisons sibling values (biology).** Rejected: spooky action-at-a-distance is impossible to reason about and debug. Pillar D gets the same incentive gradient with *static* lint, not runtime mutation.

## 8. Migration / first concrete steps

1. **Audit the escape surface first** — `rg -n '\.magnitude\b' --type py` and bucket uses into (a) arithmetic closed operators absorb, (b) boundary I/O `.inch`/`.mm`/`__format__` serve, (c) genuine float-only escapes (numpy/trig/format). The size of bucket (c) decides whether the inversion holds or whether numpy interop is the real first task.
2. **Write the failing conformance tests** — `Quantity(...)`-without-key raises; no public callable takes `provenance=`; `MeasuredLift.from_dial_indicator(...).provenance is MEASURED`; `(measured + inferred).provenance is INFERRED`; `mm(5) + inch(1)` is a mypy error (a `reveal_type`/`pytest-mypy` check).
3. **Land Pillar A + B together** behind the source factories (M1 `CamCardApprox.declare` already exists — reroute it through the keyed mint), keeping the runtime canonical-magnitude store.
4. **Land Pillar D + `CAM001`** and delete `.magnitude`; convert existing call sites bucket-by-bucket.

## 9. Open questions

- Generic `Quantity[U]` vs `NewType`-per-unit: the former enables same-instance polymorphic arithmetic (`__add__` unit-matching) at the cost of more typing machinery; the latter is lighter but loses operator unit-checking. Spike both on a 6-line `mypy --strict` driver before committing (deepen B's first step).
- How far to take dimensional rates (`inch_per_deg`, `…deg2`, `…deg3`) before hand-written `__mul__`/`__truediv__` overloads explode — measure, then decide length+angle+named-rates vs a real exponent vector.
- Should `derivation` lineage (audit without raising) ship in v1 or wait for the report generator to need it?

## 10. Provocation (unexplored direction)

Invert the call direction entirely: analyses don't *read* a profile, they **submit a question with a required fitness** and get a provenance-stamped `Answer | Refusal{reason, what_would_fix_it}`. `profile.answer(Query.PTV_MIN_CLEARANCE, require=MEASURED_NOSE)` makes "good enough for my question?" the *only* way to get a number and could dissolve the `.magnitude` hatch by removing the bare-float exit altogether — at the cost of a heavier query surface. Worth a future RFC if the fitness story (G5) grows.
