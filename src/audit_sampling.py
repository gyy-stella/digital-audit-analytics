"""Risk-based sample selection with deterministic coverage."""

from __future__ import annotations

import random
from typing import Any


def select_samples(rows: list[dict[str, Any]], sample_size: int, seed: int = 42) -> list[dict[str, Any]]:
    """Select 70% top-risk items and 30% reproducible lower-risk coverage."""
    if sample_size <= 0:
        return []
    ordered = sorted(rows, key=lambda x: (float(x["risk_score"]), abs(float(x["amount"]))), reverse=True)
    targeted_n = min(len(ordered), max(1, round(sample_size * 0.7)))
    selected = [dict(row) for row in ordered[:targeted_n]]
    remainder = ordered[targeted_n:]
    rng = random.Random(seed)
    random_n = min(sample_size - len(selected), len(remainder))
    selected.extend(dict(row) for row in rng.sample(remainder, random_n))
    for index, row in enumerate(selected, 1):
        row["sample_id"] = f"S-{index:03d}"
        row["selection_basis"] = "Targeted: highest risk" if index <= targeted_n else "Random: population coverage"
    return selected
