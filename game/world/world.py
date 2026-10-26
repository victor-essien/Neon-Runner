"""World container: moves obstacles/coins toward the player and culls them."""
from __future__ import annotations

from typing import Optional

from game import config
from game.entities.coin import Coin
from game.entities.obstacle import Obstacle


class World:
    def __init__(self, spawner=None) -> None:
        self.spawner = spawner
        self.obstacles: list[Obstacle] = []
        self.coins: list[Coin] = []

    def reset(self) -> None:
        self.obstacles.clear()
        self.coins.clear()
        if self.spawner is not None:
            self.spawner.reset()

    def add_obstacle(self, obstacle: Obstacle) -> Obstacle:
        self.obstacles.append(obstacle)
        return obstacle

    def add_coin(self, coin: Coin) -> Coin:
        self.coins.append(coin)
        return coin

    def update(self, dt: float, speed: float, difficulty: Optional[object] = None) -> None:
        distance = speed * dt
        for ob in self.obstacles:
            ob.advance(distance)
        for coin in self.coins:
            coin.advance(distance, dt)
        self.obstacles = [o for o in self.obstacles if o.z + o.length > config.DESPAWN_Z]
        self.coins = [c for c in self.coins if c.z > config.DESPAWN_Z and not c.collected]
        if self.spawner is not None and difficulty is not None:
            self.spawner.update(dt, speed, difficulty, self)
