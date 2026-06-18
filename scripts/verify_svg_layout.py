#!/usr/bin/env python3
"""Raster smoke-check for the static SVAJ SVG layout."""

from __future__ import annotations

import argparse
from pathlib import Path

import cairosvg
from PIL import Image

EXPECTED_SIZE = (1536, 1024)
PLOT_REGION = (96, 92, 1120, 840)
HOW_TO_OVERFLOW_REGION = (940, 977, 1492, 992)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render a cam-analyzer SVG to PNG and check for obvious layout failures."
    )
    parser.add_argument("svg", type=Path, help="SVG chart to verify")
    parser.add_argument(
        "--png",
        type=Path,
        default=Path("/tmp/cam-analyzer-layout-check.png"),
        help="PNG path to write for visual inspection",
    )
    args = parser.parse_args()

    cairosvg.svg2png(url=str(args.svg), write_to=str(args.png), output_width=EXPECTED_SIZE[0])
    image = Image.open(args.png).convert("RGB")
    if image.size != EXPECTED_SIZE:
        raise SystemExit(f"expected rendered PNG size {EXPECTED_SIZE}, got {image.size}")

    plot_pixels = _count_non_white(image.crop(PLOT_REGION))
    if plot_pixels < 10_000:
        raise SystemExit("rendered chart plot area appears blank")

    spill_pixels = _count_dark(image.crop(HOW_TO_OVERFLOW_REGION))
    if spill_pixels:
        raise SystemExit(
            f"How-to-read panel has {spill_pixels} dark pixels below its box; text likely spills"
        )

    print(f"layout check passed: {args.png}")
    return 0


def _count_non_white(image: Image.Image) -> int:
    data = image.tobytes()
    return sum(
        1
        for index in range(0, len(data), 3)
        if data[index] != 255 or data[index + 1] != 255 or data[index + 2] != 255
    )


def _count_dark(image: Image.Image) -> int:
    data = image.tobytes()
    return sum(
        1
        for index in range(0, len(data), 3)
        if data[index] < 170 and data[index + 1] < 170 and data[index + 2] < 170
    )


if __name__ == "__main__":
    raise SystemExit(main())
