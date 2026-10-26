"""Player state: lanes, jump physics and sliding. Pure logic (no pygame)."""
from __future__ import annotations

from enum import Enum
from typing import Optional

from game import config
from game.player.movement import LaneTween


class PlayerState(Enum):
    RUNNING = "running"
    JUMPING = "jumping"
    SLIDING = "sliding"


class Player:
    """The runner. Lane positions are in lane units (0, 1, 2); height ``y`` is metres."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.lane = config.START_LANE          # target lane
        self.lane_pos = float(self.lane)       # smoothed visual/collision position
        self.y = 0.0
        self.vy = 0.0
        self.grounded = True
        self.state = PlayerState.RUNNING
        self.slide_timer = 0.0
        self._tween: Optional[LaneTween] = None
        self._jump_buffer = 0.0
        self._slide_pending = False
        self._events: list[str] = []

    # -- derived --------------------------------------------------------------
    @property
    def height(self) -> float:
        """Current collision height (reduced while sliding)."""
        return config.SLIDE_HEIGHT if self.state is PlayerState.SLIDING else config.PLAYER_HEIGHT

    def pop_events(self) -> list[str]:
        events, self._events = self._events, []
        return events

    # -- commands -------------------------------------------------------------
    def move(self, direction: int) -> bool:
        """Change lane by -1/+1. Out-of-range requests are ignored."""
        target = self.lane + direction
        if not 0 <= target < config.LANE_COUNT:
            return False
        self.lane = target
        self._tween = LaneTween(self.lane_pos, float(target), config.LANE_CHANGE_DURATION)
        self._events.append("lane")
        return True

    def move_left(self) -> bool:
        return self.move(-1)

    def move_right(self) -> bool:
        return self.move(+1)

    def jump(self) -> bool:
        """Jump if grounded (no double jump). An early press is buffered briefly."""
        if not self.grounded:
            self._jump_buffer = config.JUMP_BUFFER_S
            return False
        self.vy = config.JUMP_FORCE
        self.grounded = False
        self.state = PlayerState.JUMPING
        self.slide_timer = 0.0
        self._events.append("jump")
        return True

    def slide(self) -> bool:
        """Slide if grounded. Airborne: fast-fall and slide on landing."""
        if not self.grounded:
            self._slide_pending = True
            self.vy = min(self.vy, -config.FAST_FALL_SPEED)
            return False
        if self.state is PlayerState.SLIDING:
            return False
        self.state = PlayerState.SLIDING
        self.slide_timer = config.SLIDE_DURATION
        self._events.append("slide")
        return True

    # -- simulation -----------------------------------------------------------
    def update(self, dt: float) -> None:
        if self._tween is not None:
            self.lane_pos = self._tween.step(dt)
            if self._tween.done:
                self.lane_pos = float(self.lane)
                self._tween = None

        if not self.grounded:
            self.vy += config.GRAVITY * dt
            self.y += self.vy * dt
            self._jump_buffer = max(0.0, self._jump_buffer - dt)
            if self.y <= 0.0:
                self.y = 0.0
                self.vy = 0.0
                self.grounded = True
                self.state = PlayerState.RUNNING
                self._events.append("land")
                if self._slide_pending:
                    self._slide_pending = False
                    self.slide()
                elif self._jump_buffer > 0.0:
                    self._jump_buffer = 0.0
                    self.jump()
        elif self.state is PlayerState.SLIDING:
            self.slide_timer -= dt
            if self.slide_timer <= 0.0:
                self.slide_timer = 0.0
                self.state = PlayerState.RUNNING
