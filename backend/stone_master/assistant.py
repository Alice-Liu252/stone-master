"""AI 個人化助手 (docs/GDD.md 第 19 章) + a persona for the encyclopedia Q&A.

Two things live here:
1. ASSISTANT_NAME / intro phrases — flavor text so answers from
   encyclopedia.answer_question() sound like a character talking, not a
   bare template dump. This part is intentionally non-deterministic
   (random.choice without a fixed seed): it's cosmetic phrasing, not game
   data, so nothing downstream depends on it being reproducible.
2. recommend() — the actual GDD 19 recommendation logic: looks at a
   player's real collection (from fingerprint_store.list_for_player) and
   suggests what to look for next, what to prioritize, and a short recap
   story. This part IS deterministic given the same collection, since the
   recommendation itself is data a player might reasonably expect to be
   stable rather than re-rolled every time they ask.
"""
from __future__ import annotations

import random
from typing import List

from . import encyclopedia, rules

ASSISTANT_NAME = "小晶"

_INTRO_PHRASES = [
    "讓我查一下資料庫...",
    "喔喔，這個我知道！",
    "翻了一下百科筆記...",
    "根據我手上的紀錄...",
]

# Extends docs/GDD.md 第 11 章 探索與召喚系統 的地形對照表，
# 補上該章節例子沒明講的 metamorphic 類別。
REGION_HINTS = {
    "mineral": "山區",
    "sedimentary": "河流",
    "igneous": "火山地質區",
    "metamorphic": "山谷／中央山脈變質岩帶",
}


def say(entry: dict, question: str) -> str:
    """Persona-wrapped version of encyclopedia.answer_question()."""
    intro = random.choice(_INTRO_PHRASES)
    answer = encyclopedia.answer_question(entry, question)
    return f"{ASSISTANT_NAME}：{intro}\n{answer}"


def recommend(collection: List) -> dict:
    """GDD 19: 石頭推薦 / 造型與訓練建議 / 專屬故事，算給定收藏下的建議。

    `collection` is a list of fingerprint_store.StoneRecord (or anything
    with .rock_type, .rarity, .stats, .discovered_at, .encyclopedia_id).
    Deterministic: same collection in -> same recommendation out.
    """
    if not collection:
        return {
            "explore_hint": f"你的圖鑑還是空的，{ASSISTANT_NAME}建議你先去附近隨便一顆石頭掃看看，任何地方都可以開始！",
            "training_hint": None,
            "completion": "0/%d 個已知種類" % len(encyclopedia.SPECIES),
            "story": f"{ASSISTANT_NAME}：我們的冒險還沒開始，我已經迫不及待了！",
        }

    rock_type_counts = {rt: 0 for rt in REGION_HINTS}
    for stone in collection:
        rock_type_counts[stone.rock_type] = rock_type_counts.get(stone.rock_type, 0) + 1

    least_type = min(rock_type_counts, key=lambda rt: rock_type_counts[rt])
    region = REGION_HINTS.get(least_type, "附近")
    explore_hint = (
        f"你收集的「{least_type}」類石頭比較少（只有 {rock_type_counts[least_type]} 顆），"
        f"下次可以往{region}找找看！"
    )

    rarity_rank = {name: i for i, (name, _) in enumerate(rules.RARITY_TABLE)}
    top_stone = max(collection, key=lambda s: rarity_rank.get(s.rarity, 0))
    top_entry = encyclopedia.get_by_id(top_stone.encyclopedia_id)
    training_hint = (
        f"你目前最稀有的是 #{top_stone.id}（{top_stone.rarity}，對應真實石頭「{top_entry['name_zh']}」），"
        f"建議優先培養牠、帶去參加道館戰！"
    )

    known_species = len(encyclopedia.SPECIES)
    matched_species = len({s.encyclopedia_id for s in collection})
    completion = f"{matched_species}/{known_species} 個已知種類"

    first_seen = min(collection, key=lambda s: s.discovered_at)
    story = (
        f"{ASSISTANT_NAME}：從你收服 #{first_seen.id} 開始，我們已經一起找到 {len(collection)} 顆石頭了，"
        f"其中「{least_type}」類還可以再多探索一點，加油！"
    )

    return {
        "explore_hint": explore_hint,
        "training_hint": training_hint,
        "completion": completion,
        "story": story,
    }
