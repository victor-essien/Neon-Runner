"""GameSession: the pure gameplay simulation (no pygame, fully testable)."""
from __future__ import annotations

import random
from typing import Optional

from game.controller.actions import Action
from game.core.events import EventBus, GameEvent
from game.player.player import Player
from game.systems.collision import check_coin_collision, check_obstacle_collision
from game.systems.difficulty import DifficultyManager
from game.systems.scoring import HighScoreStore, Scoring
from game.world.spawner import Spawner
from game.world.world import World

_PLAYER_EVENT_MAP = {
    "lane": GameEvent.LANE_CHANGE,
    "jump": GameEvent.JUMP,
    "slide": GameEvent.SLIDE,
    "land": GameEvent.LAND,
}


class GameSession:
    def __init__(self, bus: Optional[EventBus] = None, store: Optional[HighScoreStore] = None,
                 rng: Optional[random.Random] = None, spawn: bool = True) -> None:
        self.bus = bus or EventBus()
        self.player = Player()
        self.difficulty = DifficultyManager()
        self.world = World(Spawner(rng) if spawn else None)
        self.scoring = Scoring(store)
        self.crashed = False
        self.crashed_by = None
        self.world.update(0.0, 0.0, self.difficulty)   # pre-fill the track

    def reset(self) -> None:
        self.player.reset()
        self.difficulty.reset()
        self.world.reset()
        self.scoring.reset()
        self.crashed = False
        self.crashed_by = None
        self.world.update(0.0, 0.0, self.difficulty)

    @property
    def speed(self) -> float:
        return self.difficulty.speed

    # -- input ----------------------------------------------------------------
    def apply_action(self, action: Action) -> None:
        if self.crashed:
            return
        if action is Action.LEFT:
            self.player.move_left()
        elif action is Action.RIGHT:
            self.player.move_right()
        elif action is Action.JUMP:
            self.player.jump()
        elif action is Action.SLIDE:
            self.player.slide()
        self._flush_player_events()

    # -- simulation -----------------------------------------------------------
    def update(self, dt: float) -> None:
        if self.crashed:
            return
        self.player.update(dt)
        self._flush_player_events()
        self.difficulty.update(dt)
        speed = self.difficulty.speed
        self.world.update(dt, speed, self.difficulty)
        self.scoring.add_distance(speed * dt)

        for obstacle in self.world.obstacles:
            if check_obstacle_collision(self.player, obstacle):
                self.crashed = True
                self.crashed_by = obstacle
                self.bus.publish(GameEvent.CRASH, obstacle=obstacle)
                return

        for coin in self.world.coins:
            if check_coin_collision(self.player, coin):
                coin.collected = True
                self.scoring.add_coin()
                self.bus.publish(GameEvent.COIN, coin=coin)

    def _flush_player_events(self) -> None:
        for name in self.player.pop_events():
            self.bus.publish(_PLAYER_EVENT_MAP[name])
