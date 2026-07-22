from stone_master import battle, rules, skills


def test_every_element_appears_exactly_once_across_the_cycles():
    all_elements = [el for cycle in rules.ELEMENT_CYCLES for el in cycle]
    assert sorted(all_elements) == sorted(rules.ELEMENTS)
    assert len(all_elements) == len(set(all_elements))


def test_type_multiplier_is_symmetric_advantage_and_disadvantage():
    assert battle.type_multiplier("火", "冰") == 1.5  # 火剋冰
    assert battle.type_multiplier("冰", "火") == 1 / 1.5  # reverse is disadvantaged
    assert battle.type_multiplier("光", "暗") == 1.5
    assert battle.type_multiplier("水晶", "光") == 1.5  # cycle wraps around


def test_type_multiplier_is_neutral_across_unrelated_or_same_element():
    assert battle.type_multiplier("火", "火") == 1.0
    assert battle.type_multiplier("火", "光") == 1.0  # different cycles


def test_every_element_has_a_usable_loadout():
    for element in rules.ELEMENTS:
        loadout = skills.loadout_for_element(element)
        assert loadout, element
        for skill_id in loadout:
            assert skill_id in skills.SKILLS


def _weak_combatant(name="A", element="火"):
    return battle.combatant_from_stats(
        name, element, {"hp": 30, "attack": 5, "defense": 5, "speed": 5, "energy": 15}
    )


def _strong_combatant(name="B", element="水"):
    return battle.combatant_from_stats(
        name, element, {"hp": 200, "attack": 40, "defense": 20, "speed": 20, "energy": 40}
    )


def test_damage_is_floored_at_1_even_against_absurd_defense():
    attacker = _weak_combatant(element="火")
    defender = battle.combatant_from_stats(
        "tank", "水晶", {"hp": 999, "attack": 1, "defense": 999, "speed": 1, "energy": 20}
    )
    log_line = battle._resolve_skill(attacker, defender, "lava_burst")
    assert defender.hp == 998  # 999 - the 1-damage floor, never 0 or negative
    assert "1 傷害" in log_line


def test_a_much_stronger_combatant_tends_to_win():
    weak = _weak_combatant()
    strong = _strong_combatant()
    result = battle.simulate_battle(weak, strong, seed="mismatch")
    assert result.winner == strong.name


def test_battle_is_deterministic_given_the_same_seed():
    a1, b1 = _weak_combatant("A", "火"), _strong_combatant("B", "水")
    a2, b2 = _weak_combatant("A", "火"), _strong_combatant("B", "水")
    r1 = battle.simulate_battle(a1, b1, seed="replay-42")
    r2 = battle.simulate_battle(a2, b2, seed="replay-42")
    assert r1.log == r2.log
    assert r1.winner == r2.winner


def test_battle_always_terminates_with_a_winner_or_explicit_draw():
    a, b = _weak_combatant("A"), _strong_combatant("B")
    result = battle.simulate_battle(a, b, seed="terminates")
    assert result.turns <= battle.MAX_TURNS
    assert result.winner in (a.name, b.name, None)
