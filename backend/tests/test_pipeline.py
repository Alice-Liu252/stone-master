import pytest

from make_test_rocks import make_rock_image
from stone_master.fingerprint_store import FingerprintStore


def _save(tmp_path, seed, name=None):
    path = tmp_path / (name or f"rock_{seed}.png")
    make_rock_image(seed).save(path)
    return path


def test_rescanning_the_same_rock_matches_instead_of_duplicating(tmp_path):
    image = _save(tmp_path, seed=1)
    with FingerprintStore(tmp_path / "store.db") as store:
        first = store.match_or_create("alice", image)
        second = store.match_or_create("alice", image)

    assert first.is_new is True
    assert second.is_new is False
    assert second.record.id == first.record.id
    assert second.similarity == pytest.approx(1.0, abs=1e-3)


def test_two_players_scanning_the_same_rock_get_independent_stones(tmp_path):
    image = _save(tmp_path, seed=1)
    with FingerprintStore(tmp_path / "store.db") as store:
        alice_scan = store.match_or_create("alice", image)
        bob_scan = store.match_or_create("bob", image)

    assert alice_scan.is_new is True
    assert bob_scan.is_new is True
    assert alice_scan.record.id != bob_scan.record.id
    # Same photo -> same deterministic species for both, since generation
    # is a pure function of the fingerprint, not of who's scanning.
    assert alice_scan.record.rarity == bob_scan.record.rarity
    assert alice_scan.record.template_id == bob_scan.record.template_id


def test_different_rocks_are_both_new_and_distinct(tmp_path):
    rock_a = _save(tmp_path, seed=1, name="a.png")
    rock_b = _save(tmp_path, seed=2, name="b.png")
    with FingerprintStore(tmp_path / "store.db") as store:
        a = store.match_or_create("alice", rock_a)
        b = store.match_or_create("alice", rock_b)
        collection = store.list_for_player("alice")

    assert a.is_new and b.is_new
    assert a.record.id != b.record.id
    assert len(collection) == 2


def test_collection_persists_across_store_reopen(tmp_path):
    db_path = tmp_path / "store.db"
    image = _save(tmp_path, seed=3)

    with FingerprintStore(db_path) as store:
        store.match_or_create("alice", image)

    with FingerprintStore(db_path) as store:
        collection = store.list_for_player("alice")

    assert len(collection) == 1
    assert collection[0].discovered_at is not None
