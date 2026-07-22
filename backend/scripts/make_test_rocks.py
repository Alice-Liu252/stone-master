#!/usr/bin/env python3
"""Generate synthetic "rock" photos for testing the scan pipeline offline.

There's no real rock photo dataset in this environment, so this draws
irregular speckled blobs on a neutral background — good enough to exercise
color/texture/shape feature extraction and prove determinism and
per-rock distinctiveness, but NOT a substitute for testing against real
photos before Phase 0 exit (see docs/ROADMAP.md).

Usage:
    python scripts/make_test_rocks.py --count 5 --out data/test_rocks
"""
from __future__ import annotations

import argparse
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw

CANVAS_SIZE = (400, 300)
BACKGROUND_COLORS = [(210, 205, 195), (190, 195, 200), (200, 190, 175)]
ROCK_PALETTES = [
    (120, 100, 85),   # brown river stone
    (140, 140, 145),  # grey granite
    (80, 78, 75),      # dark basalt
    (170, 120, 90),   # reddish sandstone
    (90, 110, 95),     # mossy green stone
    (60, 55, 60),      # near-black obsidian
]


def make_rock_image(seed: int, size=CANVAS_SIZE) -> Image.Image:
    """Deterministic: the same seed always renders the same pixels."""
    rng = random.Random(seed)
    img = Image.new("RGB", size, rng.choice(BACKGROUND_COLORS))
    draw = ImageDraw.Draw(img)

    cx, cy = size[0] // 2 + rng.randint(-30, 30), size[1] // 2 + rng.randint(-20, 20)
    base_radius = rng.randint(60, 110)
    base_color = rng.choice(ROCK_PALETTES)

    # Irregular blob: a ring of points at jittered radius/angle.
    points = []
    n_points = 14
    for i in range(n_points):
        angle = (2 * 3.14159265 * i) / n_points
        r = base_radius * (0.75 + rng.random() * 0.5)
        x = cx + r * math.cos(angle)
        y = cy + r * 0.75 * math.sin(angle)  # slightly flattened
        points.append((x, y))
    draw.polygon(points, fill=base_color)

    # Speckle texture: scattered dots of lighter/darker variants.
    speckle_count = rng.randint(150, 400)
    for _ in range(speckle_count):
        x = cx + rng.uniform(-base_radius, base_radius)
        y = cy + rng.uniform(-base_radius * 0.75, base_radius * 0.75)
        if (x - cx) ** 2 / base_radius**2 + (y - cy) ** 2 / (base_radius * 0.75) ** 2 > 1:
            continue
        shade = rng.randint(-35, 35)
        speckle_color = tuple(max(0, min(255, c + shade)) for c in base_color)
        r = rng.randint(1, 3)
        draw.ellipse([x - r, y - r, x + r, y + r], fill=speckle_color)

    return img


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--seed-start", type=int, default=1)
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent.parent / "data" / "test_rocks")
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    for i in range(args.count):
        seed = args.seed_start + i
        img = make_rock_image(seed)
        path = args.out / f"rock_{seed}.png"
        img.save(path)
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
