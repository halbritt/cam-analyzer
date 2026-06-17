# DCR report — WR250R + Web Cam 81-651 + 13.5:1 piston

**Build:** Yamaha WR250R (DOHC 4-valve) · Web Cam 81-651 grind · **13.5:1 piston (in hand)**
**Engine geometry:** bore 77.0 mm · stroke 53.6 mm · rod 96.9 mm · **static CR 13.5**
**Generated:** 2026-06-17 from [`examples/wr250r-webcam-81651-13.5piston.json`](../../examples/wr250r-webcam-81651-13.5piston.json) via `cam-analyze`
**Headline:** **DCR ≈ 11.882** (`INFERRED`), intake-valve closing 228.5° crank (48.5° ABDC).

> **Why 13.5, and why this beats the old fixture.** The static CR here is a
> *measured spec of a physical piston the owner is holding* — a real source —
> not the unsourced `12.8` the `--reference` fixture hardcodes (that defect is
> [issue #17](https://github.com/halbritt/cam-analyzer/issues/17); stock WR250R
> is 11.8:1). The cam helps the cause: late intake closing bleeds ~1.6 points off
> static, so 13.5 static lands at **11.88 dynamic**, not 13.5.

> **This report does not yet answer the two questions that matter.** "Will the
> piston survive?" and "how much material must I remove?" are exactly the
> sections the tool refuses (`UNDECIDABLE FROM CAM CARD`) or cannot model:
> - **Detonation survival** needs a fuel/octane/knock-margin verdict the tool
>   does not produce — DCR 11.88 is *high*, but the WR250R already runs 11.8:1
>   *static* stock on pump premium, so the V8 "8.5 DCR ceiling" lore does not
>   transfer; the honest unknown is the +1.7-point static jump vs your fuel.
> - **Piston-to-valve** is `UNDECIDABLE` because the cam card carries no measured
>   clearance — see [RFC 0003](../rfc/0003-piston-to-valve-clearance-model.md).
>   **The piston vendor explicitly warns "MAKE SURE YOU CHECK P2V"** — this
>   high-comp piston is not a drop-in; P2V is the gating (binary, catastrophic)
>   failure mode, and a clay check at the intended cam timing is mandatory before
>   it runs. The tool's `UNDECIDABLE` here agrees with the vendor: go measure it.
> - **"How much dome to cut"** has no model at all (no chamber-volume math) — see
>   [RFC 0002](../rfc/0002-static-cr-chamber-volume-solver.md).

The timing/DCR numbers below are pinned for the *stock-reference* run by a golden
test (`tests/test_reference_report_golden.py`); this 13.5 build is a separate,
reproducible card.

---

# WR250R + Web Cam 81-651 + 13.5:1 piston (high-comp build)

## Profile summary
- Intake max lift: 0.360 inch [valve_side, EXTRAPOLATED]
- Exhaust max lift: 0.360 inch [valve_side, EXTRAPOLATED]
- Intake area under curve: 59.745 inch_deg [valve_side, EXTRAPOLATED]
- Exhaust area under curve: 61.860 inch_deg [valve_side, EXTRAPOLATED]

## Timing
- Intake centerline: 109.500 deg [crank]
- Exhaust centerline: 615.500 deg [crank]
- Lobe separation angle: 107.000 deg [crank]
- Overlap at 0.050 inch [valve_side, INFERRED]: 28.000 deg [crank]; intake events 228.500 deg [crank], 710.500 deg [crank]; exhaust events 18.500 deg [crank], 492.500 deg [crank]

## Dynamic compression
- Dynamic compression ratio: 11.882 ratio [dimensionless, INFERRED]; intake closing 228.500 deg [crank]

## Piston-to-valve
- intake: UNDECIDABLE FROM CAM CARD - Cam card evidence is insufficient for a physical piston-to-valve clearance verdict without measured clearance data.
- exhaust: UNDECIDABLE FROM CAM CARD - Cam card evidence is insufficient for a physical piston-to-valve clearance verdict without measured clearance data.

## Spring safety
- Spring safety: UNDECIDABLE FROM CAM CARD - Cam card evidence and missing spring measurements are insufficient for a valve spring safety verdict.

---

## CR sensitivity (this cam, intake closing 48.5° ABDC)

| static CR | dynamic CR | clearance volume Vc | note |
|---|---|---|---|
| 11.8 | 10.402 | 23.11 cc | stock WR250R |
| 12.8 | 11.272 | 21.15 cc | `--reference` fixture (issue #17) |
| **13.5** | **11.882** | **19.97 cc** | **this piston** |

Swept volume Vd = 249.60 cc. Dropping this piston back down means *adding*
clearance volume (= removing dome): 13.5→12.8 needs +1.19 cc, 13.5→11.8 needs
+3.14 cc. Those are the [RFC 0002](../rfc/0002-static-cr-chamber-volume-solver.md)
numbers the tool will compute once you CC the head — it cannot yet.

## Reproduce

```bash
cam-analyze examples/wr250r-webcam-81651-13.5piston.json
```
