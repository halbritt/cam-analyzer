"""cam-analyzer — camshaft analysis around a source-agnostic CamProfile boundary.

Layers (dependency flows inward; analysis never imports sources — C1/D001):

    sources/      produce a CamProfile from a cam card, measured lift, etc.
    profile/      the CamProfile port + canonical model + Quantity value layer
    analysis/     the eight source-blind consumers
    conformance/  the frozen adversary corpus that keeps the boundary honest

See ARCHITECTURE.md and docs/reference/ubiquitous-language.md. This package is
currently a skeleton: the value objects (quantity, provenance) are real; the
numerics raise NotImplementedError with the invariant they must uphold.
"""

__version__ = "0.0.0"
