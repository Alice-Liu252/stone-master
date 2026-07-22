from make_test_rocks import make_rock_image
from stone_master.fingerprint_store import FingerprintStore


def _new_stone(store, tmp_path, player="alice", seed=1):
    image = tmp_path / f"rock_{seed}.png"
    make_rock_image(seed).save(image)
    return store.match_or_create(player, image).record


def test_care_for_updates_exp_affinity_mood_and_diary(tmp_path):
    with FingerprintStore(tmp_path / "s.db") as store:
        stone = _new_stone(store, tmp_path)
        updated = store.care_for("alice", stone.id, "feed")

        assert updated.exp == stone.exp + 8
        assert updated.affinity == stone.affinity + 3
        assert updated.feed_count == 1
        assert len(updated.diary) == 1
        assert updated.diary[0]  # non-empty flavor text


def test_care_for_unknown_stone_returns_none(tmp_path):
    with FingerprintStore(tmp_path / "s.db") as store:
        assert store.care_for("alice", 999, "feed") is None


def test_care_for_invalid_action_raises(tmp_path):
    import pytest

    with FingerprintStore(tmp_path / "s.db") as store:
        stone = _new_stone(store, tmp_path)
        with pytest.raises(ValueError):
            store.care_for("alice", stone.id, "dance")


def test_care_for_is_scoped_to_the_right_player(tmp_path):
    with FingerprintStore(tmp_path / "s.db") as store:
        stone = _new_stone(store, tmp_path, player="alice")
        assert store.care_for("bob", stone.id, "feed") is None


def test_personality_shifts_toward_the_favored_action(tmp_path):
    with FingerprintStore(tmp_path / "s.db") as store:
        stone = _new_stone(store, tmp_path)
        for _ in range(6):
            stone = store.care_for("alice", stone.id, "play")
        assert stone.personality == "活潑"


def test_evolve_requires_thresholds_then_persists(tmp_path):
    with FingerprintStore(tmp_path / "s.db") as store:
        stone = _new_stone(store, tmp_path)
        original_template = stone.template_id

        assert store.evolve("alice", stone.id) is None  # fresh stone, not eligible yet

        # fast-forward directly to an evolution-eligible state (test-only
        # shortcut -- normal play reaches this through many care_for calls)
        store._conn.execute(
            "UPDATE stone_instances SET level = 10, affinity = 50 WHERE id = ?", (stone.id,)
        )
        store._conn.commit()

        evolved = store.evolve("alice", stone.id)
        assert evolved is not None
        assert evolved.evolved is True
        assert evolved.template_id == f"{original_template}_evolved"

        # evolving an already-evolved stone does nothing further
        assert store.evolve("alice", stone.id) is None
