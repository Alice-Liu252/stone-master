"""Per-player fingerprint store and match-or-create scan pipeline.

Stands in for the pgvector-backed matching described in
docs/TECHNICAL_ARCHITECTURE.md sections 3 and 9, using SQLite so the
prototype runs with zero external services. The matching *scope is
per-player, not global* — see docs/TECHNICAL_ARCHITECTURE.md section 3:
two different players scanning the same real rock each get their own
independent stone_instance, so there's no "first to scan it wins" race.

Similarity thresholds below are placeholders. They need to be calibrated
against a real corpus of photos of the same rock taken from different
angles/lighting before this ships — see docs/ROADMAP.md Phase 0 exit
criteria.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Union

import numpy as np

from . import vision
from .generation import generate_species
from .vision import Features

HAMMING_PREFILTER_THRESHOLD = 10  # out of 64 bits
COSINE_MATCH_THRESHOLD = 0.90

SCHEMA = """
CREATE TABLE IF NOT EXISTS stone_instances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id TEXT NOT NULL,
    phash_hex TEXT NOT NULL,
    embedding_json TEXT NOT NULL,
    rock_type TEXT NOT NULL,
    template_id TEXT NOT NULL,
    rarity TEXT NOT NULL,
    element TEXT NOT NULL,
    stats_json TEXT NOT NULL,
    level INTEGER NOT NULL DEFAULT 1,
    exp INTEGER NOT NULL DEFAULT 0,
    affinity INTEGER NOT NULL DEFAULT 0,
    discovered_at TEXT NOT NULL,
    last_seen_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_stone_player ON stone_instances(player_id);
"""


@dataclass(frozen=True)
class StoneRecord:
    id: int
    player_id: str
    rock_type: str
    template_id: str
    rarity: str
    element: str
    stats: dict
    level: int
    exp: int
    affinity: int
    discovered_at: str
    last_seen_at: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "player_id": self.player_id,
            "rock_type": self.rock_type,
            "template_id": self.template_id,
            "rarity": self.rarity,
            "element": self.element,
            "stats": self.stats,
            "level": self.level,
            "exp": self.exp,
            "affinity": self.affinity,
            "discovered_at": self.discovered_at,
            "last_seen_at": self.last_seen_at,
        }


@dataclass(frozen=True)
class ScanResult:
    is_new: bool
    record: StoneRecord
    similarity: Optional[float]  # None when is_new (nothing to compare to)


def _row_to_record(row: sqlite3.Row) -> StoneRecord:
    return StoneRecord(
        id=row["id"],
        player_id=row["player_id"],
        rock_type=row["rock_type"],
        template_id=row["template_id"],
        rarity=row["rarity"],
        element=row["element"],
        stats=json.loads(row["stats_json"]),
        level=row["level"],
        exp=row["exp"],
        affinity=row["affinity"],
        discovered_at=row["discovered_at"],
        last_seen_at=row["last_seen_at"],
    )


class FingerprintStore:
    """SQLite-backed store of scanned stones, scoped per player."""

    def __init__(self, db_path: Union[str, Path] = ":memory:"):
        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "FingerprintStore":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def _find_best_match(
        self, player_id: str, features: Features
    ) -> Optional[tuple]:
        rows = self._conn.execute(
            "SELECT * FROM stone_instances WHERE player_id = ?", (player_id,)
        ).fetchall()

        best_row, best_similarity = None, 0.0
        for row in rows:
            candidate_phash = int(row["phash_hex"], 16)
            if (
                vision.hamming_distance(features.phash, candidate_phash)
                > HAMMING_PREFILTER_THRESHOLD
            ):
                continue
            candidate_embedding = json.loads(row["embedding_json"])
            similarity = vision.cosine_similarity(
                features.embedding, np.array(candidate_embedding)
            )
            if similarity > best_similarity:
                best_row, best_similarity = row, similarity

        if best_row is not None and best_similarity >= COSINE_MATCH_THRESHOLD:
            return best_row, best_similarity
        return None

    def match_or_create(
        self, player_id: str, image: Union[str, Path]
    ) -> ScanResult:
        features = vision.extract_features(image)
        match = self._find_best_match(player_id, features)
        now = datetime.now(timezone.utc).isoformat()

        if match is not None:
            row, similarity = match
            self._conn.execute(
                "UPDATE stone_instances SET last_seen_at = ? WHERE id = ?",
                (now, row["id"]),
            )
            self._conn.commit()
            refreshed = self._conn.execute(
                "SELECT * FROM stone_instances WHERE id = ?", (row["id"],)
            ).fetchone()
            return ScanResult(
                is_new=False, record=_row_to_record(refreshed), similarity=similarity
            )

        species = generate_species(features)
        cursor = self._conn.execute(
            """
            INSERT INTO stone_instances (
                player_id, phash_hex, embedding_json, rock_type, template_id,
                rarity, element, stats_json, discovered_at, last_seen_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                player_id,
                format(features.phash, "016x"),
                json.dumps(features.embedding_list()),
                species.rock_type,
                species.template_id,
                species.rarity,
                species.element,
                json.dumps(species.stats),
                now,
                now,
            ),
        )
        self._conn.commit()
        created = self._conn.execute(
            "SELECT * FROM stone_instances WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
        return ScanResult(is_new=True, record=_row_to_record(created), similarity=None)

    def list_for_player(self, player_id: str) -> list:
        rows = self._conn.execute(
            "SELECT * FROM stone_instances WHERE player_id = ? ORDER BY id",
            (player_id,),
        ).fetchall()
        return [_row_to_record(r) for r in rows]
