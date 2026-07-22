"""Deterministic stone species generation.

Given the visual features of a rock the player has never seen before,
always produce the same species/appearance/stats for that exact feature
vector — generation must be a pure function of the fingerprint, never a
fresh coin flip, or re-running the pipeline (retries, cache misses) could
mint two different creatures out of one rock. See
docs/TECHNICAL_ARCHITECTURE.md section 3 for where this sits in the scan
pipeline, and section 4 for the base-template + material-projection
approach this stands in for on the 3D-rendering side.
"""
from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from typing import Dict

from . import encyclopedia, rules
from .vision import Features


@dataclass(frozen=True)
class StoneSpecies:
    seed: str
    rock_type: str
    template_id: str
    rarity: str
    element: str
    stats: Dict[str, int]
    encyclopedia_id: str  # links to a real-world species in encyclopedia.py

    def to_dict(self) -> dict:
        return {
            "seed": self.seed,
            "rock_type": self.rock_type,
            "template_id": self.template_id,
            "rarity": self.rarity,
            "element": self.element,
            "stats": self.stats,
            "encyclopedia_id": self.encyclopedia_id,
        }


def _seed_from_embedding(features: Features) -> str:
    return hashlib.sha256(features.embedding.tobytes()).hexdigest()


def _weighted_choice(rng: random.Random, table) -> str:
    names, weights = zip(*table)
    return rng.choices(names, weights=weights, k=1)[0]


def _rock_type_hint(features: Features) -> str:
    """Toy heuristic mapping crude texture/shape stats to a rock-type
    bucket, standing in for the trained classifier described in
    docs/TECHNICAL_ARCHITECTURE.md section 1 ("雲端視覺辨識服務"). Do not
    treat this as real geology classification — see vision.py docstring."""
    if features.fill_ratio > 0.75 and features.roughness < 0.15:
        return "mineral"
    if features.roughness > 0.35:
        return "igneous"
    if features.aspect_ratio > 1.6 or features.aspect_ratio < 0.6:
        return "metamorphic"
    return "sedimentary"


def generate_species(features: Features) -> StoneSpecies:
    seed_hex = _seed_from_embedding(features)
    rng = random.Random(seed_hex)

    rock_type = _rock_type_hint(features)
    candidates = [t for t in rules.BASE_TEMPLATES if t["rock_type"] == rock_type]
    template = rng.choice(candidates or rules.BASE_TEMPLATES)

    rarity = _weighted_choice(rng, rules.RARITY_TABLE)
    multiplier = rules.RARITY_STAT_MULTIPLIER[rarity]
    element = rng.choice(rules.ELEMENTS)

    stats = {
        stat: round(rng.randint(*bounds) * multiplier)
        for stat, bounds in rules.BASE_STAT_RANGES.items()
    }

    encyclopedia_entry = encyclopedia.match_entry(rock_type, seed_hex)

    return StoneSpecies(
        seed=seed_hex,
        rock_type=rock_type,
        template_id=template["id"],
        rarity=rarity,
        element=element,
        stats=stats,
        encyclopedia_id=encyclopedia_entry["id"],
    )
