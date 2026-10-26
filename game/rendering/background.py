"""Procedural neon-city background: sky, skyline, track, rails and side buildings."""
from __future__ import annotations

import math
import random

import pygame

from game import config
from game.rendering.projection import project
from game.rendering.shapes import Color, draw_box, draw_glow, lerp_color, scale_color

W, H = config.SCREEN_WIDTH, config.SCREEN_HEIGHT
SPAN = 150.0                      # z-length of the recycled building strip
SLEEPER_GAP = 2.4
ACCENTS: list[Color] = [config.CYAN, config.MAGENTA, config.YELLOW, (120, 255, 160), (255, 120, 80)]


class Background:
    def __init__(self, seed: int = 7) -> None:
        self.rng = random.Random(seed)
        self.scroll = 0.0
        self.time = 0.0
        self.sky = self._make_sky()
        self.ground = self._make_ground()
        self.stars = [(self.rng.randrange(W), self.rng.randrange(0, config.HORIZON_Y - 30),
                       self.rng.random() * 6.28) for _ in range(70)]
        self.buildings: list[dict] = []
        for side in (-1, 1):
            z = self.rng.uniform(-6, 4)
            while z < SPAN:
                b = self._new_building(side, z)
                self.buildings.append(b)
                z += b["depth"] + self.rng.uniform(1.5, 4.0)

    # -- static surfaces --------------------------------------------------------
    def _make_sky(self) -> pygame.Surface:
        s = pygame.Surface((W, config.HORIZON_Y + 2)).convert()
        top, mid, low = (6, 4, 28), (38, 14, 80), (150, 40, 130)
        for y in range(config.HORIZON_Y + 2):
            t = y / config.HORIZON_Y
            c = lerp_color(top, mid, t / 0.6) if t < 0.6 else lerp_color(mid, low, (t - 0.6) / 0.4)
            pygame.draw.line(s, c, (0, y), (W, y))
        cx, cy, r = W // 2, config.HORIZON_Y - 10, 120          # retro sun
        for i in range(r, 0, -2):
            k = i / r
            pygame.draw.circle(s, lerp_color((255, 220, 90), (255, 50, 150), k),
                               (cx, cy), i)
        for i in range(8):                                       # sun stripes
            y = cy - 10 + i * 14
            pygame.draw.rect(s, lerp_color(mid, low, 0.75), (cx - r, y, r * 2, 2 + i))
        glow = pygame.Surface((W, config.HORIZON_Y + 2))
        pygame.draw.ellipse(glow, (70, 20, 60), (cx - 380, cy - 40, 760, 120))
        s.blit(glow, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        x = 0                                                    # skyline silhouettes
        while x < W:
            w = self.rng.randint(30, 90)
            h = self.rng.randint(25, 120)
            pygame.draw.rect(s, (12, 8, 38), (x, config.HORIZON_Y - h, w, h + 2))
            for wy in range(config.HORIZON_Y - h + 6, config.HORIZON_Y - 4, 9):
                for wx in range(x + 5, x + w - 5, 9):
                    if self.rng.random() < 0.22:
                        pygame.draw.rect(s, self.rng.choice(((255, 200, 110), (90, 220, 255))), (wx, wy, 3, 4))
            x += w + self.rng.randint(0, 6)
        return s

    def _make_ground(self) -> pygame.Surface:
        h = H - config.HORIZON_Y
        s = pygame.Surface((W, h)).convert()
        for y in range(h):
            pygame.draw.line(s, lerp_color((52, 18, 84), (6, 4, 22), (y / h) ** 0.6), (0, y), (W, y))
        return s

    def _new_building(self, side: int, z: float) -> dict:
        rng = self.rng
        w = rng.uniform(1.8, 3.6)
        h = rng.uniform(6, 24)
        cols, rows = rng.randint(3, 6), max(3, int(h / 2.4))
        return {
            "side": side, "z": z, "inner": rng.uniform(2.35, 3.1), "w": w, "depth": rng.uniform(6, 11), "h": h,
            "color": rng.choice(((24, 18, 64), (30, 20, 76), (20, 24, 70))), "accent": rng.choice(ACCENTS),
            "cols": cols, "rows": rows,
            "lit": [rng.random() < 0.45 for _ in range(cols * rows)],
        }

    # -- update / draw ------------------------------------------------------------
    def update(self, dt: float, speed: float) -> None:
        self.time += dt
        self.scroll += speed * dt
        for b in self.buildings:
            b["z"] -= speed * dt
            if b["z"] + b["depth"] < -14:
                b.update(self._new_building(b["side"], b["z"] + SPAN))

    def draw(self, surf: pygame.Surface) -> None:
        surf.blit(self.sky, (0, 0))
        for x, y, ph in self.stars:
            k = 0.5 + 0.5 * math.sin(self.time * 2 + ph)
            c = int(90 + 140 * k)
            surf.set_at((x, y), (c, c, min(255, c + 20)))
        surf.blit(self.ground, (0, config.HORIZON_Y))
        self._draw_track(surf)
        self._draw_buildings(surf)

    def _draw_track(self, surf: pygame.Surface) -> None:
        far, near = 160.0, -12.0
        bed = [project(-1.75, far)[:2], project(1.75, far)[:2], project(1.75, near)[:2], project(-1.75, near)[:2]]
        pygame.draw.polygon(surf, (20, 14, 46), bed)
        phase = self.scroll % SLEEPER_GAP
        z = near - phase
        while z < 120:
            if z > -10:
                a, b = z, z + 0.35
                quad = [project(-1.6, a)[:2], project(1.6, a)[:2], project(1.6, b)[:2], project(-1.6, b)[:2]]
                fog = min(1.0, max(0.0, z / 120))
                pygame.draw.polygon(surf, lerp_color((70, 46, 100), config.FOG_COLOR, fog), quad)
            z += SLEEPER_GAP
        for lane in (-1, 0, 1):
            for off in (-0.3, 0.3):
                p0, p1 = project(lane + off, far), project(lane + off, near)
                pygame.draw.line(surf, (110, 110, 160), p0[:2], p1[:2], 3)
        for x in (-1.5, -0.5, 0.5, 1.5):                        # neon lane dividers
            p0, p1 = project(x, far), project(x, near)
            pygame.draw.line(surf, (18, 80, 110), p0[:2], p1[:2], 7)
            pygame.draw.line(surf, config.CYAN, p0[:2], p1[:2], 2)

    def _draw_buildings(self, surf: pygame.Surface) -> None:
        for b in sorted(self.buildings, key=lambda q: -q["z"]):
            z0, z1 = max(b["z"], -8.0), b["z"] + b["depth"]
            if z1 < -8 or z0 > 150:
                continue
            fog = min(1.0, max(0.0, (b["z"] - 25) / 110))
            x0, x1 = (b["inner"], b["inner"] + b["w"]) if b["side"] > 0 else (-b["inner"] - b["w"], -b["inner"])
            base = lerp_color(b["color"], config.FOG_COLOR, fog)
            front = draw_box(surf, x0, x1, z0, z1, 0, b["h"], base, scale_color(base, 1.5),
                             scale_color(base, 0.7), edge=lerp_color(b["accent"], config.FOG_COLOR, fog * 0.9))
            sx0, sx1 = front[0][0], front[1][0]
            sy_bot, sy_top = front[0][1], front[3][1]
            if sx1 - sx0 > 26 and b["z"] > -3:
                self._draw_windows(surf, b, sx0, sx1, sy_top, sy_bot, fog)

    def _draw_windows(self, surf, b, x0, x1, y0, y1, fog) -> None:
        cols, rows = b["cols"], b["rows"]
        cw, rh = (x1 - x0) / cols, (y1 - y0) / rows
        lit_c = lerp_color((255, 205, 120), config.FOG_COLOR, fog)
        for r in range(rows):
            for c in range(cols):
                if b["lit"][r * cols + c]:
                    pygame.draw.rect(surf, lit_c, (x0 + c * cw + cw * 0.25, y0 + r * rh + rh * 0.25, cw * 0.5, rh * 0.45))
