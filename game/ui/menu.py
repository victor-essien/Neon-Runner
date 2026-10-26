"""Reusable vertical menu + the main-menu, controls and boot screens."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

import pygame

from game import config
from game.controller.actions import Action
from game.ui.widgets import Fonts, draw_arrow, draw_text

W, H = config.SCREEN_WIDTH, config.SCREEN_HEIGHT


@dataclass
class MenuItem:
    key: str
    label: str


class Menu:
    """Controller-friendly menu: JUMP/SLIDE move, RIGHT/START select, LEFT/PAUSE back."""

    def __init__(self, items: list[MenuItem]) -> None:
        self.items = items
        self.index = 0

    @property
    def selected(self) -> MenuItem:
        return self.items[self.index]

    def handle(self, action: Action) -> Optional[tuple[str, str]]:
        n = len(self.items)
        if action is Action.JUMP:
            self.index = (self.index - 1) % n
            return "move", self.selected.key
        if action is Action.SLIDE:
            self.index = (self.index + 1) % n
            return "move", self.selected.key
        if action in (Action.RIGHT, Action.START):
            return "select", self.selected.key
        if action in (Action.LEFT, Action.PAUSE):
            return "back", self.selected.key
        return None

    def draw(self, surf: pygame.Surface, fonts: Fonts, cx: int, top: int, t: float,
             width: int = 420, height: int = 54, gap: int = 14) -> None:
        font = fonts.get(28)
        for i, item in enumerate(self.items):
            rect = pygame.Rect(0, 0, width, height)
            rect.midtop = (cx, top + i * (height + gap))
            sel = i == self.index
            pulse = 0.5 + 0.5 * math.sin(t * 6)
            body = pygame.Surface(rect.size, pygame.SRCALPHA)
            body.fill((40, 20, 90, 210) if sel else (14, 10, 40, 170))
            surf.blit(body, rect)
            color = config.CYAN if sel else (70, 70, 130)
            pygame.draw.rect(surf, color, rect, 3 if sel else 2, border_radius=10)
            if sel:
                halo = rect.inflate(int(6 + 6 * pulse), int(6 + 6 * pulse))
                pygame.draw.rect(surf, (20, 90, 120), halo, 2, border_radius=14)
                draw_arrow(surf, "right", (rect.left + 24, rect.centery), 16, config.CYAN)
                draw_arrow(surf, "left", (rect.right - 24, rect.centery), 16, config.CYAN)
            draw_text(surf, item.label, font, config.WHITE if sel else config.DIM, rect.center, "center")


def _draw_status_dot(surf, fonts: Fonts, game, x: int, y: int) -> None:
    connected = game.input.controller_connected
    draw_text(surf, "ESP32 CONTROLLER", fonts.get(18), config.DIM, (x, y), "midtop")
    color = config.GREEN if connected else (150, 150, 180)
    label = game.input.controller_label
    cy = y + 38
    font = fonts.get(22)
    width = font.size(label)[0] + 26
    dot_x = x - width // 2 + 8
    if connected:
        pygame.draw.circle(surf, color, (dot_x, cy), 7)
    else:
        pygame.draw.circle(surf, color, (dot_x, cy), 7, 2)
    draw_text(surf, label, font, color, (dot_x + 20, cy), "midleft")
    if not connected:
        draw_text(surf, "Keyboard controls enabled.", fonts.get(18), config.DIM, (x, cy + 24), "midtop")


def draw_title(surf: pygame.Surface, fonts: Fonts, t: float, y: int = 70) -> None:
    draw_text(surf, config.TITLE, fonts.get(104), config.WHITE, (W // 2, y), "midtop", glow=config.MAGENTA)
    draw_text(surf, "RUN.  DODGE.  SURVIVE.", fonts.get(26), config.CYAN, (W // 2, y + 118), "midtop")


def draw_main_menu(surf: pygame.Surface, fonts: Fonts, game) -> None:
    draw_title(surf, fonts, game.time)
    game.main_menu.draw(surf, fonts, W // 2, 292, game.time, height=48, gap=12)
    draw_text(surf, f"HIGH SCORE: {game.session.scoring.high_score:06d}", fonts.get(26), config.YELLOW,
              (W // 2, 540), "midtop")
    _draw_status_dot(surf, fonts, game, W // 2, 582)
    draw_text(surf, "JUMP / SLIDE: move     RIGHT / ENTER: select     F11: fullscreen", fonts.get(16),
              config.DIM, (W // 2, H - 14), "midbottom")


def draw_boot(surf: pygame.Surface, fonts: Fonts, game) -> None:
    draw_title(surf, fonts, game.time, y=90)
    draw_text(surf, "Initializing...", fonts.get(28), config.DIM, (W // 2, 270), "midtop")
    rows = [("Graphics", True), ("Audio", game.audio.available), ("Input", True),
            ("ESP32", True if game.input.controller_connected else None)]
    y = 330
    for i, (name, ok) in enumerate(rows):
        if game.state_time < 0.3 + i * 0.35:
            break
        draw_text(surf, name, fonts.get(26), config.WHITE, (W // 2 - 160, y), "topleft")
        label, color = ("OK", config.GREEN) if ok else (("optional", config.DIM) if ok is None else ("disabled", config.ORANGE))
        if ok:
            pygame.draw.lines(surf, color, False, [(W // 2 + 60, y + 15), (W // 2 + 68, y + 23), (W // 2 + 84, y + 6)], 4)
        draw_text(surf, label, fonts.get(22), color, (W // 2 + 100, y + 3), "topleft")
        y += 46
    if not game.input.controller_connected:
        draw_text(surf, "ESP32 CONTROLLER NOT CONNECTED  -  Keyboard controls enabled.", fonts.get(20),
                  config.DIM, (W // 2, 540), "midtop")
    if int(game.time * 2) % 2 == 0:
        draw_text(surf, "Press START", fonts.get(30), config.CYAN, (W // 2, 600), "midtop")


def draw_controls(surf: pygame.Surface, fonts: Fonts, game) -> None:
    draw_text(surf, "CONTROLS", fonts.get(60), config.WHITE, (W // 2, 50), "midtop", glow=config.CYAN)
    rows = [("left", "LEFT", "A / Left arrow", "Left-group LEFT button"),
            ("right", "RIGHT", "D / Right arrow", "Right-group RIGHT button"),
            ("up", "JUMP", "W / Up arrow / Space", "Either UP button"),
            ("down", "SLIDE", "S / Down arrow", "Either DOWN button")]
    draw_text(surf, "ACTION", fonts.get(18), config.DIM, (330, 150), "topleft")
    draw_text(surf, "KEYBOARD", fonts.get(18), config.DIM, (560, 150), "topleft")
    draw_text(surf, "ESP32 BUTTON", fonts.get(18), config.DIM, (880, 150), "topleft")
    y = 185
    for arrow, name, keys, button in rows:
        pygame.draw.rect(surf, (20, 14, 56), (200, y, 880, 62), border_radius=10)
        pygame.draw.rect(surf, (60, 60, 140), (200, y, 880, 62), 2, border_radius=10)
        draw_arrow(surf, arrow, (240, y + 31), 26, config.CYAN)
        draw_text(surf, name, fonts.get(28), config.WHITE, (290, y + 31), "midleft")
        draw_text(surf, keys, fonts.get(22), config.YELLOW, (560, y + 31), "midleft")
        draw_text(surf, button, fonts.get(20), config.GREEN, (880, y + 31), "midleft")
        y += 76
    notes = ["Physical ESP32 controller supported - keyboard fallback always available.",
             "Menus: JUMP / SLIDE move the cursor, RIGHT (or ENTER) selects, LEFT (or ESC) goes back.",
             "ESC / P pauses during a run.  F11 toggles fullscreen.  F3 toggles the debug overlay."]
    for i, n in enumerate(notes):
        draw_text(surf, n, fonts.get(20), config.DIM, (W // 2, 520 + i * 30), "midtop")
    draw_text(surf, "LEFT / ESC: back", fonts.get(18), config.CYAN, (W // 2, H - 24), "midbottom")


def draw_settings(surf: pygame.Surface, fonts: Fonts, game) -> None:
    draw_text(surf, "SETTINGS", fonts.get(60), config.WHITE, (W // 2, 70), "midtop", glow=config.CYAN)
    game.settings_menu.draw(surf, fonts, W // 2, 220, game.time, width=520)
