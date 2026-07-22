from stone_master import assistant, encyclopedia
from stone_master.fingerprint_store import StoneRecord


def _stone(id, rock_type, rarity, encyclopedia_id, discovered_at):
    return StoneRecord(
        id=id,
        player_id="alice",
        rock_type=rock_type,
        template_id="river_stone_round",
        rarity=rarity,
        element="火",
        stats={"hp": 10, "attack": 5, "defense": 5, "speed": 5, "energy": 5},
        encyclopedia_id=encyclopedia_id,
        level=1,
        exp=0,
        affinity=0,
        discovered_at=discovered_at,
        last_seen_at=discovered_at,
    )


def test_recommend_on_empty_collection_suggests_exploring():
    advice = assistant.recommend([])
    assert advice["training_hint"] is None
    assert "0/" in advice["completion"]


def test_recommend_is_deterministic_for_the_same_collection():
    collection = [
        _stone(1, "mineral", "common", "quartz", "2026-01-01T00:00:00+00:00"),
        _stone(2, "mineral", "rare", "amethyst", "2026-01-02T00:00:00+00:00"),
    ]
    a = assistant.recommend(collection)
    b = assistant.recommend(collection)
    assert a == b


def test_recommend_flags_the_least_represented_rock_type():
    collection = [
        _stone(1, "mineral", "common", "quartz", "2026-01-01T00:00:00+00:00"),
        _stone(2, "mineral", "common", "amethyst", "2026-01-02T00:00:00+00:00"),
        _stone(3, "igneous", "common", "granite", "2026-01-03T00:00:00+00:00"),
    ]
    advice = assistant.recommend(collection)
    # sedimentary and metamorphic both have 0 -- "sedimentary" wins ties
    # because dict iteration order in REGION_HINTS is insertion order and
    # min() keeps the first minimum it sees.
    assert "sedimentary" in advice["explore_hint"] or "metamorphic" in advice["explore_hint"]


def test_recommend_prioritizes_the_highest_rarity_stone():
    collection = [
        _stone(1, "mineral", "common", "quartz", "2026-01-01T00:00:00+00:00"),
        _stone(2, "igneous", "legendary", "obsidian", "2026-01-02T00:00:00+00:00"),
        _stone(3, "metamorphic", "rare", "marble", "2026-01-03T00:00:00+00:00"),
    ]
    advice = assistant.recommend(collection)
    assert "#2" in advice["training_hint"]
    assert encyclopedia.get_by_id("obsidian")["name_zh"] in advice["training_hint"]
