"""石頭養成系統 (docs/GDD.md 第 10 章).

Pure calculation functions for feeding/playing/cleaning/sleeping, leveling,
mood decay, personality, and evolution eligibility. The persistence side
(reading/writing stone_instances rows) lives in
fingerprint_store.FingerprintStore.care_for() / .evolve(), which are thin
glue that call into here — everything in this module is a pure function of
its inputs, so it's fully unit-testable without a database.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

# exp/affinity/mood deltas are fixed per action -- never randomized, so a
# given action always has a predictable, explainable effect. Only the
# diary flavor text below is allowed to vary.
ACTIONS = {
    "feed": {"label": "餵食", "exp": 8, "affinity": 3, "mood": 15},
    "play": {"label": "玩耍", "exp": 5, "affinity": 6, "mood": 20},
    "clean": {"label": "清潔", "exp": 0, "affinity": 3, "mood": 25},
    "sleep": {"label": "睡眠", "exp": 0, "affinity": 1, "mood": 30},
}

EXP_PER_LEVEL = 100
MAX_MOOD = 100
MOOD_DECAY_PER_DAY = 5  # mood drifts down this much per day with no interaction

EVOLVE_LEVEL_THRESHOLD = 10
EVOLVE_AFFINITY_THRESHOLD = 50

STAT_GROWTH_PER_LEVEL = 0.05  # +5% of base stat per level above 1


def scale_stats_for_level(base_stats: dict, level: int) -> dict:
    """Leveling should make a stone measurably stronger in battle, not
    just a number on a status screen — see battle.combatant_from_stats().
    Applies uniformly across all five stats; a real game may want
    per-species growth curves, this is the simplest version that closes
    the loop between growth.py and battle.py."""
    multiplier = 1 + STAT_GROWTH_PER_LEVEL * (level - 1)
    return {stat: max(1, round(value * multiplier)) for stat, value in base_stats.items()}

_DIARY_OPENERS = {
    "feed": ["你餵了牠喜歡的礦物餅乾，", "牠開心地吃著你給的食物，"],
    "play": ["你陪牠玩了一會兒，", "你們一起在附近探索了一下，"],
    "clean": ["你仔細擦亮了牠的表面，", "洗去了牠身上的塵土，"],
    "sleep": ["你讓牠好好休息了一下，", "牠安靜地睡了一覺，"],
}


def level_from_exp(total_exp: int) -> int:
    return 1 + total_exp // EXP_PER_LEVEL


def exp_to_next_level(total_exp: int) -> int:
    current_level = level_from_exp(total_exp)
    return current_level * EXP_PER_LEVEL - total_exp


def decayed_mood(stored_mood: int, last_interaction_at: str, now: Optional[datetime] = None) -> int:
    """Lazy decay: nothing ticks mood down in the background — it's
    recomputed from elapsed real time every time it's read, based on
    when the stone was last interacted with (fed/played with/cleaned/
    slept, or even just rescanned)."""
    now = now or datetime.now(timezone.utc)
    last = datetime.fromisoformat(last_interaction_at)
    elapsed_days = max(0.0, (now - last).total_seconds() / 86400)
    decayed = stored_mood - int(elapsed_days * MOOD_DECAY_PER_DAY)
    return max(0, min(MAX_MOOD, decayed))


def personality(feed_count: int, play_count: int, clean_count: int, sleep_count: int) -> str:
    """GDD 10: "發展出個性傾向（如親人/怕生/活潑）" — derived entirely from
    which kind of interaction the player has favored, never stored/rolled
    separately, so it's always consistent with the actual history."""
    total = feed_count + play_count + clean_count + sleep_count
    if total < 5:
        return "怕生"  # not enough interaction yet to have opened up
    tallies = {"親人": feed_count, "活潑": play_count, "穩重": clean_count + sleep_count}
    return max(tallies, key=tallies.get)


def can_evolve(level: int, affinity: int) -> bool:
    return level >= EVOLVE_LEVEL_THRESHOLD and affinity >= EVOLVE_AFFINITY_THRESHOLD


@dataclass(frozen=True)
class GrowthUpdate:
    exp: int
    affinity: int
    mood: int
    level: int
    leveled_up: bool
    diary_entry: str


def apply_action(
    action: str,
    current_exp: int,
    current_affinity: int,
    current_mood: int,
    last_interaction_at: str,
) -> GrowthUpdate:
    if action not in ACTIONS:
        raise ValueError(f"unknown action: {action!r}, expected one of {list(ACTIONS)}")
    effect = ACTIONS[action]

    mood_before_action = decayed_mood(current_mood, last_interaction_at)
    new_exp = current_exp + effect["exp"]
    new_affinity = min(100, current_affinity + effect["affinity"])
    new_mood = max(0, min(MAX_MOOD, mood_before_action + effect["mood"]))

    old_level = level_from_exp(current_exp)
    new_level = level_from_exp(new_exp)
    leveled_up = new_level > old_level

    opener = random.choice(_DIARY_OPENERS[action])
    if new_mood >= 70:
        mood_note = "牠現在心情很好。"
    elif new_mood < 40:
        mood_note = "牠好像還是有點沒精神。"
    else:
        mood_note = "牠的心情平穩了一些。"
    diary_entry = f"{opener}{mood_note}"
    if leveled_up:
        diary_entry += f"（升到了 Lv.{new_level}！）"

    return GrowthUpdate(
        exp=new_exp,
        affinity=new_affinity,
        mood=new_mood,
        level=new_level,
        leveled_up=leveled_up,
        diary_entry=diary_entry,
    )
