"""Static game-balance tables for stone generation.

Mirrors docs/GDD.md section 6 (AI 原創石頭生成), section 13 (石頭戰鬥系統
十系屬性) and docs/TECHNICAL_ARCHITECTURE.md section 4 (參數化基礎模型庫).
Kept as plain data so designers can retune odds/stats without touching
generation logic in generation.py.
"""
from __future__ import annotations

# (name, weight) -- weights are relative, they don't need to sum to 100.
RARITY_TABLE = [
    ("common", 50),
    ("uncommon", 30),
    ("rare", 14),
    ("epic", 5),
    ("legendary", 1),
]

RARITY_STAT_MULTIPLIER = {
    "common": 1.0,
    "uncommon": 1.15,
    "rare": 1.35,
    "epic": 1.6,
    "legendary": 2.0,
}

# 十系 (GDD 第 13 章)
ELEMENTS = [
    "火", "水", "雷", "冰", "森林",
    "大地", "水晶", "光", "暗", "星辰",
]

# 克制循環 (GDD 13: "彼此構成克制循環" — plural "循環" is deliberate here,
# it's two interlocking 6- and 4- element cycles rather than one big
# rock-paper-scissors, so the ten elements split into a physical cycle and
# a mystical cycle instead of every element needing an opinion about
# every other one). Each element beats the *next* one in its cycle and
# loses to the *previous* one; see battle.type_multiplier().
ELEMENT_CYCLES = [
    ["火", "冰", "森林", "大地", "雷", "水"],  # 火剋冰、冰剋森林...一路回到水剋火
    ["光", "暗", "星辰", "水晶"],              # 光剋暗、暗剋星辰、星辰剋水晶、水晶剋光
]

# Base 3D template library (GDD 第 4 章 / 技術架構文件第 4 章：參數化基礎模型
# + 材質投影). rock_type groups templates so the generation heuristic can
# pick a plausible one for a given photo; real production library is
# ~20-30 templates authored by 3D art, this is a representative subset.
BASE_TEMPLATES = [
    {"id": "river_stone_round", "rock_type": "sedimentary"},
    {"id": "sandstone_slab", "rock_type": "sedimentary"},
    {"id": "conglomerate_lump", "rock_type": "sedimentary"},
    {"id": "igneous_angular_block", "rock_type": "igneous"},
    {"id": "basalt_column", "rock_type": "igneous"},
    {"id": "granite_chunk", "rock_type": "igneous"},
    {"id": "obsidian_shard", "rock_type": "igneous"},
    {"id": "layered_metamorphic_slab", "rock_type": "metamorphic"},
    {"id": "marble_smooth", "rock_type": "metamorphic"},
    {"id": "schist_flake", "rock_type": "metamorphic"},
    {"id": "quartz_prism", "rock_type": "mineral"},
    {"id": "crystal_cluster", "rock_type": "mineral"},
    {"id": "geode_sphere", "rock_type": "mineral"},
]

# Base stat ranges before the rarity multiplier is applied (GDD 第 13 章).
BASE_STAT_RANGES = {
    "hp": (30, 60),
    "attack": (5, 15),
    "defense": (5, 15),
    "speed": (5, 15),
    "energy": (10, 20),
}
