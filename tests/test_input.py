import pygame

from game.controller.actions import Action, parse_serial_line
from game.controller.input_manager import InputManager
from game.controller.keyboard_controller import KeyboardController
from game.controller.serial_controller import SerialController


def test_serial_commands_map_to_actions():
    assert parse_serial_line("LEFT") is Action.LEFT
    assert parse_serial_line("RIGHT") is Action.RIGHT
    assert parse_serial_line("JUMP\r") is Action.JUMP
    assert parse_serial_line(" SLIDE \n") is Action.SLIDE


def test_unknown_and_malicious_lines_are_ignored():
    for junk in ("", "READY", "__import__('os')", "left; rm -rf /", "ets Jun  8 2016", "\x00\xff"):
        assert parse_serial_line(junk) is None


def test_serial_line_handler_counts_and_filters():
    c = SerialController(enabled=False)
    for line in ("LEFT", "JUMP", "JUMP", "garbage", "READY", ""):
        c._handle_line(line)
    assert c.stats[Action.LEFT] == 1 and c.stats[Action.JUMP] == 2
    assert c.unknown_lines == 1
    assert c.poll() == [Action.LEFT, Action.JUMP, Action.JUMP]
    assert c.consume_ready() is True and c.consume_ready() is False


def test_keyboard_and_serial_share_input_manager():
    serial_ctrl = SerialController(enabled=False)
    serial_ctrl._handle_line("SLIDE")
    im = InputManager(serial_ctrl, KeyboardController())
    im.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_a))
    im.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    im.update()
    assert im.drain() == [Action.LEFT, Action.PAUSE, Action.SLIDE]
    assert im.consume_action() is None


def test_keyboard_mapping():
    kb = KeyboardController()
    cases = {pygame.K_a: Action.LEFT, pygame.K_LEFT: Action.LEFT, pygame.K_d: Action.RIGHT,
             pygame.K_RIGHT: Action.RIGHT, pygame.K_w: Action.JUMP, pygame.K_UP: Action.JUMP,
             pygame.K_s: Action.SLIDE, pygame.K_DOWN: Action.SLIDE, pygame.K_ESCAPE: Action.PAUSE}
    for key, expected in cases.items():
        assert kb.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key)) is expected


def test_serial_controller_never_crashes_without_hardware():
    c = SerialController(port="/dev/definitely-not-a-port")
    c.start()
    c.stop()
    assert not c.connected
