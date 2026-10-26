"""Game: window, state machine and main loop. Gameplay itself lives in GameSession."""
from __future__ import annotations

import logging
import os
from typing import Optional

import pygame

from game import config
from game.audio.audio_manager import AudioManager
from game.controller.actions import Action
from game.controller.input_manager import InputManager
from game.controller.keyboard_controller import KeyboardController
from game.controller.serial_controller import SerialController
from game.core.clock import FrameClock
from game.core.events import EventBus, GameEvent
from game.core.game_state import GameState
from game.core.session import GameSession
from game.player.animation import PlayerAnimator
from game.rendering.effects import Effects
from game.rendering.projection import project
from game.rendering.renderer import Renderer
from game.systems.scoring import HighScoreStore
from game.ui.menu import Menu, MenuItem
from game.ui.widgets import Fonts

log = logging.getLogger(__name__)
IDLE_SPEED = 10.0


class Game:
    def __init__(self, args=None) -> None:
        get = lambda name, default=None: getattr(args, name, default) if args is not None else default
        self.debug = bool(get("debug", False)) or config.DEBUG
        self.fullscreen = bool(get("fullscreen", False))

        pygame.display.init()
        pygame.font.init()
        self.screen = self._create_window()
        pygame.display.set_caption(config.TITLE)

        self.bus = EventBus()
        self.fonts = Fonts()
        self.clock = FrameClock()
        self.fx = Effects()
        self.audio = AudioManager(self.bus, enabled=not get("no_audio", False))

        keyboard_only = bool(get("keyboard", False)) or bool(get("mock_controller", False))
        serial_ctrl = SerialController(port=get("port"), enabled=not keyboard_only)
        serial_ctrl.start()
        self.input = InputManager(serial_ctrl, KeyboardController(), simulated=bool(get("mock_controller", False)))

        self.session = GameSession(self.bus, HighScoreStore())
        self.animator = PlayerAnimator()
        self.renderer = Renderer(self.screen, self.fonts)

        self.main_menu = Menu([MenuItem("start", "START GAME"), MenuItem("controls", "CONTROLS"),
                               MenuItem("settings", "SETTINGS"), MenuItem("quit", "QUIT")])
        self.settings_menu = Menu([MenuItem("fullscreen", ""), MenuItem("sfx", ""), MenuItem("music", ""),
                                   MenuItem("debug", ""), MenuItem("back", "BACK")])
        self.pause_menu = Menu([MenuItem("resume", "RESUME"), MenuItem("restart", "RESTART"),
                                MenuItem("menu", "MAIN MENU")])
        self.game_over_menu = Menu([MenuItem("restart", "RESTART"), MenuItem("menu", "MAIN MENU")])

        self.running = True
        self.time = 0.0
        self.state = GameState.BOOT
        self.state_time = 0.0
        self.countdown_label = ""
        self._countdown_index = -1
        self.new_record = False
        self.toast_text = ""
        self.toast_timer = 0.0
        self._last_connected = self.input.controller_connected
        self._handlers = {
            GameState.BOOT: self._update_boot, GameState.MAIN_MENU: self._update_main_menu,
            GameState.CONTROLS: self._update_controls, GameState.SETTINGS: self._update_settings,
            GameState.COUNTDOWN: self._update_countdown, GameState.PLAYING: self._update_playing,
            GameState.PAUSED: self._update_paused, GameState.GAME_OVER: self._update_game_over,
        }
        self._wire_effects()
        self._refresh_settings_labels()
        self.audio.play_music("menu_music")
        self.fx.fade_in(0.6)

    # -- window -------------------------------------------------------------------
    def _create_window(self) -> pygame.Surface:
        flags = pygame.SCALED | pygame.RESIZABLE
        if self.fullscreen:
            flags |= pygame.FULLSCREEN
        try:
            return pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), flags)
        except pygame.error:
            log.warning("SCALED window unavailable, falling back to a plain window")
            return pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))

    def toggle_fullscreen(self) -> None:
        try:
            pygame.display.toggle_fullscreen()
            self.fullscreen = not self.fullscreen
        except pygame.error:
            self.show_toast("Fullscreen is not supported here")
        self._refresh_settings_labels()

    # -- helpers ------------------------------------------------------------------
    @property
    def scroll_speed(self) -> float:
        if self.state is GameState.PLAYING:
            return self.session.speed
        if self.state is GameState.COUNTDOWN:
            return 8.0
        if self.state in (GameState.PAUSED, GameState.GAME_OVER):
            return 0.0
        return IDLE_SPEED

    def show_toast(self, text: str, seconds: float = 3.0) -> None:
        self.toast_text, self.toast_timer = text, seconds

    def _player_screen(self, height: float = 0.0) -> tuple[float, float]:
        p = self.session.player
        x, y, _ = project(p.lane_pos - 1, 0, p.y + height)
        return x, y

    def _set_state(self, state: GameState) -> None:
        self.state = state
        self.state_time = 0.0
        self.fx.fade_in(0.3)
        self._sync_led()

    def _sync_led(self) -> None:
        msg = {GameState.COUNTDOWN: "GAME_START", GameState.PLAYING: "GAME_START",
               GameState.PAUSED: "PAUSED", GameState.GAME_OVER: "GAME_OVER"}.get(self.state, "READY")
        self.input.send_status(msg)

    def _refresh_settings_labels(self) -> None:
        on = lambda v: "ON" if v else "OFF"
        labels = {"fullscreen": f"FULLSCREEN: {on(self.fullscreen)}", "sfx": f"SOUND FX: {on(self.audio.sfx_enabled)}",
                  "music": f"MUSIC: {on(self.audio.music_enabled)}", "debug": f"DEBUG OVERLAY: {on(self.debug)}",
                  "back": "BACK"}
        for item in self.settings_menu.items:
            item.label = labels[item.key]

    def _wire_effects(self) -> None:
        sub, fx = self.bus.subscribe, self.fx
        sub(GameEvent.JUMP, lambda **_: fx.dust(*self._player_screen(), count=6))
        sub(GameEvent.LAND, lambda **_: (fx.dust(*self._player_screen(), count=10), self.animator.on_land()))
        sub(GameEvent.SLIDE, lambda **_: fx.sparks(*self._player_screen(), config.CYAN, 12))
        sub(GameEvent.RUN_START, lambda **_: fx.burst(*self._player_screen(0.9), config.CYAN, 30))

        def on_coin(coin, **_) -> None:
            x, y, _s = project(coin.lane - 1, coin.z, coin.y)
            fx.burst(x, y, config.YELLOW, 14, speed=200, life=0.5, size=3)
            fx.text(f"+{config.COIN_SCORE}", x, y - 20, config.YELLOW)

        def on_crash(**_) -> None:
            fx.shake(1.0)
            fx.flash(210)
            fx.burst(*self._player_screen(0.9), config.RED, 40, speed=380, life=0.9, size=5)
            fx.burst(*self._player_screen(0.9), config.MAGENTA, 20, speed=260)

        sub(GameEvent.COIN, on_coin)
        sub(GameEvent.CRASH, on_crash)

    # -- main loop ----------------------------------------------------------------
    def run(self) -> None:
        try:
            while self.running:
                dt = self.clock.tick()
                for event in pygame.event.get():
                    self._handle_event(event)
                self.input.update()
                self.update(dt)
                self.renderer.update(dt, self)
                self.renderer.draw(self)
                pygame.display.flip()
        finally:
            self.shutdown()

    def _handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            self.toggle_fullscreen()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_F3:
            self.debug = not self.debug
            self._refresh_settings_labels()
        elif event.type == pygame.WINDOWFOCUSLOST and self.state is GameState.PLAYING:
            self._pause()
        else:
            self.input.handle_event(event)

    def shutdown(self) -> None:
        self.input.send_status("READY")
        self.input.shutdown()
        pygame.quit()

    # -- update ---------------------------------------------------------------------
    def update(self, dt: float) -> None:
        self.time += dt
        self.state_time += dt
        self.toast_timer = max(0.0, self.toast_timer - dt)
        self._sync_controller()
        self.fx.update(dt)
        self._handlers[self.state](dt, self.input.drain())

    def _sync_controller(self) -> None:
        connected = self.input.controller_connected
        if connected != self._last_connected:
            if connected:
                self.show_toast("ESP32 controller connected")
                self._sync_led()
            else:
                self.show_toast("ESP32 controller disconnected. Keyboard controls enabled.")
                if self.state is GameState.PLAYING:
                    self._pause()
            self._last_connected = connected
        if self.input.consume_controller_ready():
            self._sync_led()

    def _menu_feedback(self, result: Optional[tuple[str, str]]) -> Optional[tuple[str, str]]:
        if result:
            kind = {"move": GameEvent.MENU_MOVE, "select": GameEvent.MENU_SELECT, "back": GameEvent.MENU_BACK}[result[0]]
            self.bus.publish(kind)
        return result

    # -- state handlers -------------------------------------------------------------
    def _update_boot(self, dt, actions) -> None:
        if self.state_time > config.BOOT_SCREEN_S or (actions and self.state_time > 0.8):
            self._set_state(GameState.MAIN_MENU)

    def _update_main_menu(self, dt, actions) -> None:
        for action in actions:
            res = self._menu_feedback(self.main_menu.handle(action))
            if not res or res[0] != "select":
                continue
            if res[1] == "start":
                self._start_run()
            elif res[1] == "controls":
                self._set_state(GameState.CONTROLS)
            elif res[1] == "settings":
                self._set_state(GameState.SETTINGS)
            elif res[1] == "quit":
                self.running = False
            return

    def _update_controls(self, dt, actions) -> None:
        if any(a in (Action.LEFT, Action.PAUSE, Action.START, Action.RIGHT) for a in actions):
            self.bus.publish(GameEvent.MENU_BACK)
            self._set_state(GameState.MAIN_MENU)

    def _update_settings(self, dt, actions) -> None:
        for action in actions:
            res = self._menu_feedback(self.settings_menu.handle(action))
            if not res:
                continue
            if res[0] == "back" or (res[0] == "select" and res[1] == "back"):
                self._set_state(GameState.MAIN_MENU)
                return
            if res[0] == "select":
                if res[1] == "fullscreen":
                    self.toggle_fullscreen()
                elif res[1] == "sfx":
                    self.audio.sfx_enabled = not self.audio.sfx_enabled
                elif res[1] == "music":
                    self.audio.set_music_enabled(not self.audio.music_enabled)
                elif res[1] == "debug":
                    self.debug = not self.debug
                self._refresh_settings_labels()

    def _start_run(self) -> None:
        self.session.reset()
        self.animator.reset(self.session.player)
        self.new_record = False
        self._countdown_index = -1
        self.countdown_label = ""
        self._set_state(GameState.COUNTDOWN)
        self.audio.play_music("game_music")

    def _update_countdown(self, dt, actions) -> None:
        index = int(self.state_time / config.COUNTDOWN_STEP_S)
        labels = ("3", "2", "1", "RUN!")
        if index != self._countdown_index and index < len(labels):
            self._countdown_index = index
            self.countdown_label = labels[index]
            self.bus.publish(GameEvent.COUNTDOWN_TICK, go=index == len(labels) - 1)
        self.animator.update(dt, self.session.player, 8.0)
        if index >= len(labels):
            self._set_state(GameState.PLAYING)
            self.bus.publish(GameEvent.RUN_START)

    def _update_playing(self, dt, actions) -> None:
        for action in actions:
            if action is Action.PAUSE:
                self._pause()
                return
            self.session.apply_action(action)
        self.session.update(dt)
        self.animator.update(dt, self.session.player, self.session.speed)
        px, py = self._player_screen()
        self.fx.trail(dt, px, py, config.CYAN)
        if self.session.crashed:
            self.new_record = self.session.scoring.finalize()
            self._set_state(GameState.GAME_OVER)
            self.bus.publish(GameEvent.GAME_OVER)

    def _pause(self) -> None:
        self.pause_menu.index = 0
        self._set_state(GameState.PAUSED)
        self.bus.publish(GameEvent.PAUSE)

    def _update_paused(self, dt, actions) -> None:
        for action in actions:
            res = self._menu_feedback(self.pause_menu.handle(action))
            if not res:
                continue
            if res[0] == "back" or (res[0] == "select" and res[1] == "resume"):
                self._set_state(GameState.PLAYING)
                self.bus.publish(GameEvent.RESUME)
            elif res[0] == "select" and res[1] == "restart":
                self._start_run()
            elif res[0] == "select" and res[1] == "menu":
                self._to_main_menu()
            return

    def _update_game_over(self, dt, actions) -> None:
        if self.state_time < config.GAME_OVER_INPUT_DELAY_S:
            return
        for action in actions:
            res = self._menu_feedback(self.game_over_menu.handle(action))
            if res and res[0] == "select":
                self._start_run() if res[1] == "restart" else self._to_main_menu()
                return

    def _to_main_menu(self) -> None:
        self.session.reset()
        self.main_menu.index = 0
        self._set_state(GameState.MAIN_MENU)
        self.audio.play_music("menu_music")
