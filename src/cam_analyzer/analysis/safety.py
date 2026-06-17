"""Shared safety threshold policy definitions."""

from __future__ import annotations

from dataclasses import dataclass

from cam_analyzer.quantity import Inch, Quantity, measured


@dataclass(frozen=True, slots=True)
class ThresholdPolicy:
    name: str
    minimum: Quantity[Inch]
    owner: str


# Spec-required minimum clearances from Camshaft_Analysis_Spec.md. These are
# authoritative spec data, so they carry MEASURED provenance — this module is the
# spec-policy authority and the one place outside cam_analyzer.sources allowed to
# mint MEASURED (see the measured_confined_to_sources conformance trap).
PTV_INTAKE_POLICY = ThresholdPolicy(
    name="piston-to-valve intake minimum",
    minimum=measured(0.050, Inch, "valve_side"),
    owner="Camshaft_Analysis_Spec.md",
)
PTV_EXHAUST_POLICY = ThresholdPolicy(
    name="piston-to-valve exhaust minimum",
    minimum=measured(0.080, Inch, "valve_side"),
    owner="Camshaft_Analysis_Spec.md",
)
RETAINER_TO_GUIDE_POLICY = ThresholdPolicy(
    name="retainer-to-guide minimum",
    minimum=measured(0.030, Inch, "valve_side"),
    owner="Camshaft_Analysis_Spec.md",
)
SPRING_COIL_POLICY = ThresholdPolicy(
    name="spring coil clearance minimum",
    minimum=measured(0.015, Inch, "valve_side"),
    owner="Camshaft_Analysis_Spec.md",
)
