"""Audio manager: loads files from assets/sounds if present, otherwise synthesizes
simple retro sounds at start-up. Never raises: missing audio just means silence."""
from __future__ import annotations

import logging
import math
import random
from array import array
from typing import Optional

import pygame

from game import config
from game.core.events import EventBus, GameEvent

log = logging.getLogger(__name__)
SOUND_DIR = config.ASSETS_DIR / "sounds"


class AudioManager:
    def __init__(self, bus: EventBus, enabled: bool = True) -> None:
        self.available = False
        self.sfx_enabled = True
        self.music_enabled = True
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._music_channel: Optional[pygame.mixer.Channel] = None
        self._current_music: Optional[str] = None
        if enabled:
            self._init_mixer()
        if self.available:
            self._load_all()
            self._wire(bus)

    # -- setup ------------------------------------------------------------------
    def _init_mixer(self) -> None:
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self.rate, _, self.channels = pygame.mixer.get_init()
            pygame.mixer.set_num_channels(12)
            self._music_channel = pygame.mixer.Channel(0)
            self.available = True
        except pygame.error as exc:
            log.warning("Audio unavailable: %s", exc)

    def _load_all(self) -> None:
        try:
            synth = self._synth_catalog()
        except Exception:  # noqa: BLE001 - audio must never break startup
            log.exception("Sound synthesis failed")
            synth = {}
        for name in set(synth) | {"menu_music", "game_music"}:
            sound = self._load_file(name) or synth.get(name)
            if sound is not None:
                self._sounds[name] = sound
        for name, vol in (("menu_music", 0.35), ("game_music", 0.35)):
            if name in self._sounds:
                self._sounds[name].set_volume(vol)

    def _load_file(self, name: str) -> Optional[pygame.mixer.Sound]:
        for ext in (".ogg", ".wav", ".mp3"):
            path = SOUND_DIR / f"{name}{ext}"
            if path.exists():
                try:
                    return pygame.mixer.Sound(str(path))
                except pygame.error as exc:
                    log.warning("Could not load %s: %s", path, exc)
        return None

    def _wire(self, bus: EventBus) -> None:
        mapping = {
            GameEvent.MENU_MOVE: "menu_move", GameEvent.MENU_SELECT: "menu_select",
            GameEvent.MENU_BACK: "menu_move", GameEvent.JUMP: "jump", GameEvent.SLIDE: "slide",
            GameEvent.LAND: "land", GameEvent.LANE_CHANGE: "lane", GameEvent.COIN: "coin",
            GameEvent.CRASH: "collision", GameEvent.GAME_OVER: "game_over",
        }
        for event, name in mapping.items():
            bus.subscribe(event, lambda _n=name, **_: self.play(_n))
        bus.subscribe(GameEvent.COUNTDOWN_TICK, lambda go=False, **_: self.play("go" if go else "countdown"))

    # -- playback ---------------------------------------------------------------
    def play(self, name: str) -> None:
        if self.available and self.sfx_enabled and name in self._sounds:
            self._sounds[name].play()

    def play_music(self, name: str) -> None:
        if not self.available or name == self._current_music:
            return
        self._current_music = name
        if self._music_channel is not None:
            self._music_channel.stop()
            if self.music_enabled and name in self._sounds:
                self._music_channel.play(self._sounds[name], loops=-1, fade_ms=400)

    def set_music_enabled(self, enabled: bool) -> None:
        self.music_enabled = enabled
        name, self._current_music = self._current_music, None
        if name:
            self.play_music(name)

    # -- synthesis ----------------------------------------------------------------
    def _make(self, samples: list[float]) -> pygame.mixer.Sound:
        data = array("h", (int(max(-1.0, min(1.0, s)) * 32000) for s in samples))
        if self.channels == 2:
            stereo = array("h")
            for v in data:
                stereo.extend((v, v))
            data = stereo
        return pygame.mixer.Sound(buffer=data.tobytes())

    def _tone(self, freq: float, dur: float, vol: float = 0.5, wave: str = "square",
              slide_to: Optional[float] = None, decay: float = 4.0) -> list[float]:
        n = int(self.rate * dur)
        out, phase = [], 0.0
        for i in range(n):
            t = i / n
            f = freq + ((slide_to - freq) * t if slide_to else 0.0)
            phase += f / self.rate
            frac = phase % 1.0
            if wave == "square":
                v = 1.0 if frac < 0.5 else -1.0
            elif wave == "saw":
                v = 2 * frac - 1
            elif wave == "noise":
                v = random.uniform(-1, 1)
            else:
                v = math.sin(math.tau * frac)
            out.append(v * vol * math.exp(-decay * t) * min(1.0, i / 40))
        return out

    def _concat(self, *parts: list[float]) -> list[float]:
        merged: list[float] = []
        for p in parts:
            merged.extend(p)
        return merged

    def _music(self, bpm: int, bars: list[tuple[float, list[float]]]) -> list[float]:
        step = 60.0 / bpm / 2
        total = int(self.rate * step * 8 * len(bars))
        mix = [0.0] * total
        for bar_i, (root, arp) in enumerate(bars):
            for s in range(8):
                start = int(self.rate * step * (bar_i * 8 + s))
                bass = self._tone(root / 2, step * 0.9, 0.22, "saw", decay=3) if s % 2 == 0 else []
                lead = self._tone(arp[s % len(arp)], step * 0.85, 0.12, "square", decay=5)
                for i, v in enumerate(bass):
                    mix[start + i] += v
                for i, v in enumerate(lead):
                    if start + i < total:
                        mix[start + i] += v
        return mix

    def _synth_catalog(self) -> dict[str, pygame.mixer.Sound]:
        t = self._tone
        sounds = {
            "jump": self._make(t(300, 0.18, 0.35, "square", slide_to=700, decay=3)),
            "slide": self._make(t(900, 0.25, 0.25, "noise", decay=5)),
            "land": self._make(t(120, 0.09, 0.4, "sine", slide_to=60, decay=6)),
            "lane": self._make(t(520, 0.06, 0.18, "sine", slide_to=380, decay=6)),
            "coin": self._make(self._concat(t(988, 0.06, 0.3, "square", decay=2), t(1319, 0.14, 0.3, "square", decay=5))),
            "collision": self._make(self._concat(t(200, 0.35, 0.6, "noise", decay=4), t(90, 0.3, 0.5, "saw", slide_to=40))),
            "menu_move": self._make(t(660, 0.05, 0.2, "square", decay=6)),
            "menu_select": self._make(self._concat(t(660, 0.06, 0.25, "square"), t(990, 0.1, 0.25, "square", decay=5))),
            "countdown": self._make(t(440, 0.18, 0.35, "square", decay=4)),
            "go": self._make(t(880, 0.4, 0.4, "square", decay=3)),
            "game_over": self._make(self._concat(t(440, 0.2, 0.4, "saw"), t(330, 0.2, 0.4, "saw"), t(220, 0.5, 0.4, "saw", decay=3))),
        }
        a, f, c, g = 220.0, 174.6, 261.6, 196.0
        def arp(root): return [root * 2, root * 3, root * 4, root * 3, root * 2, root * 3, root * 4, root * 6]
        bars = [(a, arp(a)), (f, arp(f)), (c, arp(c)), (g, arp(g))]
        sounds["menu_music"] = self._make(self._music(96, bars))
        sounds["game_music"] = self._make(self._music(140, bars))
        return sounds
