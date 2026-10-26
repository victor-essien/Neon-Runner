"""Renders the 3-lane world, player, effects and every screen."""
from __future__ import annotations

import math
import random

import pygame

from game import config
from game.core.game_state import GameState
from game.entities.obstacle import ObstacleKind
from game.player.player import PlayerState
from game.rendering.background import Background
from game.rendering.projection import CX, project
from game.rendering.shapes import Color, draw_box, draw_glow, lerp_color, scale_color
from game.ui import game_over, hud, menu, pause
from game.ui.widgets import Fonts, dim_overlay, draw_text

W, H = config.SCREEN_WIDTH, config.SCREEN_HEIGHT
WORLD_STATES = (GameState.COUNTDOWN, GameState.PLAYING, GameState.PAUSED, GameState.GAME_OVER)


def _fog(z: float) -> float:
    return max(0.0, min(1.0, (z - 35.0) / 80.0))


class Renderer:
    def __init__(self, screen: pygame.Surface, fonts: Fonts) -> None:
        self.screen = screen
        self.fonts = fonts
        self.scene = pygame.Surface((W, H)).convert()
        self.background = Background()
        self.vignette = self._make_vignette()
        self.t = 0.0
        rng = random.Random(3)
        self.speed_lines = [(rng.uniform(0, math.tau), rng.random(), rng.uniform(0.6, 1.0)) for _ in range(30)]

    # -- helpers --------------------------------------------------------------------
    @staticmethod
    def _make_vignette() -> pygame.Surface:
        small = pygame.Surface((64, 36), pygame.SRCALPHA)
        for y in range(36):
            for x in range(64):
                d = math.hypot((x - 31.5) / 32, (y - 17.5) / 18)
                small.set_at((x, y), (0, 0, 10, int(max(0.0, d - 0.65) * 230)))
        return pygame.transform.smoothscale(small, (W, H))

    def update(self, dt: float, game) -> None:
        self.t += dt
        self.background.update(dt, game.scroll_speed)

    # -- frame --------------------------------------------------------------------
    def draw(self, game) -> None:
        scene = self.scene
        self.background.draw(scene)
        if game.state in WORLD_STATES:
            self._draw_entities(scene, game)
        self._draw_speed_lines(scene, game)
        game.fx.particles.draw(scene)
        game.fx.draw_texts(scene, self.fonts.get(28))
        scene.blit(self.vignette, (0, 0))

        self.screen.fill((0, 0, 0))
        self.screen.blit(scene, game.fx.shake_offset())
        self._draw_ui(self.screen, game)
        if game.toast_timer > 0:
            self._draw_toast(self.screen, game)
        if game.debug:
            hud.draw_debug(self.screen, self.fonts, game)
        game.fx.draw_overlays(self.screen)

    # -- world ----------------------------------------------------------------------
    def _draw_entities(self, surf: pygame.Surface, game) -> None:
        world = game.session.world
        drawables: list[tuple[float, int, object]] = [(o.z, 0, o) for o in world.obstacles]
        drawables += [(c.z, 1, c) for c in world.coins]
        drawables.append((0.0, 2, None))
        for _, kind, obj in sorted(drawables, key=lambda d: -d[0]):
            if kind == 0:
                self._draw_obstacle(surf, obj)
            elif kind == 1:
                self._draw_coin(surf, obj)
            else:
                self._draw_player(surf, game)
        if game.debug:
            self._draw_debug_boxes(surf, game)

    def _draw_obstacle(self, surf: pygame.Surface, ob) -> None:
        fog = _fog(ob.z)
        x = ob.lane - 1
        z0, z1 = ob.z, ob.z + ob.length

        def tint(c: Color) -> Color:
            return lerp_color(c, config.FOG_COLOR, fog)

        if ob.kind is ObstacleKind.BARRIER:
            base = (230, 90, 40)
            f = draw_box(surf, x - 0.4, x + 0.4, z0, z1, 0, ob.y1, tint(base), tint(scale_color(base, 1.3)),
                         tint(scale_color(base, 0.6)), edge=tint(config.YELLOW))
            y = (f[0][1] + f[3][1]) / 2
            pygame.draw.line(surf, tint(config.YELLOW), (f[0][0], y), (f[1][0], y), 3)
        elif ob.kind is ObstacleKind.OVERHEAD:
            post, bar = (70, 60, 120), (200, 40, 150)
            for px in (x - 0.42, x + 0.34):
                draw_box(surf, px, px + 0.08, z0, z1, 0, ob.y1, tint(post), tint(post), tint(scale_color(post, 0.6)))
            f = draw_box(surf, x - 0.42, x + 0.42, z0, z1, ob.y0, ob.y1, tint(bar), tint(scale_color(bar, 1.3)),
                         tint(scale_color(bar, 0.6)), edge=tint(config.MAGENTA))
            draw_glow(surf, (f[0][0] + f[1][0]) / 2, f[0][1], (f[1][0] - f[0][0]) * 0.8, scale_color(config.MAGENTA, 0.5 * (1 - fog)))
        else:
            base = (52, 84, 150)
            f = draw_box(surf, x - 0.42, x + 0.42, z0, z1, 0, ob.y1, tint(base), tint(scale_color(base, 1.4)),
                         tint(scale_color(base, 0.65)), edge=tint(config.CYAN))
            left, right, bottom, top = f[0][0], f[1][0], f[0][1], f[3][1]
            w, h = right - left, bottom - top
            if w > 14 and ob.z > -3:
                pygame.draw.rect(surf, tint((14, 24, 60)), (left + w * 0.1, top + h * 0.1, w * 0.8, h * 0.36))
                pygame.draw.rect(surf, tint(config.CYAN), (left + w * 0.1, top + h * 0.1, w * 0.8, h * 0.36), 2)
                pygame.draw.rect(surf, tint(config.MAGENTA), (left, bottom - h * 0.32, w, max(2, h * 0.05)))
                for hx in (left + w * 0.18, right - w * 0.18):
                    draw_glow(surf, hx, bottom - h * 0.16, w * 0.14, scale_color(config.YELLOW, 1 - fog))

    def _draw_coin(self, surf: pygame.Surface, coin) -> None:
        sx, sy, s = project(coin.lane - 1, coin.z, coin.y)
        r = 0.27 * config.PX_PER_M * s
        if r < 1.5:
            return
        w = max(2.0, abs(math.cos(coin.spin)) * r)
        fog = _fog(coin.z)
        gold = lerp_color(config.YELLOW, config.FOG_COLOR, fog)
        rect = pygame.Rect(0, 0, w * 2, r * 2)
        rect.center = (sx, sy)
        pygame.draw.ellipse(surf, gold, rect)
        pygame.draw.ellipse(surf, lerp_color((255, 245, 180), config.FOG_COLOR, fog), rect, max(1, int(r * 0.2)))
        if s > 0.35:
            draw_glow(surf, sx, sy, r * 2.2, scale_color(config.YELLOW, 0.35))

    def _draw_player(self, surf: pygame.Surface, game) -> None:
        p = game.session.player
        if game.session.crashed and int(game.state_time * 14) % 2:
            return
        pose = game.animator.pose(p)
        x, fy, s = project(p.lane_pos - 1, 0, p.y)
        gx, gy, _ = project(p.lane_pos - 1, 0, 0)
        h = config.PX_PER_M
        k = 1.0 - min(1.0, p.y / 1.8) * 0.5
        shadow = pygame.Surface((int(0.9 * h), int(0.28 * h)), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, int(140 * k)), shadow.get_rect())
        surf.blit(shadow, shadow.get_rect(center=(gx, gy)))

        suit, accent, dark = config.CYAN, config.MAGENTA, (12, 12, 40)
        sq = 1.0 - pose.squash
        lean = pose.lean * 0.25 * h

        def Y(m: float) -> float:
            return fy - m * h * sq

        def limb(a, b, color, w) -> None:
            pygame.draw.line(surf, dark, a, b, w + 4)
            pygame.draw.line(surf, color, a, b, w)

        lw = int(0.15 * h)
        if pose.state is PlayerState.SLIDING:
            hip, sh = (x - 0.15 * h, Y(0.3)), (x - 0.55 * h, Y(0.5))
            head = (x - 0.75 * h, Y(0.62))
            for k_, col in ((1, scale_color(suit, 0.6)), (0, suit)):
                foot = (x + 0.7 * h, Y(0.08 + 0.1 * k_))
                limb(hip, ((hip[0] + foot[0]) / 2, Y(0.32 - 0.1 * k_)), col, lw)
                limb(((hip[0] + foot[0]) / 2, Y(0.32 - 0.1 * k_)), foot, col, lw)
            limb(hip, sh, accent, int(lw * 1.6))
            limb(sh, (x - 0.1 * h, Y(0.15)), suit, int(lw * 0.8))
        else:
            hip = (x + lean * 0.4, Y(0.95))
            sh = (x + lean, Y(1.5))
            head = (sh[0] + lean * 0.2, Y(1.72))
            for k_ in (1, 0):
                col = scale_color(suit, 0.6) if k_ else suit
                if pose.state is PlayerState.JUMPING:
                    foot = (x + (0.22 if k_ else -0.18) * h, Y(0.55 if k_ else 0.4))
                    hand = (sh[0] + (0.4 if k_ else -0.4) * h, Y(1.95))
                else:
                    a = pose.phase + k_ * math.pi
                    foot = (x + math.sin(a) * 0.32 * h, fy - max(0.0, math.cos(a)) * 0.28 * h)
                    hand = (sh[0] - math.sin(a) * 0.3 * h, Y(1.05 + 0.15 * math.cos(a)))
                knee = ((hip[0] + foot[0]) / 2 + 0.06 * h, (hip[1] + foot[1]) / 2)
                limb(hip, knee, col, lw)
                limb(knee, foot, col, lw)
                limb(sh, hand, col, int(lw * 0.8))
            limb(hip, sh, accent, int(lw * 1.7))
        pygame.draw.circle(surf, dark, (int(head[0]), int(head[1])), int(0.2 * h))
        pygame.draw.circle(surf, suit, (int(head[0]), int(head[1])), int(0.17 * h))
        pygame.draw.rect(surf, accent, (head[0] - 0.12 * h, head[1] - 0.03 * h, 0.24 * h, 0.06 * h), border_radius=3)
        draw_glow(surf, head[0], head[1], 0.5 * h, scale_color(accent, 0.35))

    def _draw_debug_boxes(self, surf: pygame.Surface, game) -> None:
        for ob in game.session.world.obstacles:
            x = ob.lane - 1
            pts = [project(x + dx, ob.z, y)[:2] for dx, y in
                   ((-0.5, ob.y0), (0.5, ob.y0), (0.5, ob.y1), (-0.5, ob.y1))]
            pygame.draw.polygon(surf, config.GREEN, pts, 1)
        p = game.session.player
        pts = [project(p.lane_pos - 1 + dx, 0, y)[:2] for dx, y in
               ((-0.3, p.y), (0.3, p.y), (0.3, p.y + p.height), (-0.3, p.y + p.height))]
        pygame.draw.polygon(surf, config.RED, pts, 2)

    def _draw_speed_lines(self, surf: pygame.Surface, game) -> None:
        speed = game.scroll_speed
        if speed < 18:
            return
        n = min(len(self.speed_lines), int((speed - 14) * 1.6))
        for angle, phase, length in self.speed_lines[:n]:
            f = (self.t * speed * 0.03 + phase) % 1.0
            r0 = 160 + f * 720
            r1 = r0 + 30 + 160 * length * f
            a = (math.cos(angle), math.sin(angle) * 0.6)
            c = (CX + a[0] * r0, config.HORIZON_Y + 60 + a[1] * r0)
            e = (CX + a[0] * r1, config.HORIZON_Y + 60 + a[1] * r1)
            pygame.draw.line(surf, (60 + int(60 * f), 40 + int(40 * f), 120 + int(60 * f)), c, e, 2)

    # -- UI ------------------------------------------------------------------------
    def _draw_ui(self, screen: pygame.Surface, game) -> None:
        st = game.state
        f = self.fonts
        if st is GameState.BOOT:
            dim_overlay(screen, 130)
            menu.draw_boot(screen, f, game)
        elif st is GameState.MAIN_MENU:
            dim_overlay(screen, 90)
            menu.draw_main_menu(screen, f, game)
        elif st is GameState.CONTROLS:
            dim_overlay(screen, 205)
            menu.draw_controls(screen, f, game)
        elif st is GameState.SETTINGS:
            dim_overlay(screen, 200)
            menu.draw_settings(screen, f, game)
        else:
            hud.draw_hud(screen, f, game)
            if st is GameState.COUNTDOWN:
                self._draw_countdown(screen, game)
            elif st is GameState.PAUSED:
                pause.draw_pause(screen, f, game)
            elif st is GameState.GAME_OVER:
                game_over.draw_game_over(screen, f, game)

    def _draw_countdown(self, screen: pygame.Surface, game) -> None:
        k = (game.state_time % config.COUNTDOWN_STEP_S) / config.COUNTDOWN_STEP_S
        size = int(170 * (1.35 - 0.35 * min(1.0, k * 2)))
        go = game.countdown_label == "RUN!"
        draw_text(screen, game.countdown_label, self.fonts.get(size), config.GREEN if go else config.WHITE,
                  (W // 2, 250), "center", glow=config.CYAN if not go else config.GREEN,
                  alpha=int(255 * (1 - max(0.0, k - 0.7) / 0.3)))

    def _draw_toast(self, screen: pygame.Surface, game) -> None:
        font = self.fonts.get(22)
        img = font.render(game.toast_text, True, config.WHITE)
        rect = img.get_rect(midbottom=(W // 2, H - 26)).inflate(36, 18)
        bg = pygame.Surface(rect.size, pygame.SRCALPHA)
        bg.fill((10, 6, 40, 220))
        screen.blit(bg, rect)
        pygame.draw.rect(screen, config.CYAN, rect, 2, border_radius=8)
        screen.blit(img, img.get_rect(center=rect.center))
