"""Battle system (docs/GDD.md 第 13 章 石頭戰鬥系統).

A turn-based simulator: two Combatants take turns using skills from
skills.py until one reaches 0 HP or a turn cap is hit. This stands in for
the server-authoritative battle resolution described in
docs/TECHNICAL_ARCHITECTURE.md section 7 — in the real game this logic
runs on the battle server, never on the client, so it can't be tampered
with. Everything here is a pure function of its inputs plus an explicit
`seed`, so a given matchup + seed always plays out identically (useful
for battle replays, GDD 13's `battle_log.replay_seed`).
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional

from . import rules, skills

ENERGY_REGEN_PER_TURN = 5
MAX_TURNS = 50  # safety cap so a stalemate ends in a draw, not an infinite loop

_BEATS = {}
for _cycle in rules.ELEMENT_CYCLES:
    for _i, _element in enumerate(_cycle):
        _BEATS[_element] = _cycle[(_i + 1) % len(_cycle)]


def type_multiplier(attacker_element: str, defender_element: str) -> float:
    """1.5x if attacker's element beats defender's (per rules.ELEMENT_CYCLES),
    1/1.5x if the reverse is true, 1.0x otherwise (including elements in
    different cycles, or a stone hitting its own element)."""
    if _BEATS.get(attacker_element) == defender_element:
        return 1.5
    if _BEATS.get(defender_element) == attacker_element:
        return 1 / 1.5
    return 1.0


@dataclass
class Combatant:
    name: str
    element: str
    max_hp: int
    attack: int
    defense: int
    speed: int
    max_energy: int
    skill_ids: List[str]
    hp: int = field(init=False)
    energy: int = field(init=False)
    buffs: List[dict] = field(default_factory=list)  # [{"stat": "defense", "amount": 0.5, "turns_left": 3}]

    def __post_init__(self):
        self.hp = self.max_hp
        self.energy = self.max_energy

    def is_alive(self) -> bool:
        return self.hp > 0

    def effective(self, stat: str) -> float:
        base = getattr(self, stat)
        bonus = sum(b["amount"] for b in self.buffs if b["stat"] == stat)
        return base * (1 + bonus)

    def tick_buffs(self) -> None:
        for buff in self.buffs:
            buff["turns_left"] -= 1
        self.buffs = [b for b in self.buffs if b["turns_left"] > 0]

    def affordable_skills(self) -> List[str]:
        affordable = [sid for sid in self.skill_ids if skills.get(sid)["cost"] <= self.energy]
        return affordable or ["struggle"]  # always has SOME move


STRUGGLE = {"name": "掙扎", "category": "attack", "power": 10, "cost": 0}


def _resolve_skill(actor: Combatant, target: Combatant, skill_id: str) -> str:
    skill = STRUGGLE if skill_id == "struggle" else skills.get(skill_id)
    actor.energy -= skill.get("cost", 0)

    if skill["category"] in ("attack", "ultimate") and "power" in skill:
        multiplier = type_multiplier(actor.element, target.element) if "element" in skill else 1.0
        raw = actor.effective("attack") + skill["power"] - target.effective("defense") * 0.5
        damage = max(1, round(raw * multiplier))
        target.hp = max(0, target.hp - damage)
        tag = " (效果絕佳!)" if multiplier > 1 else (" (效果不太好...)" if multiplier < 1 else "")
        return f"{actor.name} 使用「{skill['name']}」，對 {target.name} 造成 {damage} 傷害{tag}"

    if skill["category"] == "defense":
        actor.buffs.append({"stat": "defense", "amount": skill["boost"], "turns_left": skill["duration"]})
        return f"{actor.name} 使用「{skill['name']}」，防禦力提升"

    if skill["category"] == "support" or skill.get("effect"):
        effect = skill.get("effect")
        if effect == "heal":
            healed = round(actor.max_hp * skill["amount"])
            actor.hp = min(actor.max_hp, actor.hp + healed)
            return f"{actor.name} 使用「{skill['name']}」，恢復了 {healed} 點 HP"
        if effect == "attack_up":
            actor.buffs.append({"stat": "attack", "amount": skill["amount"], "turns_left": skill["duration"]})
            return f"{actor.name} 使用「{skill['name']}」，攻擊力提升"
        if effect == "speed_up":
            actor.buffs.append({"stat": "speed", "amount": skill["amount"], "turns_left": skill["duration"]})
            return f"{actor.name} 使用「{skill['name']}」，速度提升"
        if effect == "defense_up":
            actor.buffs.append({"stat": "defense", "amount": skill["amount"], "turns_left": skill["duration"]})
            return f"{actor.name} 使用「{skill['name']}」，防禦力提升"
        if effect == "full_heal_and_buff":
            actor.hp = actor.max_hp
            actor.buffs.append({"stat": "attack", "amount": 0.3, "turns_left": 3})
            actor.buffs.append({"stat": "defense", "amount": 0.3, "turns_left": 3})
            return f"{actor.name} 使用「{skill['name']}」，完全恢復並提升了攻防！"

    return f"{actor.name} 使用「{skill['name']}」"


@dataclass(frozen=True)
class BattleResult:
    winner: Optional[str]  # combatant name, or None for a draw/timeout
    turns: int
    log: List[str]


def simulate_battle(a: Combatant, b: Combatant, seed: str) -> BattleResult:
    rng = random.Random(seed)
    log: List[str] = [f"戰鬥開始：{a.name}（{a.element}系）VS {b.name}（{b.element}系）"]

    for turn in range(1, MAX_TURNS + 1):
        order = sorted([a, b], key=lambda c: c.effective("speed"), reverse=True)
        # deterministic tie-break: if speed is equal, seed decides who's first
        if a.effective("speed") == b.effective("speed"):
            order = [a, b] if rng.random() < 0.5 else [b, a]

        for actor in order:
            other = b if actor is a else a
            if not actor.is_alive() or not other.is_alive():
                continue
            actor.energy = min(actor.max_energy, actor.energy + ENERGY_REGEN_PER_TURN)
            skill_id = rng.choice(actor.affordable_skills())
            log.append(f"[第 {turn} 回合] " + _resolve_skill(actor, other, skill_id))
            if not other.is_alive():
                log.append(f"{other.name} 倒下了！{actor.name} 獲勝！")
                return BattleResult(winner=actor.name, turns=turn, log=log)

        a.tick_buffs()
        b.tick_buffs()

    log.append("回合數到達上限，比賽平手。")
    return BattleResult(winner=None, turns=MAX_TURNS, log=log)


def combatant_from_stats(name: str, element: str, stats: dict, skill_ids: Optional[List[str]] = None) -> Combatant:
    """Build a Combatant from a stone's stats dict (fingerprint_store.StoneRecord.stats)."""
    return Combatant(
        name=name,
        element=element,
        max_hp=stats["hp"],
        attack=stats["attack"],
        defense=stats["defense"],
        speed=stats["speed"],
        max_energy=stats["energy"],
        skill_ids=skill_ids or skills.loadout_for_element(element),
    )
