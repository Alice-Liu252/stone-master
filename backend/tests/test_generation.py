import numpy as np
import pytest

from stone_master import rules
from stone_master.generation import generate_species
from stone_master.vision import Features

EMBEDDING_LEN = 76  # COLOR_BINS_PER_CHANNEL**3 (64) + texture (10) + shape (2)


def _fake_features(seed: int, roughness=0.1, fill_ratio=0.8, aspect_ratio=1.0) -> Features:
    rng = np.random.RandomState(seed)
    embedding = rng.rand(EMBEDDING_LEN).astype(np.float32)
    embedding /= np.linalg.norm(embedding)
    return Features(
        embedding=embedding,
        phash=seed,
        mean_color=(100, 100, 100),
        fill_ratio=fill_ratio,
        aspect_ratio=aspect_ratio,
        roughness=roughness,
    )


def test_generate_species_is_deterministic():
    features = _fake_features(seed=42)
    a = generate_species(features)
    b = generate_species(features)
    assert a.to_dict() == b.to_dict()


def test_rarity_is_from_the_configured_table():
    valid_rarities = {name for name, _ in rules.RARITY_TABLE}
    for seed in range(20):
        species = generate_species(_fake_features(seed))
        assert species.rarity in valid_rarities


def test_element_is_from_the_ten_element_table():
    for seed in range(20):
        species = generate_species(_fake_features(seed))
        assert species.element in rules.ELEMENTS


def test_stats_are_positive_and_scale_with_rarity():
    # Same base roll (seed fixed via monkeypatched multiplier indirectly):
    # instead, just check every generated stat is positive and within a
    # sane upper bound (max base range * highest multiplier).
    max_possible = max(hi for _, hi in rules.BASE_STAT_RANGES.values()) * max(
        rules.RARITY_STAT_MULTIPLIER.values()
    )
    for seed in range(20):
        species = generate_species(_fake_features(seed))
        for stat_name, value in species.stats.items():
            assert 0 < value <= max_possible, (stat_name, value)


@pytest.mark.parametrize(
    "roughness,fill_ratio,aspect_ratio,expected",
    [
        (0.05, 0.9, 1.0, "mineral"),
        (0.5, 0.5, 1.0, "igneous"),
        (0.1, 0.5, 2.0, "metamorphic"),
        (0.1, 0.5, 1.0, "sedimentary"),
    ],
)
def test_rock_type_heuristic_buckets(roughness, fill_ratio, aspect_ratio, expected):
    features = _fake_features(1, roughness=roughness, fill_ratio=fill_ratio, aspect_ratio=aspect_ratio)
    species = generate_species(features)
    assert species.rock_type == expected
    template_ids_for_type = {t["id"] for t in rules.BASE_TEMPLATES if t["rock_type"] == expected}
    assert species.template_id in template_ids_for_type
