"""Tiny publish/subscribe bus that decouples gameplay from audio and effects."""
from __future__ import annotations

import logging
from collections import defaultdict
from enum import Enum, auto
from typing import Any, Callable

log = logging.getLogger(__name__)


class GameEvent(Enum):
    MENU_MOVE = auto()
    MENU_SELECT = auto()
    MENU_BACK = auto()
    COUNTDOWN_TICK = auto()
    RUN_START = auto()
    LANE_CHANGE = auto()
    JUMP = auto()
    SLIDE = auto()
    LAND = auto()
    COIN = auto()
    CRASH = auto()
    GAME_OVER = auto()
    PAUSE = auto()
    RESUME = auto()


class EventBus:
    """Synchronous event bus. A failing handler never breaks the game."""

    def __init__(self) -> None:
        self._subs: dict[GameEvent, list[Callable[..., None]]] = defaultdict(list)

    def subscribe(self, event: GameEvent, handler: Callable[..., None]) -> None:
        self._subs[event].append(handler)

    def publish(self, event: GameEvent, **data: Any) -> None:
        for handler in list(self._subs[event]):
            try:
                handler(**data)
            except Exception:  # noqa: BLE001 - isolate subscribers
                log.exception("Event handler failed for %s", event)
