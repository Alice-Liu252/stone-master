from stone_master import encyclopedia

REQUIRED_FIELDS = {
    "id", "rock_type", "name_zh", "name_en", "sci_name", "color", "texture",
    "hardness", "density", "luster", "composition", "formation", "era",
    "world_locations", "taiwan_locations", "collection_value", "uses",
    "fun_fact",
}


def test_every_species_entry_has_all_required_fields():
    for entry in encyclopedia.SPECIES:
        missing = REQUIRED_FIELDS - entry.keys()
        assert not missing, f"{entry.get('id')} missing fields: {missing}"


def test_every_species_id_is_unique():
    ids = [entry["id"] for entry in encyclopedia.SPECIES]
    assert len(ids) == len(set(ids))


def test_match_entry_is_deterministic():
    a = encyclopedia.match_entry("igneous", seed="abc123")
    b = encyclopedia.match_entry("igneous", seed="abc123")
    assert a["id"] == b["id"]


def test_match_entry_stays_within_requested_bucket():
    for rock_type in ["igneous", "sedimentary", "metamorphic", "mineral"]:
        entry = encyclopedia.match_entry(rock_type, seed="some-seed")
        assert entry["rock_type"] == rock_type


def test_get_by_id_roundtrip():
    entry = encyclopedia.match_entry("mineral", seed="xyz")
    assert encyclopedia.get_by_id(entry["id"]) == entry


def test_get_by_id_unknown_returns_none():
    assert encyclopedia.get_by_id("not-a-real-species") is None


def test_answer_question_is_grounded_in_the_entry():
    entry = encyclopedia.get_by_id("hokutolite")
    assert entry["name_zh"] in encyclopedia.answer_question(entry, "這是什麼石頭？")
    assert entry["formation"] in encyclopedia.answer_question(entry, "如何形成？")
    assert entry["taiwan_locations"] in encyclopedia.answer_question(entry, "哪裡可以找到？")
    assert entry["fun_fact"] in encyclopedia.answer_question(entry, "有什麼特色？")
