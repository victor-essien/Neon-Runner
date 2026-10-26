"""Game actions and the (strict) serial protocol vocabulary."""
from __future__ import annotations

from enum import Enum
from typing import Optional


class Action(Enum):
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    JUMP = "JUMP"
    SLIDE = "SLIDE"
    PAUSE = "PAUSE"
    START = "START"


# ESP32 -> PC movement commands. Nothing else is ever turned into an Action.
SERIAL_ACTIONS: dict[str, Action] = {
    "LEFT": Action.LEFT,
    "RIGHT": Action.RIGHT,
    "JUMP": Action.JUMP,
    "SLIDE": Action.SLIDE,
}

# Informational lines the firmware may send.
STATUS_MESSAGES = frozenset({"READY", "GAME_START", "GAME_OVER", "PAUSED"})

# PC -> ESP32 LED state messages.
OUTGOING_MESSAGES = frozenset({"READY", "GAME_START", "GAME_OVER", "PAUSED"})


def parse_serial_line(line: str) -> Optional[Action]:
    """Map one received serial line to an Action, or None if unknown.

    Pure string matching: no eval/exec, unknown input is ignored.
    """
    return SERIAL_ACTIONS.get(line.strip().upper())
