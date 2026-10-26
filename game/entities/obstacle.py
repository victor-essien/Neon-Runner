"""Obstacle entities. ``z`` is the distance ahead of the player in metres."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from game import config


class ObstacleKind(Enum):
    BARRIER = "barrier"      # jump over (or change lane)
    OVERHEAD = "overhead"    # slide under (or change lane)
    TRAIN = "train"          # change lane


@dataclass
class Obstacle:
    kind: ObstacleKind
    lane: int
    z: float
    length: float
    y0: float
    y1: float
    prev_z: float = field(init=False)

    def __post_init__(self) -> None:
        self.prev_z = self.z

    def advance(self, distance: float) -> None:
        self.prev_z = self.z
        self.z -= distance

    @classmethod
    def barrier(cls, lane: int, z: float) -> "Obstacle":
        return cls(ObstacleKind.BARRIER, lane, z, config.BARRIER_DEPTH, 0.0, config.BARRIER_HEIGHT)

    @classmethod
    def overhead(cls, lane: int, z: float) -> "Obstacle":
        return cls(ObstacleKind.OVERHEAD, lane, z, config.BARRIER_DEPTH,
                   config.OVERHEAD_BOTTOM, config.OVERHEAD_TOP)

    @classmethod
    def train(cls, lane: int, z: float, length: float) -> "Obstacle":
        return cls(ObstacleKind.TRAIN, lane, z, length, 0.0, config.TRAIN_HEIGHT)
