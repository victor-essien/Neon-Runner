"""Single entry point for all player input.

The game only ever sees ``Action`` values, never raw keys or serial lines.
"""
from __future__ import annotations

from collections import deque
from typing import Optional

from game.controller.actions import Action


class InputManager:
    def __init__(self, serial_controller=None, keyboard=None, simulated: bool = False) -> None:
        self.serial = serial_controller
        self.keyboard = keyboard
        self.simulated = simulated
        self._queue: deque[Action] = deque(maxlen=16)

    # -- feeding --------------------------------------------------------------
    def handle_event(self, event) -> None:
        if self.keyboard is not None:
            action = self.keyboard.handle_event(event)
            if action is not None:
                self._queue.append(action)

    def push(self, action: Action) -> None:
        self._queue.append(action)

    def update(self) -> None:
        if self.serial is not None:
            for action in self.serial.poll():
                self._queue.append(action)

    # -- consuming ------------------------------------------------------------
    def consume_action(self) -> Optional[Action]:
        return self._queue.popleft() if self._queue else None

    def drain(self) -> list[Action]:
        actions = list(self._queue)
        self._queue.clear()
        return actions

    # -- status ---------------------------------------------------------------
    @property
    def controller_connected(self) -> bool:
        if self.simulated:
            return True
        return bool(self.serial and self.serial.connected)

    @property
    def controller_label(self) -> str:
        if self.simulated:
            return "SIMULATED (keyboard)"
        if self.serial is None or not self.serial.enabled:
            return "KEYBOARD ONLY"
        return "CONNECTED" if self.serial.connected else "NOT CONNECTED"

    def send_status(self, message: str) -> None:
        if self.serial is not None:
            self.serial.send(message)

    def consume_controller_ready(self) -> bool:
        return bool(self.serial and self.serial.consume_ready())

    def shutdown(self) -> None:
        if self.serial is not None:
            self.serial.stop()
