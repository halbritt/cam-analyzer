# Tutorial — Milestone 1: a cam card in, CamProfiles out

The smallest end-to-end path the architecture must support (C2/D003):

```python
from cam_analyzer.quantity import Angle
from cam_analyzer.sources.cam_card import CamCard, profiles_from_cam_card

card = CamCard.wr250r_reference()        # the Web Cam 81-651 reference numbers
profiles = profiles_from_cam_card(card)  # intake and exhaust CamProfile objects

lift = profiles.intake.lift_at(Angle.crank(109.5))  # -> ProvFloat
print(float(lift), lift.unit, lift.frame, lift.provenance)
```

Note what the tutorial demonstrates, by construction:

- `lift_at` returns a `ProvFloat`, never a bare `float` (D004/D012).
- The value's provenance is `INFERRED`/`EXTRAPOLATED`, not `MEASURED` — a cam-card
  approximation cannot claim measured support (D002/D006).
- The profile objects satisfy the full C5 surface; later, a
  `MeasuredValveLiftProfile` swaps in with no change to any analysis that consumed
  it (C4) — though the *answers* may change at cliff functions (D009).
