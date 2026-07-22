#!/usr/bin/env python3
"""List a player's collection with their stone ids -- so you don't have to
guess ids when using ask_demo.py / battle_demo.py. Ids are global across
all players (not reset to 1 per player), which is a real UX detail the
production game should hide behind a per-player display number.

Usage:
    python scripts/collection_demo.py --player alice
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from stone_master import encyclopedia  # noqa: E402
from stone_master.fingerprint_store import FingerprintStore  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--player", required=True)
    parser.add_argument(
        "--db",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data" / "stones.db",
    )
    args = parser.parse_args()

    with FingerprintStore(args.db) as store:
        collection = store.list_for_player(args.player)

    if not collection:
        print(f"{args.player} 還沒有任何石頭，先用 scan_demo.py 掃描一顆吧。")
        return

    print(f"=== {args.player} 的收藏（共 {len(collection)} 顆）===")
    for stone in collection:
        entry = encyclopedia.get_by_id(stone.encyclopedia_id)
        print(f"#{stone.id}｜{stone.rarity} {stone.element}系｜對應真實石頭：{entry['name_zh']}｜HP{stone.stats['hp']} 攻{stone.stats['attack']} 防{stone.stats['defense']}")


if __name__ == "__main__":
    main()
