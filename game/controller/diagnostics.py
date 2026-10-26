"""``--test-controller`` screen: live view of what the ESP32 is sending."""
from __future__ import annotations

import pygame

from game import config
from game.controller.actions import Action
from game.controller.serial_controller import SerialController
from game.ui.widgets import Fonts, draw_text


def run_controller_test(port=None) -> int:
    pygame.display.init()
    pygame.font.init()
    screen = pygame.display.set_mode((900, 560))
    pygame.display.set_caption("NEON RUNNER - ESP32 controller test")
    fonts = Fonts()
    ctrl = SerialController(port=port)
    ctrl.start()
    clock = pygame.time.Clock()
    flash = 0.0
    last_seen = None
    try:
        running = True
        while running:
            dt = clock.tick(60) / 1000.0
            for e in pygame.event.get():
                if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                    running = False
            ctrl.poll()                                   # keep the queue drained
            if ctrl.last_command is not None and (ctrl.last_command, sum(ctrl.stats.values())) != last_seen:
                last_seen = (ctrl.last_command, sum(ctrl.stats.values()))
                flash = 0.4
            flash = max(0.0, flash - dt)

            screen.fill((10, 6, 32))
            draw_text(screen, "ESP32 CONTROLLER TEST", fonts.get(46), config.WHITE, (450, 30), "midtop", glow=config.CYAN)
            ok = ctrl.connected
            draw_text(screen, f"CONNECTED: {'YES' if ok else 'NO'}", fonts.get(30), config.GREEN if ok else config.RED, (60, 110))
            draw_text(screen, ctrl.status_text, fonts.get(20), config.DIM, (60, 150))
            if ctrl.last_error and not ok:
                draw_text(screen, ctrl.last_error[:80], fonts.get(16), config.ORANGE, (60, 176))
            draw_text(screen, "Last command:", fonts.get(22), config.DIM, (60, 220))
            cmd = ctrl.last_command.value if ctrl.last_command else "-"
            draw_text(screen, cmd, fonts.get(72), config.YELLOW if flash > 0 else config.WHITE, (60, 250))
            draw_text(screen, "Commands received:", fonts.get(22), config.DIM, (480, 220))
            for i, action in enumerate((Action.LEFT, Action.RIGHT, Action.JUMP, Action.SLIDE)):
                draw_text(screen, f"{action.value}:", fonts.get(30), config.CYAN, (480, 260 + i * 44))
                draw_text(screen, str(ctrl.stats[action]), fonts.get(30), config.WHITE, (700, 260 + i * 44))
            draw_text(screen, f"Status: {ctrl.last_status or '-'}    Ignored lines: {ctrl.unknown_lines}",
                      fonts.get(18), config.DIM, (60, 470))
            draw_text(screen, "Press each physical button. ESC to exit. Close the Arduino Serial Monitor first.",
                      fonts.get(18), config.DIM, (450, 520), "midtop")
            pygame.display.flip()
    finally:
        ctrl.stop()
        pygame.quit()
    return 0
