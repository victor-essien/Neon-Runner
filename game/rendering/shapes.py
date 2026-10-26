"""Drawing helpers: colour math, 3D-ish boxes and cached glow sprites."""
from __future__ import annotations

import pygame

from game import config
from game.rendering.projection import project

Color = tuple[int, int, int]


def lerp_color(a: Color, b: Color, t: float) -> Color:
    t = max(0.0, min(1.0, t))
    return (int(a[0] + (b[0] - a[0]) * t), int(a[1] + (b[1] - a[1]) * t), int(a[2] + (b[2] - a[2]) * t))


def scale_color(c: Color, k: float) -> Color:
    return (max(0, min(255, int(c[0] * k))), max(0, min(255, int(c[1] * k))), max(0, min(255, int(c[2] * k))))


def draw_box(surf: pygame.Surface, x0: float, x1: float, z0: float, z1: float, y0: float, y1: float,
             front: Color, top: Color, side: Color, edge: Color | None = None) -> list[tuple[float, float]]:
    """Draw an axis-aligned box seen from the camera. Returns the front-face polygon."""
    def P(x: float, z: float, y: float) -> tuple[float, float]:
        sx, sy, _ = project(x, z, y)
        return sx, sy

    f = [P(x0, z0, y0), P(x1, z0, y0), P(x1, z0, y1), P(x0, z0, y1)]
    b = [P(x0, z1, y0), P(x1, z1, y0), P(x1, z1, y1), P(x0, z1, y1)]
    if x1 < 0:
        pygame.draw.polygon(surf, side, [f[1], b[1], b[2], f[2]])
    elif x0 > 0:
        pygame.draw.polygon(surf, side, [f[0], b[0], b[3], f[3]])
    if y1 < config.EYE_HEIGHT:
        pygame.draw.polygon(surf, top, [f[3], f[2], b[2], b[3]])
    pygame.draw.polygon(surf, front, f)
    if edge is not None:
        pygame.draw.polygon(surf, edge, f, 2)
        if y1 < config.EYE_HEIGHT:
            pygame.draw.lines(surf, edge, False, [f[3], b[3], b[2], f[2]], 1)
    return f


_glow_cache: dict[tuple[int, Color], pygame.Surface] = {}


def glow_sprite(radius: int, color: Color) -> pygame.Surface:
    key = (radius, color)
    sprite = _glow_cache.get(key)
    if sprite is None:
        sprite = pygame.Surface((radius * 2, radius * 2)).convert()
        sprite.fill((0, 0, 0))
        steps = max(4, radius // 2)
        for i in range(steps):
            r = radius * (1 - i / steps)
            k = (i / steps) ** 2 * 0.9
            pygame.draw.circle(sprite, scale_color(color, k), (radius, radius), int(r))
        _glow_cache[key] = sprite
    return sprite


def draw_glow(surf: pygame.Surface, x: float, y: float, radius: float, color: Color) -> None:
    r = int(radius)
    if r < 3:
        return
    r = min(r, 160)
    r = (r // 4) * 4 or 4          # bucket radii so the cache stays small
    surf.blit(glow_sprite(r, color), (x - r, y - r), special_flags=pygame.BLEND_RGB_ADD)
