"""Frame clock returning a clamped delta time in seconds."""
from __future__ import annotations

import pygame

from game import config


class FrameClock:
    def __init__(self, fps: int = config.FPS, max_dt: float = config.MAX_FRAME_DT) -> None:
        self._clock = pygame.time.Clock()
        self._fps = fps
        self._max_dt = max_dt

    def tick(self) -> float:
        """Advance one frame; returns dt in seconds (clamped)."""
        return min(self._clock.tick(self._fps) / 1000.0, self._max_dt)

    @property
    def fps(self) -> float:
        return self._clock.get_fps()
