# Camshaft Analysis Software Specification

## Reference Camshaft

Based on Web Cam 81-651 (Yamaha WR250R DOHC 4V)

### Cam Card Data

- Valve lash: 0.006" intake, 0.008" exhaust (cold)
- Valve lift: 0.360" / 9.14 mm intake and exhaust
- Advertised duration: 262° intake, 270° exhaust
- Duration @ 0.050": 238° intake, 246° exhaust
- Lobe centers: 109.5° intake, 104.5° exhaust, 107° overall
- Intake opens: 9.5° BTDC
- Intake closes: 48.5° ABDC
- Exhaust opens: 47.5° BBDC
- Exhaust closes: 18.5° ATDC

---

# Goal

Build software that accepts a cam card, engine geometry, and optional measured cam/lift data and produces a complete analysis of:

- Timing events
- Lift curves
- Overlap
- Dynamic compression ratio
- Piston-to-valve clearance
- Valve acceleration and jerk
- Valve spring safety
- Cam timing sensitivity

---

# Core Modules

## 1. Cam Card Parser

### Inputs

```yaml
engine:
  bore_mm:
  stroke_mm:
  rod_length_mm:
  compression_ratio_static:
  deck_clearance_mm:
  gasket_bore_mm:
  gasket_thickness_mm:
  piston_dish_cc:
  chamber_cc:

camshaft:
  intake:
    valve_lift_in:
    advertised_duration_deg:
    duration_050_deg:
    lobe_center_deg_atdc:
    opens_050_deg:
    closes_050_deg:
    lash_in:

  exhaust:
    valve_lift_in:
    advertised_duration_deg:
    duration_050_deg:
    lobe_center_deg_btdc:
    opens_050_deg:
    closes_050_deg:
    lash_in:
```

### Features

- Manual entry
- CSV import
- Cam card PDF parsing
- Image OCR support

---

## 2. Timing Analysis

### Outputs

- Intake centerline
- Exhaust centerline
- Lobe separation angle
- Overlap at advertised timing
- Overlap at 0.050"
- Intake closing angle
- Exhaust opening angle
- Full 720° timing map
- Cam advance/retard effects

### Example Results

```text
Overlap @ 0.050": 28°
Intake centerline: 109.5° ATDC
Exhaust centerline: 104.5° BTDC
LSA: 107°
```

---

## 3. Lift Curve Reconstruction

### Inputs

- Peak lift
- Advertised duration
- Duration @ 0.050"
- Lobe center
- Lash
- Measured lift data (optional)

### Outputs

- Valve lift vs crank angle
- Velocity
- Acceleration
- Jerk
- Area under curve
- Lift at overlap TDC
- Lift in piston chase zones

### Data Sources

- Dial indicator measurements
- Degree wheel measurements
- Cam Doctor exports
- Lobe coordinate measurements

---

## 4. Dynamic Compression Ratio

### Inputs

- Static compression ratio
- Bore
- Stroke
- Rod length
- Intake closing angle

### Outputs

- Effective stroke
- Dynamic compression ratio
- Trapped compression ratio
- Cranking pressure estimate
- Sensitivity to cam timing changes

### Notes

Use seat timing and low-lift closing estimates rather than only 0.050" timing.

---

## 5. Piston-to-Valve Clearance

### Inputs

- Crank geometry
- Valve lift curves
- Valve angle
- Valve diameter
- Pocket geometry
- Deck height
- Head gasket thickness
- Cam timing offsets
- Lash

### Outputs

- Minimum intake clearance
- Minimum exhaust clearance
- Crank angle of minimum clearance
- Safety margin

### Safety Thresholds

- Intake: 0.050" minimum
- Exhaust: 0.080" minimum

---

## 6. Valve Spring / Retainer Analysis

### Inputs

- Installed height
- Open height
- Spring rate
- Coil bind height
- Retainer-to-guide clearance
- Valve mass
- Retainer mass
- Keeper mass
- Rocker/follower mass
- Maximum RPM

### Outputs

- Coil bind margin
- Retainer-to-guide margin
- Seat pressure
- Open pressure
- Float risk estimate
- Recommended maximum RPM

### Safety Checks

- Minimum retainer-to-guide clearance: 0.030"
- Minimum spring coil clearance: 0.015"

---

## 7. Cam Install Sensitivity Analysis

### Variables

- Intake advance/retard
- Exhaust advance/retard
- Cam chain indexing error
- Adjustable cam gear offsets
- Lash variation
- Deck height variation
- Head gasket thickness variation

### Outputs

- DCR changes
- Overlap changes
- PTV changes
- Torque bias estimates
- Safe/unsafe operating regions

---

## 8. Report Generator

### Formats

- HTML
- PDF
- Markdown

### Contents

- Cam card summary
- Timing diagram
- Valve lift plots
- Overlap diagrams
- DCR calculations
- PTV clearance plots
- Spring analysis
- Installation checklist
- Warning summary

---

# Recommended Development Order

1. Cam card parser
2. Timing event calculator
3. Lift curve approximation
4. Dynamic compression calculator
5. Cam timing sensitivity
6. Measured lift import
7. Piston-to-valve model
8. Valve spring dynamics

---

# Design Philosophy

A cam card alone is sufficient for:

- Timing analysis
- Overlap calculations
- Approximate DCR calculations
- Approximate lift reconstruction

A complete analysis requires:

- Measured lift data
- Engine geometry
- Piston geometry
- Valve geometry
- Spring specifications

The software should explicitly distinguish between inferred values and measured values so users understand confidence levels in every calculation.
