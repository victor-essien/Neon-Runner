"""NEON RUNNER entry point.

    python -m game.main                    # play (ESP32 auto-detected, keyboard always works)
    python -m game.main --keyboard         # never touch serial
    python -m game.main --mock-controller  # simulated controller (keyboard drives it)
    python -m game.main --test-controller  # live ESP32 diagnostics
"""
from __future__ import annotations

import argparse
import logging
import sys

from game import config


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="game.main", description="NEON RUNNER - ESP32-controlled endless runner")
    p.add_argument("--keyboard", action="store_true", help="keyboard only; do not open any serial port")
    p.add_argument("--mock-controller", action="store_true", help="simulated controller (no hardware needed)")
    p.add_argument("--test-controller", action="store_true", help="show live ESP32 controller diagnostics")
    p.add_argument("--port", default=None, help="serial port override, e.g. COM5 or /dev/ttyUSB0")
    p.add_argument("--fullscreen", action="store_true", help="start in fullscreen")
    p.add_argument("--no-audio", action="store_true", help="disable all audio")
    p.add_argument("--debug", action="store_true", help="show the debug overlay")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    logging.basicConfig(filename=str(config.LOG_FILE), level=logging.DEBUG if args.debug else logging.INFO,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        if args.test_controller:
            from game.controller.diagnostics import run_controller_test
            return run_controller_test(args.port)
        from game.core.game import Game
        Game(args).run()
        return 0
    except KeyboardInterrupt:
        return 0
    except Exception:  # noqa: BLE001 - friendly message instead of a stack trace
        logging.getLogger(__name__).exception("Fatal error")
        if args.debug:
            raise
        print(f"NEON RUNNER hit an unexpected problem. Details were saved to {config.LOG_FILE.name}.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
