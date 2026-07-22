from datetime import datetime, timedelta, timezone

from stone_master import growth


def test_level_from_exp():
    assert growth.level_from_exp(0) == 1
    assert growth.level_from_exp(99) == 1
    assert growth.level_from_exp(100) == 2
    assert growth.level_from_exp(250) == 3


def test_exp_to_next_level():
    assert growth.exp_to_next_level(0) == 100
    assert growth.exp_to_next_level(80) == 20
    assert growth.exp_to_next_level(100) == 100


def test_decayed_mood_is_unchanged_with_no_elapsed_time():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert growth.decayed_mood(80, now.isoformat(), now=now) == 80


def test_decayed_mood_drops_over_days():
    last = datetime(2026, 1, 1, tzinfo=timezone.utc)
    now = last + timedelta(days=4)
    assert growth.decayed_mood(80, last.isoformat(), now=now) == 80 - 4 * growth.MOOD_DECAY_PER_DAY


def test_decayed_mood_never_goes_below_zero():
    last = datetime(2026, 1, 1, tzinfo=timezone.utc)
    now = last + timedelta(days=100)
    assert growth.decayed_mood(50, last.isoformat(), now=now) == 0


def test_personality_defaults_to_shy_with_little_interaction():
    assert growth.personality(1, 0, 0, 0) == "怕生"


def test_personality_reflects_dominant_action():
    assert growth.personality(feed_count=10, play_count=1, clean_count=1, sleep_count=1) == "親人"
    assert growth.personality(feed_count=1, play_count=10, clean_count=1, sleep_count=1) == "活潑"
    assert growth.personality(feed_count=1, play_count=1, clean_count=10, sleep_count=10) == "穩重"


def test_can_evolve_requires_both_thresholds():
    assert not growth.can_evolve(level=5, affinity=80)
    assert not growth.can_evolve(level=15, affinity=10)
    assert growth.can_evolve(level=10, affinity=50)


def test_apply_action_rejects_unknown_action():
    import pytest

    with pytest.raises(ValueError):
        growth.apply_action("dance", 0, 0, 70, datetime.now(timezone.utc).isoformat())


def test_apply_action_deltas_are_deterministic():
    now_iso = datetime.now(timezone.utc).isoformat()
    a = growth.apply_action("feed", current_exp=0, current_affinity=0, current_mood=70, last_interaction_at=now_iso)
    b = growth.apply_action("feed", current_exp=0, current_affinity=0, current_mood=70, last_interaction_at=now_iso)
    assert (a.exp, a.affinity, a.mood, a.level, a.leveled_up) == (b.exp, b.affinity, b.mood, b.level, b.leveled_up)


def test_apply_action_feed_effect():
    now_iso = datetime.now(timezone.utc).isoformat()
    update = growth.apply_action("feed", current_exp=0, current_affinity=0, current_mood=70, last_interaction_at=now_iso)
    assert update.exp == 8
    assert update.affinity == 3
    assert update.mood == 85  # 70 + 15, no decay since last_interaction_at is "now"
    assert update.level == 1
    assert not update.leveled_up


def test_apply_action_reports_level_up():
    now_iso = datetime.now(timezone.utc).isoformat()
    update = growth.apply_action("feed", current_exp=95, current_affinity=0, current_mood=50, last_interaction_at=now_iso)
    assert update.exp == 103
    assert update.level == 2
    assert update.leveled_up
    assert "Lv.2" in update.diary_entry


def test_affinity_is_capped_at_100():
    now_iso = datetime.now(timezone.utc).isoformat()
    update = growth.apply_action("play", current_exp=0, current_affinity=98, current_mood=50, last_interaction_at=now_iso)
    assert update.affinity == 100
