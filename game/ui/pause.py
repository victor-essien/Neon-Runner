"""Pause overlay."""
from __future__ import annotations

import pygame

from game import config
from game.ui.widgets import Fonts, dim_overlay, draw_text

W, H = config.SCREEN_WIDTH, config.SCREEN_HEIGHT


def draw_pause(surf: pygame.Surface, fonts: Fonts, game) -> None:
    dim_overlay(surf, 170)
    draw_text(surf, "PAUSED", fonts.get(84), config.WHITE, (W // 2, 140), "midtop", glow=config.CYAN)
    game.pause_menu.draw(surf, fonts, W // 2, 300, game.time)
