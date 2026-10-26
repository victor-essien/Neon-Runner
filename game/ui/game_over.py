"""Game-over screen."""
from __future__ import annotations

import pygame

from game import config
from game.ui.widgets import Fonts, dim_overlay, draw_text

W, H = config.SCREEN_WIDTH, config.SCREEN_HEIGHT


def draw_game_over(surf: pygame.Surface, fonts: Fonts, game) -> None:
    k = min(1.0, game.state_time / 0.6)               # fade/slide-in
    dim_overlay(surf, int(190 * k))
    sc = game.session.scoring
    y = int(70 - 40 * (1 - k))
    draw_text(surf, "GAME OVER", fonts.get(92), config.RED, (W // 2, y), "midtop", glow=config.MAGENTA,
              alpha=int(255 * k))
    if k < 1.0:
        return
    cols = [("SCORE", f"{sc.score:07d}", config.WHITE), ("COINS", str(sc.coins), config.YELLOW),
            ("DISTANCE", f"{sc.distance / 1000:.2f} KM", config.CYAN),
            ("HIGH SCORE", f"{sc.high_score:07d}", config.MAGENTA)]
    for i, (name, value, color) in enumerate(cols):
        x = 260 + i * 250
        draw_text(surf, name, fonts.get(18), config.DIM, (x, 215), "midtop")
        draw_text(surf, value, fonts.get(34), color, (x, 240), "midtop")
    if game.new_record:
        draw_text(surf, "NEW HIGH SCORE!", fonts.get(30), config.YELLOW, (W // 2, 300), "midtop",
                  glow=config.ORANGE)
    if game.state_time >= config.GAME_OVER_INPUT_DELAY_S:
        game.game_over_menu.draw(surf, fonts, W // 2, 370, game.time)
