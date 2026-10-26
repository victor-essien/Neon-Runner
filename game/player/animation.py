"""Procedural animation state for the runner (consumed by the renderer)."""
from __future__ import annotations

from dataclasses import dataclass

from game.player.player import Player, PlayerState


@dataclass
class Pose:
    state: PlayerState
    phase: float      # run-cycle phase in radians
    lean: float       # -1..1 sideways lean while changing lanes
    squash: float     # 0..0.3 landing squash


class PlayerAnimator:
    def __init__(self) -> None:
        self.phase = 0.0
        self.lean = 0.0
        self.squash = 0.0
        self._last_lane_pos = 1.0

    def reset(self, player: Player) -> None:
        self.phase = 0.0
        self.lean = 0.0
        self.squash = 0.0
        self._last_lane_pos = player.lane_pos

    def on_land(self) -> None:
        self.squash = 0.25

    def update(self, dt: float, player: Player, speed: float) -> None:
        self.phase += dt * (6.0 + speed * 0.5)
        if dt > 0:
            vel = (player.lane_pos - self._last_lane_pos) / dt
            self.lean += (max(-1.0, min(1.0, vel / 5.0)) - self.lean) * min(1.0, dt * 14)
        self._last_lane_pos = player.lane_pos
        self.squash = max(0.0, self.squash - dt * 1.4)

    def pose(self, player: Player) -> Pose:
        return Pose(player.state, self.phase, self.lean, self.squash)
