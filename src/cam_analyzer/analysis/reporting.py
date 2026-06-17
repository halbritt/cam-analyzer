"""Simple Markdown reporting over source-blind analysis results."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from cam_analyzer.analysis.dynamic_compression import (
    DynamicCompressionInput,
    analyze_dynamic_compression,
)
from cam_analyzer.analysis.piston_to_valve import PistonToValveInput, evaluate_piston_to_valve
from cam_analyzer.analysis.spring_safety import SpringSafetyInput, evaluate_spring_safety
from cam_analyzer.analysis.timing import basic_timing_map
from cam_analyzer.profile import CamProfile
from cam_analyzer.quantity import Angle, ProvFloat, Refusal, SafetyVerdict


@dataclass(frozen=True, slots=True)
class ReportInputs:
    timing_lifts: tuple[ProvFloat, ...]
    dynamic_compression_input: DynamicCompressionInput | None = None
    ptv_inputs: tuple[PistonToValveInput, ...] = ()
    spring_input: SpringSafetyInput | None = None
    title: str = "Cam analysis report"


def render_markdown_report(
    intake: CamProfile,
    exhaust: CamProfile,
    *,
    timing_lifts: Iterable[ProvFloat],
    dynamic_compression_input: DynamicCompressionInput | None = None,
    ptv_inputs: Iterable[PistonToValveInput] = (),
    spring_input: SpringSafetyInput | None = None,
    title: str = "Cam analysis report",
) -> str:
    """Render stamped values, refusals, and safety verdict explanations."""

    report_inputs = ReportInputs(
        timing_lifts=tuple(timing_lifts),
        dynamic_compression_input=dynamic_compression_input,
        ptv_inputs=tuple(ptv_inputs),
        spring_input=spring_input,
        title=title,
    )
    timing = basic_timing_map(intake, exhaust, report_inputs.timing_lifts)

    lines = [
        f"# {report_inputs.title}",
        "",
        "## Profile summary",
        f"- Intake max lift: {_format_value(intake.max_lift())}",
        f"- Exhaust max lift: {_format_value(exhaust.max_lift())}",
        f"- Intake area under curve: {_format_value(intake.area_under_curve())}",
        f"- Exhaust area under curve: {_format_value(exhaust.area_under_curve())}",
        "",
        "## Timing",
        f"- Intake centerline: {_format_angle(timing.intake_centerline)}",
        f"- Exhaust centerline: {_format_angle(timing.exhaust_centerline)}",
        f"- Lobe separation angle: {_format_angle(timing.lobe_separation_angle)}",
    ]

    for lift in report_inputs.timing_lifts:
        key = float(lift)
        lines.append(
            "- "
            f"Overlap at {_format_value(lift)}: {_format_angle(timing.overlap_by_lift[key])}; "
            f"intake events {_format_angles(timing.intake_events_by_lift[key])}; "
            f"exhaust events {_format_angles(timing.exhaust_events_by_lift[key])}"
        )

    if report_inputs.dynamic_compression_input is not None:
        lines.extend(["", "## Dynamic compression"])
        dcr = analyze_dynamic_compression(intake, report_inputs.dynamic_compression_input)
        if isinstance(dcr, Refusal):
            lines.append(f"- Dynamic compression ratio: REFUSED - {dcr.reason} Remedy: {dcr.remedy}")
        else:
            lines.append(
                "- "
                f"Dynamic compression ratio: {_format_value(dcr.dynamic_compression_ratio)}; "
                f"intake closing {_format_angle(dcr.intake_closing_angle)}"
            )

    if report_inputs.ptv_inputs:
        lines.extend(["", "## Piston-to-valve"])
        for ptv_input in report_inputs.ptv_inputs:
            ptv_result = evaluate_piston_to_valve(
                intake if ptv_input.valve == "intake" else exhaust,
                ptv_input,
            )
            if isinstance(ptv_result, Refusal):
                lines.append(
                    f"- {ptv_input.valve}: REFUSED - {ptv_result.reason} "
                    f"Remedy: {ptv_result.remedy}"
                )
                continue
            margin = f"; margin {_format_value(ptv_result.margin)}" if ptv_result.margin is not None else ""
            lines.append(
                f"- {ptv_input.valve}: {_format_verdict(ptv_result.verdict)} - "
                f"{ptv_result.explanation}{margin}"
            )

    if report_inputs.spring_input is not None:
        lines.extend(["", "## Spring safety"])
        spring_result = evaluate_spring_safety(intake, report_inputs.spring_input)
        if isinstance(spring_result, Refusal):
            lines.append(
                f"- Spring safety: REFUSED - {spring_result.reason} "
                f"Remedy: {spring_result.remedy}"
            )
            return "\n".join(lines) + "\n"
        margins = ""
        if spring_result.retainer_to_guide_margin is not None and spring_result.coil_margin is not None:
            margins = (
                f"; retainer margin {_format_value(spring_result.retainer_to_guide_margin)}"
                f"; coil margin {_format_value(spring_result.coil_margin)}"
            )
        lines.append(
            f"- Spring safety: {_format_verdict(spring_result.verdict)} - "
            f"{spring_result.explanation}{margins}"
        )

    return "\n".join(lines) + "\n"


def _format_value(value: ProvFloat | None) -> str:
    if value is None:
        return "not available"
    return f"{float(value):.3f} {value.unit} [{value.frame}, {value.provenance.name}]"


def _format_angle(angle: Angle) -> str:
    return f"{angle.degrees:.3f} deg [{angle.frame}]"


def _format_angles(angles: Iterable[Angle]) -> str:
    return ", ".join(_format_angle(angle) for angle in angles)


def _format_verdict(verdict: SafetyVerdict) -> str:
    return verdict.value
