#!/usr/bin/env python3
"""CLI demo of the growth/care system (docs/GDD.md 第 10 章).

Usage:
    python scripts/care_demo.py --player alice --stone-id 1 --action feed
    python scripts/care_demo.py --player alice --stone-id 1 --action play
    python scripts/care_demo.py --player alice --stone-id 1 --action clean
    python scripts/care_demo.py --player alice --stone-id 1 --action sleep
    python scripts/care_demo.py --player alice --stone-id 1 --evolve
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from stone_master import growth  # noqa: E402
from stone_master.fingerprint_store import FingerprintStore  # noqa: E402


def _print_status(stone) -> None:
    print(
        f"#{stone.id}｜Lv.{stone.level}（還差 {growth.exp_to_next_level(stone.exp)} 經驗升級）"
        f"｜好感度 {stone.affinity}｜心情 {stone.current_mood}｜個性：{stone.personality}"
        + ("｜已進化" if stone.evolved else "")
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--player", required=True)
    parser.add_argument("--stone-id", type=int, required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--action", choices=list(growth.ACTIONS))
    group.add_argument("--evolve", action="store_true")
    parser.add_argument(
        "--db",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data" / "stones.db",
    )
    args = parser.parse_args()

    with FingerprintStore(args.db) as store:
        if args.evolve:
            stone = store.evolve(args.player, args.stone_id)
            if stone is None:
                print("還不能進化（需要等級 >= 10 且好感度 >= 50），或這隻已經進化過了。", file=sys.stderr)
                raise SystemExit(1)
            print(f"進化成功！新的樣板：{stone.template_id}")
            _print_status(stone)
            return

        stone = store.care_for(args.player, args.stone_id, args.action)
        if stone is None:
            print(f"找不到 {args.player} 的第 {args.stone_id} 號石頭。", file=sys.stderr)
            raise SystemExit(1)

        print(stone.diary[-1])
        _print_status(stone)


if __name__ == "__main__":
    main()
