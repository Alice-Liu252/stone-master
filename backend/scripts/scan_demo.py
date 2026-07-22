#!/usr/bin/env python3
"""CLI demo of the full scan pipeline: photo -> features -> match-or-create.

This is the runnable stand-in for what will eventually be a client -> API
call once Unity + a real backend exist (see docs/TECHNICAL_ARCHITECTURE.md
section 3). Point it at any image twice in a row for the same player and
the second call should come back as a match, not a new stone.

Usage:
    python scripts/scan_demo.py --player alice --image data/test_rocks/rock_1.png
    python scripts/scan_demo.py --player alice --image data/test_rocks/rock_1.png  # scan again -> matches
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from stone_master.fingerprint_store import FingerprintStore  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--player", required=True, help="player id, e.g. 'alice'")
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument(
        "--db",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data" / "stones.db",
        help="SQLite file that persists this player's collection across runs",
    )
    args = parser.parse_args()

    if not args.image.exists():
        parser.error(f"image not found: {args.image}")

    args.db.parent.mkdir(parents=True, exist_ok=True)
    with FingerprintStore(args.db) as store:
        result = store.match_or_create(args.player, args.image)

    print(json.dumps({
        "is_new": result.is_new,
        "similarity": result.similarity,
        "stone": result.record.to_dict(),
    }, indent=2, ensure_ascii=False))

    if result.is_new:
        print("\n-> 新石頭！加入圖鑑。", file=sys.stderr)
    else:
        print(f"\n-> 認出這顆石頭了（相似度 {result.similarity:.3f}），讀取既有紀錄。", file=sys.stderr)


if __name__ == "__main__":
    main()
