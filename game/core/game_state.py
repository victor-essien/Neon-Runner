"""High-level game states."""
from enum import Enum, auto


class GameState(Enum):
    BOOT = auto()
    MAIN_MENU = auto()
    CONTROLS = auto()
    SETTINGS = auto()
    COUNTDOWN = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
