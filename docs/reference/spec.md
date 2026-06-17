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

Milestone 1 fits the published card with `PolynomialMotionLawCamCardOperator`,
exposed through `profiles_from_cam_card()`. The operator is a constrained
piecewise-quintic motion law, not a sine-power visual fit. It builds finite lash
ramps, opening/closing flanks, and a high-lift dwell region from quintic Hermite
segments so lift, velocity, and acceleration are continuous and jerk is finite.

The published cam-card events are hard constraints. The WR250R Web Cam 81-651
profile must cross 0.050 in exactly at:

| Event | Crank angle |
|---|---:|
| Intake opens @0.050 | 9.5° BTDC |
| Intake closes @0.050 | 48.5° ABDC |
| Exhaust opens @0.050 | 47.5° BBDC |
| Exhaust closes @0.050 | 18.5° ATDC |

The generated curve also preserves the advertised duration and peak lift. This
is still a cam-card approximation: generated values are inferred or
extrapolated, never measured. The SVAJ stack and quality warnings intentionally
call out symmetric flanks, model-derived derivatives, and high-lift dwell that
are motion-law assumptions rather than observed lobe geometry.
