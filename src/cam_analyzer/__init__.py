"""cam-analyzer — camshaft analysis around a source-agnostic CamProfile boundary.

Layers (dependency flows inward; analysis never imports sources — C1/D001):

    sources/      produce a CamProfile from a cam card, measured lift, etc.
    profile/      the CamProfile port + canonical model + ProvFloat value layer
    analysis/     the eight source-blind consumers
    conformance/  the frozen adversary corpus that keeps the boundary honest

See ARCHITECTURE.md and docs/reference/ubiquitous-language.md. Milestone 1 turns
the reference cam card into source-agnostic profiles and returns stamped answers,
formal refusals, or undecidable safety verdicts rather than fabricated precision.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("cam-analyzer")
except PackageNotFoundError:  # running from a source tree that isn't installed
    __version__ = "0.0.0"
