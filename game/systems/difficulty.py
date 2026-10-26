"""Difficulty manager: speed curve, pattern tier and reaction-gap tuning."""
from __future__ import annotations

from game import config


class DifficultyManager:
    def __init__(self) -> None:
        self.elapsed = 0.0

    def reset(self) -> None:
        self.elapsed = 0.0

    def update(self, dt: float) -> None:
        self.elapsed += dt

    @property
    def multiplier(self) -> float:
        curve = config.DIFFICULTY_CURVE
        t = self.elapsed
        if t >= curve[-1][0]:
            return curve[-1][1]
        for (t0, m0), (t1, m1) in zip(curve, curve[1:]):
            if t0 <= t < t1:
                return m0 + (m1 - m0) * (t - t0) / (t1 - t0)
        return curve[0][1]

    @property
    def speed(self) -> float:
        return min(config.MAX_SPEED, config.INITIAL_SPEED * self.multiplier)

    @property
    def tier(self) -> int:
        """0 = gentle, 1 = intermediate, 2 = full pattern set."""
        return sum(self.elapsed >= t for t in config.TIER_TIMES)

    @property
    def gap_seconds(self) -> float:
        """Reaction time left between obstacle patterns."""
        return max(config.MIN_GAP_SECONDS,
                   config.BASE_GAP_SECONDS - config.GAP_DECAY_PER_SECOND * self.elapsed)
