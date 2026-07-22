#!/usr/bin/env python3
"""CLI demo of the capture system (docs/GDD.md 第 12 章).

Unlike scan_demo.py (which always successfully catalogs a new rock, kept
simple for the rest of this prototype), this demonstrates the real GDD 12
mechanic: capture can fail, and your odds depend on your tool, your bait,
the stone's rarity, and how many times you've already tried on this same
rock (親密度 -- retrying raises your odds, pass a higher --attempt).

Usage:
    python scripts/capture_demo.py --player alice --image data/test_rocks/rock_1.png
    python scripts/capture_demo.py --player alice --image data/test_rocks/rock_1.png --tool legendary_orb --bait crystal_powder
    # if it fails, try again on the SAME rock with a higher --attempt:
    python scripts/capture_demo.py --player alice --image data/test_rocks/rock_1.png --attempt 2
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from stone_master import capture  # noqa: E402
from stone_master.fingerprint_store import FingerprintStore  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--player", required=True)
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--tool", choices=list(capture.TOOLS), default="resonance_orb")
    parser.add_argument("--bait", choices=[b for b in capture.BAITS if b is not None], default=None)
    parser.add_argument("--attempt", type=int, default=1, dest="attempt_number", help="which try this is on this same rock (raises odds)")
    parser.add_argument(
        "--db",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data" / "stones.db",
    )
    args = parser.parse_args()

    if not args.image.exists():
        parser.error(f"image not found: {args.image}")

    args.db.parent.mkdir(parents=True, exist_ok=True)
    with FingerprintStore(args.db) as store:
        result = store.attempt_capture(
            args.player, args.image, tool=args.tool, bait=args.bait, attempt_number=args.attempt_number
        )

    tool_name = capture.TOOLS[args.tool]["name"]
    bait_name = capture.BAITS[args.bait]["name"]

    if result.outcome == "recognized":
        print(f"這隻已經是你的了（#{result.record.id}），不用再捕捉。")
    elif result.outcome == "captured":
        print(f"用「{tool_name}」+「{bait_name}」捕捉成功！（成功率 {result.chance:.0%}）")
        print(f"加入圖鑑：#{result.record.id}｜{result.record.rarity} {result.record.element}系")
    else:
        preview = result.species_preview
        print(f"跑掉了...（成功率只有 {result.chance:.0%}）")
        print(f"看起來是一顆 {preview['rarity']} {preview['element']}系 的石頭，再試一次？（用 --attempt {args.attempt_number + 1}）")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
