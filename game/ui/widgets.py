"""Shared UI helpers: fonts, text drawing and arrow icons."""
from __future__ import annotations

import pygame

from game import config


class Fonts:
    """Lazy font cache. Uses assets/fonts/*.ttf when present, else a system font."""

    CANDIDATES = "bahnschrift,segoeuisemibold,dejavusansmono,arial,helvetica"

    def __init__(self) -> None:
        self._cache: dict[int, pygame.font.Font] = {}
        custom = sorted((config.ASSETS_DIR / "fonts").glob("*.ttf"))
        self._path = str(custom[0]) if custom else pygame.font.match_font(self.CANDIDATES, bold=True)

    def get(self, size: int) -> pygame.font.Font:
        font = self._cache.get(size)
        if font is None:
            try:
                font = pygame.font.Font(self._path, size)
            except (OSError, TypeError):
                font = pygame.font.Font(None, int(size * 1.2))
            self._cache[size] = font
        return font


def draw_text(surf: pygame.Surface, text: str, font: pygame.font.Font, color, pos, anchor: str = "topleft",
              glow=None, alpha: int = 255) -> pygame.Rect:
    img = font.render(text, True, color)
    rect = img.get_rect()
    setattr(rect, anchor, pos)
    if glow is not None:
        halo = font.render(text, True, glow)
        halo.set_alpha(110)
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-2, 2), (2, 2)):
            surf.blit(halo, rect.move(dx, dy))
    if alpha < 255:
        img.set_alpha(alpha)
    surf.blit(img, rect)
    return rect


def draw_arrow(surf: pygame.Surface, direction: str, center, size: int, color, width: int = 0) -> None:
    """direction in {'left','right','up','down'}."""
    cx, cy = center
    s = size / 2
    pts = {
        "left": [(cx - s, cy), (cx + s * 0.6, cy - s), (cx + s * 0.6, cy + s)],
        "right": [(cx + s, cy), (cx - s * 0.6, cy - s), (cx - s * 0.6, cy + s)],
        "up": [(cx, cy - s), (cx - s, cy + s * 0.6), (cx + s, cy + s * 0.6)],
        "down": [(cx, cy + s), (cx - s, cy - s * 0.6), (cx + s, cy - s * 0.6)],
    }[direction]
    pygame.draw.polygon(surf, color, pts, width)


def dim_overlay(surf: pygame.Surface, alpha: int) -> None:
    overlay = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    overlay.fill((4, 2, 18, alpha))
    surf.blit(overlay, (0, 0))
