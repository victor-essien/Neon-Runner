"""Small movement helpers (easing + lane tween)."""
from __future__ import annotations

from dataclasses import dataclass


def ease_in_out(t: float) -> float:
    """Smoothstep easing for t in [0, 1]."""
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


@dataclass
class LaneTween:
    start: float
    end: float
    duration: float
    elapsed: float = 0.0

    def step(self, dt: float) -> float:
        """Advance and return the current lane position."""
        self.elapsed += dt
        return self.start + (self.end - self.start) * ease_in_out(self.elapsed / self.duration)

    @property
    def done(self) -> bool:
        return self.elapsed >= self.duration
