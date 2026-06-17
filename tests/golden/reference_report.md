# WR250R reference (Web Cam 81-651)

## Profile summary
- Intake max lift: 0.360 inch [valve_side, EXTRAPOLATED]
- Exhaust max lift: 0.360 inch [valve_side, EXTRAPOLATED]
- Intake area under curve: 62.401 inch_deg [valve_side, EXTRAPOLATED]
- Exhaust area under curve: 64.486 inch_deg [valve_side, EXTRAPOLATED]

## Lift threshold durations
| Lift | Intake duration | Exhaust duration |
|---|---:|---:|
| 0.001 in | 258.118 deg | 266.147 deg |
| 0.006 in | 254.358 deg | 262.414 deg |
| 0.020 in | 249.023 deg | 257.115 deg |
| 0.050 in | 238.000 deg | 246.000 deg |
| 0.100 in | 214.580 deg | 221.793 deg |
| 0.200 in | 168.295 deg | 173.952 deg |

## Profile quality warnings
- intake: WARNING underconstrained_reconstruction - Cam-card reconstruction is model-derived; replace with measured lift data before using derivative-sensitive conclusions.
- intake: WARNING implausibly_symmetric_lobe - Opening and closing flanks are nearly mirror-symmetric; the cam card does not constrain real asymmetric flank behavior.
- intake: WARNING long_high_lift_dwell - Duration above 98% of peak lift is 61.5 crank degrees; treat the plateau as a motion-law assumption, not measured dwell.
- intake: INFO model_derived_derivatives - Velocity, acceleration, and jerk are derivatives of the cam-card motion law, not measured valvetrain data.
- intake: WARNING excessive_model_acceleration - Model acceleration reaches 0.001333 in/deg^2; inspect the SVAJ stack before trusting the reconstruction.
- exhaust: WARNING underconstrained_reconstruction - Cam-card reconstruction is model-derived; replace with measured lift data before using derivative-sensitive conclusions.
- exhaust: WARNING implausibly_symmetric_lobe - Opening and closing flanks are nearly mirror-symmetric; the cam card does not constrain real asymmetric flank behavior.
- exhaust: WARNING long_high_lift_dwell - Duration above 98% of peak lift is 63.6 crank degrees; treat the plateau as a motion-law assumption, not measured dwell.
- exhaust: INFO model_derived_derivatives - Velocity, acceleration, and jerk are derivatives of the cam-card motion law, not measured valvetrain data.
- exhaust: WARNING excessive_model_acceleration - Model acceleration reaches 0.001355 in/deg^2; inspect the SVAJ stack before trusting the reconstruction.

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
