"""Skill data (docs/GDD.md 第 14 章 技能系統).

The flavor names are straight from the GDD's example list. The power/cost/
category numbers are this prototype's first concrete numbers for them --
balance values to tune during playtesting, nothing here is load-bearing
outside battle.py.

The GDD's example attack-skill list only names 6 (of the 10 elements in
rules.ELEMENTS): 大地/火/雷/冰/水晶/星辰. 水/森林/光/暗 don't have a
dedicated named move yet -- battle.py falls back to a generic elemental
strike for those (see battle.attack_skill_for()). Writing dedicated named
skills for the remaining 4 elements is a good follow-up content task.
"""
from __future__ import annotations

SKILLS = {
    # 攻擊 (attack: deals damage, type multiplier applies via `element`)
    "rolling_stone_charge": {"name": "滾石衝鋒", "category": "attack", "element": "大地", "power": 28, "cost": 12},
    "lava_burst": {"name": "熔岩爆發", "category": "attack", "element": "火", "power": 32, "cost": 14},
    "thunder_strike": {"name": "雷霆攻擊", "category": "attack", "element": "雷", "power": 30, "cost": 13},
    "ice_crystal_blade": {"name": "冰晶飛刃", "category": "attack", "element": "冰", "power": 29, "cost": 12},
    "crystal_burst": {"name": "水晶爆裂", "category": "attack", "element": "水晶", "power": 31, "cost": 13},
    "falling_star": {"name": "星辰墜落", "category": "attack", "element": "星辰", "power": 33, "cost": 15},

    # 防禦 (defense: raises the user's defense for a few turns)
    "rock_shield": {"name": "岩石護盾", "category": "defense", "boost": 0.5, "duration": 3, "cost": 10},
    "crystal_barrier": {"name": "水晶結界", "category": "defense", "boost": 0.5, "duration": 3, "cost": 10},
    "energy_barrier": {"name": "能量屏障", "category": "defense", "boost": 0.4, "duration": 3, "cost": 9},
    "diamond_armor": {"name": "鑽石護甲", "category": "defense", "boost": 0.7, "duration": 2, "cost": 14},

    # 輔助 (support: heal or buff the user)
    "heal": {"name": "治癒", "category": "support", "effect": "heal", "amount": 0.35, "cost": 12},
    "recover": {"name": "回復", "category": "support", "effect": "heal", "amount": 0.25, "cost": 8},
    "empower": {"name": "強化", "category": "support", "effect": "attack_up", "amount": 0.4, "duration": 3, "cost": 10},
    "speed_up": {"name": "速度提升", "category": "support", "effect": "speed_up", "amount": 0.5, "duration": 3, "cost": 8},
    "defense_up": {"name": "防禦提升", "category": "support", "effect": "defense_up", "amount": 0.4, "duration": 3, "cost": 8},

    # 終極 (ultimate: high power/cost, gated by energy investment since
    # max energy scales with rarity — see rules.BASE_STAT_RANGES)
    "world_tremor": {"name": "世界震動", "category": "ultimate", "element": "大地", "power": 70, "cost": 28},
    "star_core_burst": {"name": "星核爆裂", "category": "ultimate", "element": "星辰", "power": 75, "cost": 30},
    "spacetime_rift": {"name": "時空裂縫", "category": "ultimate", "element": "暗", "power": 72, "cost": 29},
    "rainbow_miracle": {"name": "彩虹奇蹟", "category": "ultimate", "effect": "full_heal_and_buff", "cost": 30},
}

# Every element that doesn't have a dedicated named ultimate above falls
# back to 彩虹奇蹟, so every element has *some* ultimate option.
_ULTIMATE_BY_ELEMENT = {
    skill["element"]: skill_id
    for skill_id, skill in SKILLS.items()
    if skill["category"] == "ultimate" and "element" in skill
}


def get(skill_id: str) -> dict:
    return SKILLS[skill_id]


def attack_skill_id_for_element(element: str) -> str | None:
    for skill_id, skill in SKILLS.items():
        if skill["category"] == "attack" and skill.get("element") == element:
            return skill_id
    return None


def ultimate_skill_id_for_element(element: str) -> str:
    return _ULTIMATE_BY_ELEMENT.get(element, "rainbow_miracle")


def loadout_for_element(element: str) -> list:
    """A stone's default move set: its element's named attack skill (if
    any), a generic recover + defense buff every stone can use, and an
    ultimate. Real system would let players choose/train skills (GDD 14:
    技能升級、技能熟練度） — this is just enough to run a battle."""
    ids = []
    attack_id = attack_skill_id_for_element(element)
    if attack_id:
        ids.append(attack_id)
    ids += ["recover", "defense_up"]
    ids.append(ultimate_skill_id_for_element(element))
    return ids
