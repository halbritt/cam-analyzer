# DCR report — WR250R reference (Web Cam 81-651)

**Cam:** Web Cam 81-651, Yamaha WR250R (DOHC 4-valve)
**Engine geometry:** bore 77.0 mm · stroke 53.6 mm · rod 96.9 mm · static CR 12.8
**Generated:** 2026-06-17 by `cam-analyze --reference` (this repo's CLI)
**Headline:** **Dynamic compression ratio ≈ 11.272** (`INFERRED`), intake-valve closing at 228.5° crank.

> **What "INFERRED" means here.** The DCR is *defensible from the cam card alone*,
> not *measured*. It is computed from a lift curve reconstructed from a sparse
> card — so the boundary stamps it `INFERRED`, never launders it as `MEASURED`.
> The piston-to-valve and valve-spring sections come back **UNDECIDABLE FROM CAM
> CARD** on purpose: the card carries no clearance or spring measurements, so the
> tool refuses a PASS/FAIL rather than fabricating one. That refusal is the
> behaviour the whole architecture exists to protect.

The numbers below (LSA, centerlines, overlap, DCR) are pinned by a golden test
(`tests/test_reference_report_golden.py`) — a refactor cannot drift them silently.

---

# WR250R reference (Web Cam 81-651)

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
- Dynamic compression ratio: 11.272 ratio [dimensionless, INFERRED]; intake closing 228.500 deg [crank]

## Piston-to-valve
- intake: UNDECIDABLE FROM CAM CARD - Cam card evidence is insufficient for a physical piston-to-valve clearance verdict without measured clearance data.
- exhaust: UNDECIDABLE FROM CAM CARD - Cam card evidence is insufficient for a physical piston-to-valve clearance verdict without measured clearance data.

## Spring safety
- Spring safety: UNDECIDABLE FROM CAM CARD - Cam card evidence and missing spring measurements are insufficient for a valve spring safety verdict.

---

## Reproduce

```bash
cam-analyze --reference        # built-in Web Cam 81-651 WR250R card
# or, without installing the entry point:
PYTHONPATH=src python3 -m cam_analyzer --reference
```
