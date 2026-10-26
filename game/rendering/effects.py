"""Particles, floating text, screen shake, flash and fade effects."""
from __future__ import annotations

import math
import random

import pygame

from game.rendering.shapes import Color, scale_color

MAX_PARTICLES = 400


class ParticleSystem:
    """Fixed-cap particle pool: [x, y, vx, vy, life, max_life, size, color, gravity]."""

    def __init__(self) -> None:
        self.p: list[list] = []

    def emit(self, x: float, y: float, color: Color, count: int, speed: float = 160.0,
             life: float = 0.5, size: float = 3.0, gravity: float = 350.0,
             angle: float | None = None, spread: float = math.tau) -> None:
        for _ in range(count):
            if len(self.p) >= MAX_PARTICLES:
                return
            a = (angle if angle is not None else 0.0) + random.uniform(-spread / 2, spread / 2)
            v = speed * random.uniform(0.3, 1.0)
            l = life * random.uniform(0.6, 1.0)
            self.p.append([x, y, math.cos(a) * v, math.sin(a) * v, l, l, size * random.uniform(0.6, 1.2),
                           color, gravity])

    def update(self, dt: float) -> None:
        alive = []
        for q in self.p:
            q[4] -= dt
            if q[4] > 0:
                q[3] += q[8] * dt
                q[0] += q[2] * dt
                q[1] += q[3] * dt
                alive.append(q)
        self.p = alive

    def draw(self, surf: pygame.Surface) -> None:
        for x, y, _, _, life, max_life, size, color, _ in self.p:
            k = life / max_life
            pygame.draw.circle(surf, scale_color(color, 0.35 + 0.65 * k), (int(x), int(y)), max(1, int(size * (0.4 + 0.6 * k))))


class Effects:
    """Bundles every transient visual effect."""

    def __init__(self) -> None:
        self.particles = ParticleSystem()
        self.texts: list[list] = []          # [text, x, y, t, life, color]
        self.trauma = 0.0
        self.flash_alpha = 0.0
        self.fade_alpha = 0.0
        self.fade_speed = 0.0
        self._trail_t = 0.0

    # -- triggers -------------------------------------------------------------
    def burst(self, x, y, color, count=24, speed=260, life=0.7, size=4.0) -> None:
        self.particles.emit(x, y, color, count, speed=speed, life=life, size=size)

    def dust(self, x, y, count=8) -> None:
        self.particles.emit(x, y, (170, 150, 220), count, speed=110, life=0.45, size=3, gravity=-40,
                            angle=-math.pi / 2, spread=math.pi)

    def sparks(self, x, y, color, count=10) -> None:
        self.particles.emit(x, y, color, count, speed=200, life=0.4, size=2.5, gravity=500,
                            angle=-math.pi / 2, spread=math.pi * 0.9)

    def trail(self, dt: float, x: float, y: float, color: Color) -> None:
        self._trail_t += dt
        if self._trail_t >= 0.04:
            self._trail_t = 0.0
            self.particles.emit(x, y, color, 1, speed=60, life=0.35, size=3, gravity=240,
                                angle=math.pi / 2, spread=0.6)

    def text(self, text: str, x: float, y: float, color: Color) -> None:
        self.texts.append([text, x, y, 0.0, 0.9, color])

    def shake(self, amount: float = 1.0) -> None:
        self.trauma = min(1.0, self.trauma + amount)

    def flash(self, alpha: float = 200.0) -> None:
        self.flash_alpha = alpha

    def fade_in(self, duration: float = 0.35) -> None:
        self.fade_alpha = 255.0
        self.fade_speed = 255.0 / duration

    # -- per frame ------------------------------------------------------------
    def update(self, dt: float) -> None:
        self.particles.update(dt)
        for t in self.texts:
            t[3] += dt
            t[2] -= 60 * dt
        self.texts = [t for t in self.texts if t[3] < t[4]]
        self.trauma = max(0.0, self.trauma - dt * 1.8)
        self.flash_alpha = max(0.0, self.flash_alpha - dt * 500)
        self.fade_alpha = max(0.0, self.fade_alpha - self.fade_speed * dt)

    def shake_offset(self) -> tuple[int, int]:
        m = self.trauma ** 2 * 18
        return (int(random.uniform(-m, m)), int(random.uniform(-m, m))) if m > 0.3 else (0, 0)

    def draw_texts(self, surf: pygame.Surface, font: pygame.font.Font) -> None:
        for text, x, y, t, life, color in self.texts:
            img = font.render(text, True, color)
            img.set_alpha(int(255 * (1 - t / life)))
            surf.blit(img, img.get_rect(center=(x, y)))

    def draw_overlays(self, surf: pygame.Surface) -> None:
        if self.flash_alpha > 1:
            overlay = pygame.Surface(surf.get_size())
            overlay.fill((255, 255, 255))
            overlay.set_alpha(int(self.flash_alpha))
            surf.blit(overlay, (0, 0))
        if self.fade_alpha > 1:
            overlay = pygame.Surface(surf.get_size())
            overlay.set_alpha(int(self.fade_alpha))
            surf.blit(overlay, (0, 0))
