"""Analysis layer — the eight source-blind consumers.

THE RULE (C1/D001): modules in this package import only ``cam_analyzer.profile``
and ``cam_analyzer.quantity`` (plus stdlib / numerics). They must **never** import
``cam_analyzer.sources`` or any source-specific type. A consumer gets numbers only
by calling the CamProfile C5 surface, and only as Quantity/Angle values.

This rule is enforced by tests/test_architecture_boundary.py — not by review.
"""
