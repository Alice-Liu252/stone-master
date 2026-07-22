#!/usr/bin/env python3
"""CLI demo of the battle system (docs/GDD.md 第 13-14 章).

Usage:
    # scan two stones first (can be the same or different players):
    python scripts/scan_demo.py --player alice --image data/test_rocks/rock_1.png
    python scripts/scan_demo.py --player bob   --image data/test_rocks/rock_2.png

    # then battle them:
    python scripts/battle_demo.py --player-a alice --stone-id-a 1 --player-b bob --stone-id-b 1
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from stone_master import battle  # noqa: E402
from stone_master.fingerprint_store import FingerprintStore  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--player-a", required=True)
    parser.add_argument("--stone-id-a", type=int, required=True)
    parser.add_argument("--player-b", required=True)
    parser.add_argument("--stone-id-b", type=int, required=True)
    parser.add_argument("--seed", default="battle-demo", help="battle replay seed (same seed = same outcome)")
    parser.add_argument(
        "--db",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data" / "stones.db",
    )
    args = parser.parse_args()

    with FingerprintStore(args.db) as store:
        stone_a = store.get_by_id(args.player_a, args.stone_id_a)
        stone_b = store.get_by_id(args.player_b, args.stone_id_b)

    if stone_a is None or stone_b is None:
        print("找不到其中一隻石頭，先用 scan_demo.py 掃描吧。", file=sys.stderr)
        raise SystemExit(1)

    a = battle.combatant_from_stats(f"{args.player_a}的#{stone_a.id}", stone_a.element, stone_a.stats)
    b = battle.combatant_from_stats(f"{args.player_b}的#{stone_b.id}", stone_b.element, stone_b.stats)

    result = battle.simulate_battle(a, b, seed=args.seed)
    print("\n".join(result.log))
    print(f"\n共 {result.turns} 回合。" + (f"獲勝者：{result.winner}" if result.winner else "平手。"))


if __name__ == "__main__":
    main()
