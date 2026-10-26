"""In-run HUD and debug overlay."""
from __future__ import annotations

import pygame

from game import config
from game.ui.widgets import Fonts, draw_text

W = config.SCREEN_WIDTH
_bar: pygame.Surface | None = None


def _top_bar() -> pygame.Surface:
    global _bar
    if _bar is None:
        _bar = pygame.Surface((W, 92), pygame.SRCALPHA)
        for y in range(92):
            pygame.draw.line(_bar, (4, 2, 20, int(150 * (1 - y / 92))), (0, y), (W, y))
    return _bar


def draw_hud(surf: pygame.Surface, fonts: Fonts, game) -> None:
    sc = game.session.scoring
    surf.blit(_top_bar(), (0, 0))
    label, value = fonts.get(16), fonts.get(40)
    draw_text(surf, "SCORE", label, config.CYAN, (40, 14))
    draw_text(surf, f"{sc.score:07d}", value, config.WHITE, (40, 32), glow=config.CYAN)
    draw_text(surf, "COINS", label, config.YELLOW, (W // 2, 14), "midtop")
    pygame.draw.circle(surf, config.YELLOW, (W // 2 - 44, 56), 11)
    pygame.draw.circle(surf, (255, 240, 160), (W // 2 - 44, 56), 11, 2)
    draw_text(surf, f"{sc.coins}", value, config.WHITE, (W // 2 - 22, 56), "midleft")
    draw_text(surf, "SPEED", label, config.MAGENTA, (W - 40, 14), "topright")
    draw_text(surf, f"{game.session.speed / config.INITIAL_SPEED:.2f}", value, config.WHITE, (W - 40, 32),
              "topright", glow=config.MAGENTA)


def draw_debug(surf: pygame.Surface, fonts: Fonts, game) -> None:
    p, s = game.session.player, game.session
    lines = [
        f"FPS {game.clock.fps:5.1f}   STATE {game.state.name}",
        f"LANE {p.lane} (pos {p.lane_pos:.2f})  PLAYER {p.state.value}  y={p.y:.2f}",
        f"SPEED {s.speed:.1f} m/s   t={s.difficulty.elapsed:.0f}s   tier {s.difficulty.tier}",
        f"OBSTACLES {len(s.world.obstacles)}   COINS {len(s.world.coins)}   PARTICLES {len(game.fx.particles.p)}",
        f"SERIAL {game.input.serial.status_text if game.input.serial else 'n/a'}",
    ]
    for i, line in enumerate(lines):
        draw_text(surf, line, fonts.get(16), config.GREEN, (14, 100 + i * 20))
