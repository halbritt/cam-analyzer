# Tutorial — Milestone 1: a cam card in, a CamProfile out

> Stub. Becomes runnable once `CamCardApproxProfile` and the half-sine operator
> are implemented.

The smallest end-to-end path the architecture must support (C2/D003):

```python
from cam_analyzer.sources.cam_card import CamCard, CamCardApproxProfile

card = CamCard.wr250r_reference()        # the Web Cam 81-651 reference numbers
profile = CamCardApproxProfile(card)     # backed by one HalfSineCamCardOperator

lift = profile.lift_at(Angle.crank(360)) # -> Quantity[Lift], provenance INFERRED
print(lift.unit, lift.frame, lift.provenance)
```

Note what the tutorial will demonstrate, by construction:

- `lift_at` returns a `Quantity`, never a bare `float` (D004).
- The value's provenance is `INFERRED`/`EXTRAPOLATED`, not `MEASURED` — a cam-card
  approximation cannot claim measured support (D002/D006).
- The same `profile` object satisfies the full C5 surface; later, a
  `MeasuredValveLiftProfile` swaps in with no change to any analysis that consumed
  it (C4) — though the *answers* may change at cliff functions (D009).
