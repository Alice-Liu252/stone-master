#!/usr/bin/env python3
"""CLI demo of the AI 個人化助手 (docs/GDD.md 第 19 章) — 小晶 looks at your
whole collection and recommends what to explore/train next.

Usage:
    python scripts/assistant_demo.py --player alice
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from stone_master import assistant  # noqa: E402
from stone_master.fingerprint_store import FingerprintStore  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--player", required=True)
    parser.add_argument(
        "--db",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data" / "stones.db",
    )
    args = parser.parse_args()

    with FingerprintStore(args.db) as store:
        collection = store.list_for_player(args.player)

    advice = assistant.recommend(collection)

    print(f"=== {assistant.ASSISTANT_NAME} 給 {args.player} 的建議 ===")
    print(f"圖鑑完成度：{advice['completion']}")
    print(f"探索建議：{advice['explore_hint']}")
    if advice["training_hint"]:
        print(f"培養建議：{advice['training_hint']}")
    print(f"\n{advice['story']}")


if __name__ == "__main__":
    main()
