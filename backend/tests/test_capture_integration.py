from make_test_rocks import make_rock_image
from stone_master.fingerprint_store import FingerprintStore


def test_failed_capture_persists_nothing(tmp_path):
    image = tmp_path / "rock.png"
    make_rock_image(1).save(image)

    with FingerprintStore(tmp_path / "s.db") as store:
        found_failure = False
        found_success = False
        # Independent players (fresh identity each time) rolling against
        # the same rock at base difficulty should show a mix of outcomes,
        # since the seed mixes in player_id -- if it didn't, every player
        # would get an identical yes/no on the same rock.
        for i in range(30):
            player = f"player-{i}"
            result = store.attempt_capture(player, image, tool="resonance_orb", bait=None, attempt_number=1)
            if result.outcome == "failed":
                found_failure = True
                assert result.record is None
                assert result.species_preview is not None
                assert result.species_preview["rarity"]
                assert store.list_for_player(player) == []
            else:
                found_success = True
                assert result.outcome == "captured"
                assert result.record is not None
                assert store.list_for_player(player) != []

        assert found_failure, "expected at least one failed attempt across 30 independent players"
        assert found_success, "expected at least one successful attempt across 30 independent players"


def test_different_players_get_independent_rolls_on_the_same_rock(tmp_path):
    image = tmp_path / "rock.png"
    make_rock_image(2).save(image)

    with FingerprintStore(tmp_path / "s.db") as store:
        outcomes = {
            store.attempt_capture(f"p{i}", image, tool="resonance_orb", bait=None, attempt_number=1).outcome
            for i in range(20)
        }
    # if outcomes were NOT player-independent, this set would have only
    # one element (everyone gets the same result on the same rock)
    assert len(outcomes) > 1


def test_recognized_stone_is_not_re_rolled(tmp_path):
    image = tmp_path / "rock.png"
    make_rock_image(3).save(image)

    with FingerprintStore(tmp_path / "s.db") as store:
        first = store.attempt_capture(
            "alice", image, tool="legendary_orb", bait="crystal_powder", attempt_number=10
        )
        assert first.outcome == "captured"

        second = store.attempt_capture("alice", image, tool="resonance_orb", bait=None, attempt_number=1)
        assert second.outcome == "recognized"
        assert second.record.id == first.record.id
        assert second.chance is None  # no roll happened, it's already yours


def test_retrying_after_a_failure_can_eventually_succeed(tmp_path):
    image = tmp_path / "rock.png"
    make_rock_image(4).save(image)

    with FingerprintStore(tmp_path / "s.db") as store:
        # sweep attempt_number upward with a strong loadout until capture
        # succeeds -- proves retries actually get a fresh roll and the
        # familiarity bonus (higher attempt_number) helps.
        result = None
        for attempt_number in range(1, 40):
            result = store.attempt_capture(
                "alice", image, tool="legendary_orb", bait="crystal_powder", attempt_number=attempt_number
            )
            if result.outcome == "captured":
                break

        assert result.outcome == "captured"
        assert store.list_for_player("alice") != []
