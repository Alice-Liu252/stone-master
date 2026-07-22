# Backend prototype (Phase 0)

Runnable proof of the scan pipeline described in
[../docs/TECHNICAL_ARCHITECTURE.md](../docs/TECHNICAL_ARCHITECTURE.md) section 3 —
photo in, deterministic 3D-character-ready data out — without needing Unity,
Node, or a real database. This is scaffolding to validate pipeline *logic*,
not production code: see [Limitations](#limitations) before reusing any of it
as-is.

## What's here

| Module | Role |
|---|---|
| `stone_master/vision.py` | Turns a photo into a deterministic feature vector + perceptual hash (color/texture/shape stats — not a trained classifier) |
| `stone_master/rules.py` | Rarity table, elemental attributes, base 3D template library, base stat ranges — plain data, tune freely |
| `stone_master/generation.py` | Deterministic species generation: same fingerprint always yields the same rarity/element/stats/template |
| `stone_master/fingerprint_store.py` | SQLite-backed per-player store; `match_or_create()` is the full "did we see this rock before?" pipeline |
| `stone_master/encyclopedia.py` | AI 石頭百科 (GDD 第 5 章): 10 real rock/mineral entries + template-based Q&A, grounded only in that data — no invented facts |
| `stone_master/assistant.py` | AI 個人化助手 (GDD 第 19 章): persona wrapper for encyclopedia answers ("小晶"), plus `recommend()` — analyzes a player's real collection and suggests what to explore/train next |
| `scripts/make_test_rocks.py` | Generates synthetic speckled-blob rock photos (no real rock dataset available in this environment) |
| `scripts/scan_demo.py` | CLI that runs the full scan pipeline end to end against a real image file |
| `scripts/ask_demo.py` | CLI: ask a scanned stone "這是什麼石頭？" etc., answered by 小晶 from real encyclopedia data |
| `scripts/assistant_demo.py` | CLI: get 小晶's personalized recommendation based on a player's whole collection |

## Setup

```bash
python3 -m pip install -r requirements.txt
```

## Try it

```bash
# generate a few synthetic test photos
python3 scripts/make_test_rocks.py --count 5 --out data/test_rocks

# scan one — first time is always new
python3 scripts/scan_demo.py --player alice --image data/test_rocks/rock_1.png

# scan the exact same photo again — should come back as a match, not a duplicate
python3 scripts/scan_demo.py --player alice --image data/test_rocks/rock_1.png

# ask 小晶 (the AI assistant) about the stone you just scanned (use the id it printed)
python3 scripts/ask_demo.py --player alice --stone-id 1 --question "這是什麼石頭？"
python3 scripts/ask_demo.py --player alice --stone-id 1 --list-questions

# get a personalized recommendation based on your whole collection
python3 scripts/assistant_demo.py --player alice
```

## Tests

```bash
python3 -m pip install -r requirements.txt
python3 -m pytest -v
```

Covers: deterministic feature extraction, deterministic generation, rescanning
the same rock matches instead of duplicating, two players scanning the same
rock get independent instances, collections persist across store reopen,
encyclopedia answers are grounded in the real data (not invented), and
personalized recommendations are deterministic for a given collection.

## Limitations

This is a Phase 0 logic prototype, built inside an environment with no Node,
Docker, or Unity available — see [../docs/ROADMAP.md](../docs/ROADMAP.md).
Before any of this ships:

- **No real rock photos were used to tune anything.** All thresholds
  (`HAMMING_PREFILTER_THRESHOLD`, `COSINE_MATCH_THRESHOLD` in
  `fingerprint_store.py`) are placeholders. They need calibration against a
  real corpus of the same rock photographed from different angles/lighting.
- **`rock_type` classification is a toy heuristic**, not a trained model —
  see the docstring in `vision.py`. It cannot actually tell igneous from
  sedimentary rock; that needs a labeled geology image dataset and real
  training, per `docs/TECHNICAL_ARCHITECTURE.md` section 1.
- **Matching is global-scan-per-player, O(player's collection size)** — fine
  for a prototype, but the real system should use pgvector (or similar) once
  collections get large, per `docs/TECHNICAL_ARCHITECTURE.md` section 9.
- **No API layer.** This is called as a Python library / CLI, not over
  HTTP. Wiring it behind an API and picking the production backend language
  (Node/Go per the architecture doc) is separate work.
- **Encyclopedia matching only picks among 10 hand-written entries**, and
  since the rock_type heuristic above is a toy, most synthetic test photos
  end up bucketed the same way — don't read much into which real species a
  synthetic photo gets matched to. `stone_master/encyclopedia.py` Q&A is
  template-based, not a real LLM/RAG system (see `docs/TECHNICAL_ARCHITECTURE.md`
  section 5 for what that should eventually be).
