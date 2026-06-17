"""Shared safety threshold policy definitions."""

from __future__ import annotations

from dataclasses import dataclass

from cam_analyzer.quantity import ProvFloat, Provenance


@dataclass(frozen=True, slots=True)
class ThresholdPolicy:
    name: str
    minimum: ProvFloat
    owner: str


PTV_INTAKE_POLICY = ThresholdPolicy(
    name="piston-to-valve intake minimum",
    minimum=ProvFloat(0.050, "inch", "valve_side", Provenance.MEASURED),
    owner="Camshaft_Analysis_Spec.md",
)
PTV_EXHAUST_POLICY = ThresholdPolicy(
    name="piston-to-valve exhaust minimum",
    minimum=ProvFloat(0.080, "inch", "valve_side", Provenance.MEASURED),
    owner="Camshaft_Analysis_Spec.md",
)
RETAINER_TO_GUIDE_POLICY = ThresholdPolicy(
    name="retainer-to-guide minimum",
    minimum=ProvFloat(0.030, "inch", "valve_side", Provenance.MEASURED),
    owner="Camshaft_Analysis_Spec.md",
)
SPRING_COIL_POLICY = ThresholdPolicy(
    name="spring coil clearance minimum",
    minimum=ProvFloat(0.015, "inch", "valve_side", Provenance.MEASURED),
    owner="Camshaft_Analysis_Spec.md",
)
