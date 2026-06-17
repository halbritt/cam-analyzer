"""``cam-analyze`` — one command from a cam-card file to a Markdown report.

Stays dependency-free: a cam card is a small JSON file (or use ``--reference`` for
the built-in Web Cam 81-651 WR250R card). The CLI only wires source → profile →
report; every honesty guarantee lives in the layers it calls. Where the card's
evidence can't justify a number, the report says so (refusals / UNDECIDABLE),
exactly as the library does.

Card JSON shape (durations in crank degrees, lifts in inches)::

    {
      "intake":  {"valve_lift_in": 0.360, "advertised_duration_deg": 262.0,
                  "duration_050_deg": 238.0, "lobe_center_deg": 109.5, "lash_in": 0.006},
      "exhaust": {"valve_lift_in": 0.360, "advertised_duration_deg": 270.0,
                  "duration_050_deg": 246.0, "lobe_center_deg": 104.5, "lash_in": 0.008},
      "engine":  {"bore_mm": 77.0, "stroke_mm": 53.6, "rod_length_mm": 96.9,
                  "static_compression_ratio": 12.8},   // optional → enables DCR
      "timing_lifts_in": [0.050],                       // optional, default [0.050]
      "approximate_derivatives": false                  // optional
    }
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from cam_analyzer.analysis.dynamic_compression import DynamicCompressionInput, EngineGeometry
from cam_analyzer.analysis.piston_to_valve import (
    PistonToValveInput,
    default_exhaust_policy,
    default_intake_policy,
)
from cam_analyzer.analysis.reporting import render_markdown_report
from cam_analyzer.analysis.spring_safety import SpringSafetyInput, default_spring_policy
from cam_analyzer.quantity import Inch, ProvFloat, inferred
from cam_analyzer.sources.cam_card import CamCard, CamLobeSpec, profiles_from_cam_card

_DEFAULT_TIMING_LIFTS_IN = (0.050,)


def _lobe_from_mapping(side: str, data: Any) -> CamLobeSpec:
    if not isinstance(data, dict):
        raise ValueError(f"card '{side}' must be an object with the lobe fields")
    try:
        return CamLobeSpec(
            valve_lift_in=float(data["valve_lift_in"]),
            advertised_duration_deg=float(data["advertised_duration_deg"]),
            duration_050_deg=float(data["duration_050_deg"]),
            lobe_center_deg=float(data["lobe_center_deg"]),
            lash_in=float(data["lash_in"]),
        )
    except KeyError as exc:
        raise ValueError(f"card '{side}' is missing required field {exc}") from exc


def _card_from_mapping(data: Any) -> CamCard:
    if not isinstance(data, dict) or "intake" not in data or "exhaust" not in data:
        raise ValueError("card file must be an object with 'intake' and 'exhaust' lobes")
    return CamCard(
        intake=_lobe_from_mapping("intake", data["intake"]),
        exhaust=_lobe_from_mapping("exhaust", data["exhaust"]),
    )


def _dcr_input_from_mapping(data: Any, closing_lift: ProvFloat) -> DynamicCompressionInput | None:
    engine = data.get("engine") if isinstance(data, dict) else None
    if engine is None:
        return None
    if not isinstance(engine, dict):
        raise ValueError("card 'engine' must be an object")
    try:
        return DynamicCompressionInput(
            static_compression_ratio=float(engine["static_compression_ratio"]),
            geometry=EngineGeometry.from_mm(
                bore=float(engine["bore_mm"]),
                stroke=float(engine["stroke_mm"]),
                rod_length=float(engine["rod_length_mm"]),
            ),
            closing_lift=closing_lift,
        )
    except KeyError as exc:
        raise ValueError(f"card 'engine' is missing required field {exc}") from exc


def _timing_lifts_in(data: Any) -> tuple[float, ...]:
    raw = data.get("timing_lifts_in") if isinstance(data, dict) else None
    if raw is None:
        return _DEFAULT_TIMING_LIFTS_IN
    if not isinstance(raw, list) or not raw:
        raise ValueError("'timing_lifts_in' must be a non-empty list of inch values")
    return tuple(float(value) for value in raw)


def render_report_from_card_data(data: Any, *, approximate_derivatives: bool) -> str:
    """Build profiles from parsed card data and render the Markdown report."""
    card = _card_from_mapping(data)
    profiles = profiles_from_cam_card(card, approximate_derivatives=approximate_derivatives)
    timing_lifts = tuple(inferred(value, Inch, "valve_side") for value in _timing_lifts_in(data))
    return render_markdown_report(
        profiles.intake,
        profiles.exhaust,
        timing_lifts=timing_lifts,
        dynamic_compression_input=_dcr_input_from_mapping(data, timing_lifts[0]),
        ptv_inputs=(
            PistonToValveInput("intake", default_intake_policy()),
            PistonToValveInput("exhaust", default_exhaust_policy()),
        ),
        spring_input=SpringSafetyInput(default_spring_policy()),
        title=str(data.get("title", "Cam analysis report")) if isinstance(data, dict) else "Cam analysis report",
    )


def _load_card_data(args: argparse.Namespace) -> Any:
    if args.reference:
        card = CamCard.wr250r_reference()
        return {
            "title": "WR250R reference (Web Cam 81-651)",
            "intake": _lobe_to_mapping(card.intake),
            "exhaust": _lobe_to_mapping(card.exhaust),
            "engine": {
                "bore_mm": 77.0,
                "stroke_mm": 53.6,
                "rod_length_mm": 96.9,
                "static_compression_ratio": 12.8,
            },
        }
    text = Path(args.card).read_text()
    return json.loads(text)


def _lobe_to_mapping(lobe: CamLobeSpec) -> dict[str, float]:
    return {
        "valve_lift_in": lobe.valve_lift_in,
        "advertised_duration_deg": lobe.advertised_duration_deg,
        "duration_050_deg": lobe.duration_050_deg,
        "lobe_center_deg": lobe.lobe_center_deg,
        "lash_in": lobe.lash_in,
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cam-analyze",
        description="Turn a cam-card JSON file into a source-blind Markdown analysis report.",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("card", nargs="?", help="path to a cam-card JSON file")
    source.add_argument(
        "--reference",
        action="store_true",
        help="use the built-in Web Cam 81-651 WR250R reference card instead of a file",
    )
    parser.add_argument(
        "--approximate",
        action="store_true",
        help="answer otherwise-refused higher derivatives with an EXTRAPOLATED ballpark",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        data = _load_card_data(args)
        report = render_report_from_card_data(data, approximate_derivatives=args.approximate)
    except FileNotFoundError as exc:
        print(f"cam-analyze: card file not found: {exc.filename}", file=sys.stderr)
        return 2
    except (ValueError, json.JSONDecodeError) as exc:
        print(f"cam-analyze: invalid cam card: {exc}", file=sys.stderr)
        return 2
    print(report, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
