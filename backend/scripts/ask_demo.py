#!/usr/bin/env python3
"""CLI demo of the AI 石頭百科 (docs/GDD.md 第 5 章) — ask a scanned stone
what it is, once it's in your collection.

Usage:
    # first scan a rock so it's in the database:
    python scripts/scan_demo.py --player alice --image data/test_rocks/rock_1.png

    # then ask about it by its stone id (printed by scan_demo.py):
    python scripts/ask_demo.py --player alice --stone-id 1 --question "這是什麼石頭？"
    python scripts/ask_demo.py --player alice --stone-id 1 --question "如何形成？"
    python scripts/ask_demo.py --player alice --stone-id 1 --list-questions
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from stone_master import assistant, encyclopedia  # noqa: E402
from stone_master.fingerprint_store import FingerprintStore  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--player", required=True)
    parser.add_argument("--stone-id", type=int, required=True)
    parser.add_argument("--question", default="這是什麼石頭？")
    parser.add_argument("--list-questions", action="store_true", help="show the canonical questions you can ask")
    parser.add_argument(
        "--db",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "data" / "stones.db",
    )
    args = parser.parse_args()

    if args.list_questions:
        print("可以問的問題：")
        for q in encyclopedia.CANONICAL_QUESTIONS:
            print(f"  - {q}")
        return

    with FingerprintStore(args.db) as store:
        stone = store.get_by_id(args.player, args.stone_id)

    if stone is None:
        print(f"找不到 {args.player} 的第 {args.stone_id} 號石頭，先用 scan_demo.py 掃描一顆吧。", file=sys.stderr)
        raise SystemExit(1)

    entry = encyclopedia.get_by_id(stone.encyclopedia_id)
    print(f"[你的石頭 #{stone.id}｜遊戲屬性：{stone.rarity} {stone.element}系｜稀有度樣板 {stone.template_id}]")
    print(f"你問{assistant.ASSISTANT_NAME}：{args.question}")
    print(assistant.say(entry, args.question))


if __name__ == "__main__":
    main()
