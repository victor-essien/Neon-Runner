"""Procedural pattern spawner. Guarantees every row is passable."""
from __future__ import annotations

import math
import random
from typing import Optional

from game import config
from game.entities.coin import Coin
from game.entities.obstacle import Obstacle, ObstacleKind

LANES = list(range(config.LANE_COUNT))


def row_is_passable(row: list[Obstacle]) -> bool:
    """A row (obstacles at the same depth) is fair if the player can always get through.

    Fair means: at least one lane is empty, OR there are no trains and every
    obstacle needs the same action (all jump or all slide).
    """
    blocked = {o.lane for o in row}
    if len(blocked) < config.LANE_COUNT:
        return True
    if any(o.kind is ObstacleKind.TRAIN for o in row):
        return False
    return len({o.kind for o in row}) == 1


class Spawner:
    def __init__(self, rng: Optional[random.Random] = None) -> None:
        self.rng = rng or random.Random()
        self.cursor = config.SPAWN_START_Z

    def reset(self) -> None:
        self.cursor = config.SPAWN_START_Z

    # -- main loop --------------------------------------------------------------
    def update(self, dt: float, speed: float, difficulty, world) -> None:
        self.cursor -= speed * dt
        while self.cursor <= config.SPAWN_Z:
            length = self._spawn_pattern(world, self.cursor, difficulty, speed)
            self.cursor += length + difficulty.gap_seconds * speed

    # -- pattern selection ------------------------------------------------------
    def _spawn_pattern(self, world, z: float, difficulty, speed: float) -> float:
        tier = difficulty.tier
        table = [(self._single_barrier, 3), (self._single_overhead, 2),
                 (self._coin_line, 3), (self._coin_arc, 1)]
        if tier >= 1:
            table += [(self._two_barriers, 2), (self._two_overheads, 1), (self._train, 2),
                      (self._coin_arc, 2), (self._mixed, 1)]
        if tier >= 2:
            table += [(self._two_trains, 2), (self._full_barrier_row, 1),
                      (self._full_overhead_row, 1), (self._mixed, 2)]
        funcs, weights = zip(*table)
        pattern = self.rng.choices(funcs, weights=weights, k=1)[0]
        return pattern(world, z, difficulty.gap_seconds * speed)

    # -- helpers ----------------------------------------------------------------
    def _place_row(self, world, row: list[Obstacle]) -> None:
        """Add a row, dropping obstacles until it is passable (safety net)."""
        while row and not row_is_passable(row):
            row.pop()
        for ob in row:
            world.add_obstacle(ob)

    def _coin_run(self, world, lane: int, z: float, count: int, spacing: float = 2.2) -> None:
        for i in range(count):
            world.add_coin(Coin(lane, z + i * spacing))

    def _arc_over(self, world, lane: int, z: float, count: int = 5, spacing: float = 1.3) -> None:
        for i in range(count):
            h = config.COIN_HEIGHT + 0.9 * math.sin(math.pi * i / (count - 1))
            world.add_coin(Coin(lane, z + i * spacing, y=h))

    # -- patterns (each returns the pattern length in metres) -----------------------
    def _single_barrier(self, world, z, gap) -> float:
        self._place_row(world, [Obstacle.barrier(self.rng.choice(LANES), z)])
        return 1.0

    def _single_overhead(self, world, z, gap) -> float:
        self._place_row(world, [Obstacle.overhead(self.rng.choice(LANES), z)])
        return 1.0

    def _two_barriers(self, world, z, gap) -> float:
        lanes = self.rng.sample(LANES, 2)
        self._place_row(world, [Obstacle.barrier(l, z) for l in lanes])
        return 1.0

    def _two_overheads(self, world, z, gap) -> float:
        lanes = self.rng.sample(LANES, 2)
        self._place_row(world, [Obstacle.overhead(l, z) for l in lanes])
        return 1.0

    def _train(self, world, z, gap) -> float:
        lane = self.rng.choice(LANES)
        length = self.rng.uniform(config.TRAIN_MIN_LENGTH, config.TRAIN_MAX_LENGTH)
        self._place_row(world, [Obstacle.train(lane, z, length)])
        free = self.rng.choice([l for l in LANES if l != lane])
        self._coin_run(world, free, z, int(length / 2.2))
        return length

    def _two_trains(self, world, z, gap) -> float:
        lanes = self.rng.sample(LANES, 2)
        length = self.rng.uniform(config.TRAIN_MIN_LENGTH, config.TRAIN_MAX_LENGTH)
        self._place_row(world, [Obstacle.train(l, z, length) for l in lanes])
        free = next(l for l in LANES if l not in lanes)
        self._coin_run(world, free, z, int(length / 2.2))
        return length

    def _coin_line(self, world, z, gap) -> float:
        count = self.rng.randint(5, 8)
        self._coin_run(world, self.rng.choice(LANES), z, count)
        return count * 2.2

    def _coin_arc(self, world, z, gap) -> float:
        lane = self.rng.choice(LANES)
        self._place_row(world, [Obstacle.barrier(lane, z + 2.6)])
        self._arc_over(world, lane, z)
        return 6.0

    def _mixed(self, world, z, gap) -> float:
        a, b, _ = self.rng.sample(LANES, 3)
        self._place_row(world, [Obstacle.barrier(a, z), Obstacle.overhead(b, z)])
        z2 = z + gap            # second row after one full reaction gap
        c = self.rng.choice(LANES)
        self._place_row(world, [Obstacle.barrier(c, z2)])
        return z2 - z + 1.0

    def _full_barrier_row(self, world, z, gap) -> float:
        self._place_row(world, [Obstacle.barrier(l, z) for l in LANES])
        self._arc_over(world, 1, z - 1.2, count=4, spacing=0.8)
        return 1.0

    def _full_overhead_row(self, world, z, gap) -> float:
        self._place_row(world, [Obstacle.overhead(l, z) for l in LANES])
        return 1.0
