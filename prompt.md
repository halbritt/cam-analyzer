Design the architecture for a camshaft analysis application with early, durable cam profile abstraction.

The most important requirement is that all downstream analysis modules depend only on a `CamProfile` interface, never directly on a cam card, PDF parser, CSV format, or measured-data source.

The software should analyze automotive/motorcycle camshafts, starting with a Yamaha WR250R Web Cam 81-651 cam card, but it must be able to evolve from sparse cam-card approximations into measured valve-lift curves, Cam Doctor exports, scanned lobe profiles, and full valvetrain-dynamics models.

Define a clean domain model that separates:

- `CamCard`: sparse published timing specs
- `CamProfile`: continuous valve-lift function over crank angle
- `Valvetrain`: mechanism converting cam/lobe motion into valve motion
- `EngineGeometry`: bore, stroke, rod length, compression ratio, deck, gasket, piston geometry
- `ValveGeometry`: valve angle, diameter, pocket geometry, installed clearances
- `SpringPackage`: spring rate, installed height, coil bind, masses, retainer-guide clearance

Create a `CamProfile` interface with methods like:

- `lift_at(crank_deg)`
- `velocity_at(crank_deg)`
- `acceleration_at(crank_deg)`
- `jerk_at(crank_deg)`
- `events_at_lift(lift_in)`
- `duration_at_lift(lift_in)`
- `max_lift()`
- `area_under_curve()`

Then define multiple implementations:

- `CamCardApproxProfile`
- `MeasuredValveLiftProfile`
- `CamDoctorProfile`
- `LobeCoordinateProfile`
- `PolynomialProfile`
- `SplineProfile`
- `CompositeProfile`

Make sure the following modules consume only `CamProfile`, not source-specific data:

- timing analysis
- overlap analysis
- dynamic compression ratio
- piston-to-valve clearance
- valve spring safety
- valve acceleration / jerk analysis
- cam advance/retard sensitivity
- report generation

Include example Python type definitions or interfaces, a proposed package structure, test strategy, and architectural rules that prevent leakage of cam-card assumptions into analysis code.

The first milestone should be:

Input: cam card  
Output: generated `CamProfile`

Not:

Input: cam card  
Output: DCR

The design should explicitly distinguish measured values from inferred values, attach confidence/quality metadata to generated profiles, and make it easy to replace an approximate cam-card profile with measured lift data later without changing downstream analysis code.
