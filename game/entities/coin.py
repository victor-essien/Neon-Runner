"""Collectible coin."""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from game import config


@dataclass
class Coin:
    lane: int
    z: float
    y: float = config.COIN_HEIGHT
    collected: bool = False
    spin: float = field(default_factory=lambda: random.random() * 6.28)
    prev_z: float = field(init=False)

    def __post_init__(self) -> None:
        self.prev_z = self.z

    def advance(self, distance: float, dt: float) -> None:
        self.prev_z = self.z
        self.z -= distance
        self.spin += dt * 6.0
