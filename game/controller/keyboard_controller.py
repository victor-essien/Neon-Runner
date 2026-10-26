"""Keyboard fallback: pygame key events -> Actions."""
from __future__ import annotations

from typing import Optional

import pygame

from game.controller.actions import Action

KEY_MAP: dict[int, Action] = {
    pygame.K_a: Action.LEFT, pygame.K_LEFT: Action.LEFT,
    pygame.K_d: Action.RIGHT, pygame.K_RIGHT: Action.RIGHT,
    pygame.K_w: Action.JUMP, pygame.K_UP: Action.JUMP, pygame.K_SPACE: Action.JUMP,
    pygame.K_s: Action.SLIDE, pygame.K_DOWN: Action.SLIDE,
    pygame.K_ESCAPE: Action.PAUSE, pygame.K_p: Action.PAUSE,
    pygame.K_RETURN: Action.START, pygame.K_KP_ENTER: Action.START,
}


class KeyboardController:
    def handle_event(self, event: pygame.event.Event) -> Optional[Action]:
        if event.type == pygame.KEYDOWN and not getattr(event, "repeat", False):
            return KEY_MAP.get(event.key)
        return None
