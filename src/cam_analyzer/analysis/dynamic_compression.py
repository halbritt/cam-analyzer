"""Dynamic compression ratio — a source-blind consumer of CamProfile.

DCR is driven by the intake-closing angle, which depends on the low-lift / seat
region — exactly the region a cam-card approximation *fabricates*. So DCR must
read each Quantity's provenance and refuse (or loudly downgrade) when the closing
estimate rests on EXTRAPOLATED lift (D006/D009).
"""

from __future__ import annotations

from cam_analyzer.profile import CamProfile
from cam_analyzer.quantity import Quantity


def dynamic_compression_ratio(
    intake: CamProfile,
    static_cr: float,
    bore_mm: float,
    stroke_mm: float,
    rod_length_mm: float,
) -> Quantity:
    """Effective-stroke DCR from the intake-closing angle.

    Source-agnostic by construction; honesty comes from the provenance of the
    closing-angle lift the profile returns, not from inspecting the source.
    """
    raise NotImplementedError(
        "derive intake close from intake.events_at_lift(seat); compute effective "
        "stroke and DCR; provenance joins the closing-lift provenance — D006/D009"
    )
