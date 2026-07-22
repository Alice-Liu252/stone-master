"""捕捉系統 (docs/GDD.md 第 12 章 捕捉系統).

Pure success-rate math for capturing a newly-identified stone. This is
layered on top of vision.py/generation.py: those determine WHAT a rock
would become (deterministic, given its fingerprint); this module
determines WHETHER an attempt to catch it succeeds (probabilistic, given
tool/bait/rarity/attempt number) — matching the GDD's split between AR
掃描 (第 4 章, always identifies) and 捕捉 (第 12 章, a separate step that
can fail). See fingerprint_store.FingerprintStore.attempt_capture() for
where this plugs into the scan pipeline.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

# 捕捉工具：強度係數
TOOLS = {
    "resonance_orb": {"name": "共鳴晶球", "strength": 1.0},
    "advanced_orb": {"name": "高級晶球", "strength": 1.5},
    "legendary_orb": {"name": "傳說晶球", "strength": 2.2},
    "energy_net": {"name": "能量網", "strength": 1.2},
    "geo_scanner": {"name": "地質掃描器", "strength": 1.3},
}

# 誘餌：加成係數（乘在工具強度上）
BAITS = {
    None: {"name": "（無）", "bonus": 1.0},
    "mineral_cookie": {"name": "礦物餅乾", "bonus": 1.1},
    "honey": {"name": "蜂蜜", "bonus": 1.15},
    "crystal_powder": {"name": "水晶粉", "bonus": 1.25},
    "nectar": {"name": "花蜜", "bonus": 1.1},
}

# 稀有度係數：越稀有基礎捕捉率越低（數字是「難度」，不是機率本身）
RARITY_CATCH_DIFFICULTY = {
    "common": 1.0,
    "uncommon": 1.3,
    "rare": 1.8,
    "epic": 2.6,
    "legendary": 4.0,
}

BASE_CATCH_RATE = 0.9  # 最弱工具、無誘餌、第一次嘗試、普通稀有度時的基準值
FAMILIARITY_BONUS_PER_ATTEMPT = 0.12  # GDD 12: 親密度隨重複嘗試提升成功率
MAX_CATCH_RATE = 0.98  # 永遠不是 100% 保證捕捉
MIN_CATCH_RATE = 0.02  # 永遠不是完全不可能


def success_rate(tool: str, bait: Optional[str], rarity: str, attempt_number: int = 1) -> float:
    if tool not in TOOLS:
        raise ValueError(f"unknown tool: {tool!r}, expected one of {list(TOOLS)}")
    if bait not in BAITS:
        raise ValueError(f"unknown bait: {bait!r}, expected one of {list(BAITS)}")
    if rarity not in RARITY_CATCH_DIFFICULTY:
        raise ValueError(f"unknown rarity: {rarity!r}, expected one of {list(RARITY_CATCH_DIFFICULTY)}")

    strength = TOOLS[tool]["strength"] * BAITS[bait]["bonus"]
    difficulty = RARITY_CATCH_DIFFICULTY[rarity]
    familiarity = 1 + FAMILIARITY_BONUS_PER_ATTEMPT * (max(1, attempt_number) - 1)

    rate = BASE_CATCH_RATE * strength / difficulty * familiarity
    return max(MIN_CATCH_RATE, min(MAX_CATCH_RATE, rate))


@dataclass(frozen=True)
class CaptureAttempt:
    success: bool
    chance: float
    tool: str
    bait: Optional[str]
    attempt_number: int


def attempt(tool: str, bait: Optional[str], rarity: str, attempt_number: int, seed: str) -> CaptureAttempt:
    """Deterministic given the same seed — callers should mix in something
    that varies per player + per real attempt (see fingerprint_store.py),
    not just the rock's fingerprint, or every player would get an
    identical yes/no on the same rock."""
    chance = success_rate(tool, bait, rarity, attempt_number)
    rng = random.Random(seed)
    success = rng.random() < chance
    return CaptureAttempt(success=success, chance=chance, tool=tool, bait=bait, attempt_number=attempt_number)
