# Product Boundary (reference)

The source of truth for *what cam-analyzer computes* is the product spec at the
repository root:

- [`../../Camshaft_Analysis_Spec.md`](../../Camshaft_Analysis_Spec.md) — the eight
  analysis modules, their inputs/outputs, safety thresholds, and the recommended
  development order.
- [`../../prompt.md`](../../prompt.md) — the original architectural request (the
  `CamProfile`-boundary requirement and the Milestone-1 definition).

This page restates only the load-bearing reference numbers so they are citable
from the model docs without opening the full spec. When this page and
`Camshaft_Analysis_Spec.md` disagree, **the spec wins.**

## Reference part — Web Cam 81-651 (Yamaha WR250R, DOHC 4V)

| Spec | Intake | Exhaust |
|---|---|---|
| Valve lift | 0.360″ / 9.14 mm | 0.360″ / 9.14 mm |
| Lash (cold) | 0.006″ | 0.008″ |
| Advertised duration | 262° | 270° |
| Duration @ 0.050″ | 238° | 246° |
| Lobe center | 109.5° ATDC | 104.5° BTDC |

Lobe separation angle: **107°**. Events: IO 9.5° BTDC, IC 48.5° ABDC,
EO 47.5° BBDC, EC 18.5° ATDC.

## Safety thresholds (from the spec)

| Check | Threshold |
|---|---|
| Piston-to-valve, intake | ≥ 0.050″ |
| Piston-to-valve, exhaust | ≥ 0.080″ |
| Retainer-to-guide clearance | ≥ 0.030″ |
| Spring coil clearance | ≥ 0.015″ |

## Milestone 1

```
Input:  cam card
Output: a generated CamProfile          (NOT: cam card → DCR)
```

The first durable output is a *profile*, not an analysis result (C2). DCR, PTV,
and spring safety are downstream of, and source-blind to, that profile.

## Cam-card approximation

Milestone 1 fits the published card with `SinePowerCamCardOperator`, exposed
through `profiles_from_cam_card()`. A fixed `sin^2` half-sine cannot fit both advertised
duration and duration at 0.050 in for the reference card, so the operator uses:

```text
lift = peak * sin(pi * t / advertised_duration) ** power
```

The exponent is solved so the generated curve crosses 0.050 in at the published
0.050-duration events. This is still a cam-card approximation: generated values
are inferred or extrapolated, never measured, and unsupported low-lift, nose, or
higher-derivative queries must refuse or downgrade rather than fabricate
precision.
