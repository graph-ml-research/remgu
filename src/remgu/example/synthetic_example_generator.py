# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Create reproducible lightweight synthetic examples for UI demonstrations."""
import random


class SyntheticExampleGenerator:
    """Generate small numeric examples without writing to any persistent sample pool."""

    def generate(self, count: int, *, seed: int = 0, feature_count: int = 4) -> list[dict[str, object]]:
        """Return deterministic synthetic records held only in memory."""
        if count < 0: raise ValueError("count must be non-negative")
        if feature_count < 1: raise ValueError("feature_count must be positive")
        randomizer = random.Random(seed)
        return [{"example_id": f"synthetic-{seed}-{index}",
                 "features": [round(randomizer.random(), 6) for _ in range(feature_count)],
                 "label": randomizer.randrange(2), "synthetic": True} for index in range(count)]
