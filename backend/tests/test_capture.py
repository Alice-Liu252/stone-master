import pytest

from stone_master import capture


def test_success_rate_increases_with_a_better_tool_and_bait():
    weak = capture.success_rate("resonance_orb", None, "common", 1)
    strong = capture.success_rate("legendary_orb", "crystal_powder", "common", 1)
    assert strong > weak


def test_success_rate_decreases_with_rarity():
    common = capture.success_rate("resonance_orb", None, "common", 1)
    legendary = capture.success_rate("resonance_orb", None, "legendary", 1)
    assert legendary < common


def test_success_rate_increases_with_repeated_attempts():
    first = capture.success_rate("resonance_orb", None, "rare", 1)
    fifth = capture.success_rate("resonance_orb", None, "rare", 5)
    assert fifth > first


def test_success_rate_is_clamped_to_bounds():
    assert capture.success_rate("legendary_orb", "crystal_powder", "common", 100) <= capture.MAX_CATCH_RATE
    assert capture.success_rate("resonance_orb", None, "legendary", 1) >= capture.MIN_CATCH_RATE


def test_success_rate_rejects_unknown_inputs():
    with pytest.raises(ValueError):
        capture.success_rate("laser_pointer", None, "common", 1)
    with pytest.raises(ValueError):
        capture.success_rate("resonance_orb", "ketchup", "common", 1)
    with pytest.raises(ValueError):
        capture.success_rate("resonance_orb", None, "mythic", 1)


def test_attempt_is_deterministic_given_the_same_seed():
    a = capture.attempt("resonance_orb", None, "common", 1, seed="fixed-seed")
    b = capture.attempt("resonance_orb", None, "common", 1, seed="fixed-seed")
    assert a == b


def test_attempt_with_near_certain_chance_almost_always_succeeds():
    # legendary_orb + best bait + high attempt_number pushes chance to the
    # MAX_CATCH_RATE ceiling even for a common-rarity stone -- across many
    # independent seeds it should succeed the vast majority of the time.
    outcomes = [
        capture.attempt("legendary_orb", "crystal_powder", "common", 10, seed=f"seed-{i}").success
        for i in range(50)
    ]
    assert sum(outcomes) >= 45  # ~90%+ given MAX_CATCH_RATE == 0.98


def test_attempt_with_low_chance_mostly_fails():
    # weakest tool, no bait, legendary rarity, first try -> 22.5% chance.
    # Expected successes over 50 trials: ~11 (std ~3). Bound below is set
    # with a wide safety margin (>4 std) so this is not a flaky test.
    chance = capture.success_rate("resonance_orb", None, "legendary", 1)
    assert chance == pytest.approx(0.225)
    outcomes = [
        capture.attempt("resonance_orb", None, "legendary", 1, seed=f"seed-{i}").success
        for i in range(50)
    ]
    assert sum(outcomes) <= 25  # clearly under half, even with margin for variance
