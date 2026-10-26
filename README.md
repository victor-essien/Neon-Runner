# NEON RUNNER — ESP32 Controller + Python/Pygame Endless Runner

A three-lane neon-city endless runner played with a **custom six-button ESP32 controller**
(keyboard fallback included). Hardware → embedded C++ → USB serial → Python → Pygame.
All art and audio are original and procedurally generated, so the game runs right after install.

## 1. Features
- Three-lane perspective world with smooth lane changes, jump physics, slide, fast-fall and jump buffering
- Ground barriers (jump), overhead gates (slide), trains (change lane)
- Coins, coin lines/arcs, score, distance, persistent high score (`highscore.json`)
- Procedural spawner that **never** produces an unpassable row, plus a data-driven difficulty curve
- Menus, controls screen, settings, countdown, pause, game over, debug overlay
- Particles, screen shake, speed lines, glow, fades; synthesized music and SFX (overridable with files)
- Serial reader on a background thread: auto-detect, auto-reconnect, never crashes the game
- Controller diagnostics screen, mock-controller mode, 29 unit tests

## 2. Architecture
```
 6 buttons ─▶ ESP32 firmware (C++) ──USB serial 115200──▶ SerialController (thread)
                      ▲  LED state msgs                          │
                      └──────────────────────────────────────────┤
 Keyboard ───────────────────────────────▶ InputManager ◀────────┘
                                               │  Action enum only
                                               ▼
                 Game (state machine) ─▶ GameSession (pure logic: player, world,
                      │                   collision, scoring, difficulty)
                      ├─ EventBus ─▶ AudioManager, Effects
                      └─ Renderer (projection, background, entities, UI screens)
```
`GameSession` has no pygame dependency, which is why gameplay is fully unit-tested.

## 3. Hardware
ESP32 DevKit, 6 push buttons, 1 green LED, 1 resistor (220–330 Ω), breadboard, jumper wires, USB cable (data-capable).

### GPIO map (edit only `esp32_controller/config.h`)
| Button | GPIO | Command |
|---|---|---|
| Left group — LEFT | 13 | `LEFT` |
| Left group — UP | 14 | `JUMP` |
| Left group — DOWN | 27 | `SLIDE` |
| Right group — RIGHT | 26 | `RIGHT` |
| Right group — UP | 25 | `JUMP` |
| Right group — DOWN | 33 | `SLIDE` |
| Status LED (via resistor) | 18 | — |

### Wiring
```
ESP32 GPIO 13 ──[LEFT  btn]── GND        ESP32 GPIO 26 ──[RIGHT btn]── GND
ESP32 GPIO 14 ──[UP    btn]── GND        ESP32 GPIO 25 ──[UP    btn]── GND
ESP32 GPIO 27 ──[DOWN  btn]── GND        ESP32 GPIO 33 ──[DOWN  btn]── GND
ESP32 GPIO 18 ──[220Ω]──▶|(green LED, long leg to resistor)── GND
```
Buttons use `INPUT_PULLUP`: **HIGH = not pressed, LOW = pressed**. No external resistors needed.
Each press sends exactly one line (debounced 25 ms, press-edge only; holding does not repeat).

### Serial protocol (115200 baud, `\n`-terminated lines)
| Direction | Lines |
|---|---|
| ESP32 → PC | `LEFT` `RIGHT` `JUMP` `SLIDE` (+ `READY` at boot) |
| PC → ESP32 | `READY` `GAME_START` `PAUSED` `GAME_OVER` |

LED: `READY`/`GAME_START` solid, `PAUSED` blinking, `GAME_OVER` off. Anything unknown is ignored; nothing is ever evaluated.

## 4. Arduino IDE setup (firmware)
1. Install Arduino IDE 2.x.
2. *File ▸ Preferences ▸ Additional boards manager URLs*: add
   `https://espressif.github.io/arduino-esp32/package_esp32_index.json`
3. *Tools ▸ Board ▸ Boards Manager*: install **esp32 by Espressif Systems**.
4. Plug in the ESP32 over USB. *Tools ▸ Board ▸* **ESP32 Dev Module** (or your exact board).
5. *Tools ▸ Port ▸* choose the ESP32's port (COMx / `/dev/ttyUSB0` / `/dev/cu.usbserial-*`).
6. Open `esp32_controller/esp32_controller.ino` (all `.h/.cpp` files must stay in that folder).
7. **Verify** (compile), then **Upload** (hold the BOOT button if upload stalls on "Connecting...").
8. *Tools ▸ Serial Monitor* at **115200**: press buttons, you should see `LEFT`, `JUMP`, `SLIDE`, `RIGHT`...
9. **Close the Serial Monitor** before running the game.

```
Arduino IDE ─ uploads firmware ─▶ ESP32          Python ─ runs desktop game ─ talks to ─▶ ESP32
```

## 5. Python setup (Python 3.9+)
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows      (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
```

## 6. Running
```bash
python -m game.main                    # play; ESP32 auto-detected, keyboard always works
python -m game.main --keyboard         # never opens a serial port
python -m game.main --mock-controller  # simulated controller, no hardware needed
python -m game.main --test-controller  # live ESP32 diagnostics (counts per command)
python -m game.main --port COM5        # manual port override (Windows example)
python -m game.main --fullscreen --debug --no-audio
```
Run tests: `pip install -r requirements-dev.txt && python -m pytest`

### Controls
| Action | ESP32 | Keyboard |
|---|---|---|
| Left / Right | LEFT / RIGHT buttons | A, D / ← → |
| Jump | either UP button | W, ↑, Space |
| Slide (also fast-fall in the air) | either DOWN button | S, ↓ |
| Pause | *(auto-pauses if the controller disconnects or the window loses focus)* | Esc, P |
| Menus | JUMP/SLIDE move, RIGHT select, LEFT back | ↑↓, Enter, Esc |
| Fullscreen / debug overlay | — | F11 / F3 |

The ESP32 has no dedicated pause/start button by design, so menus are navigated with the same four buttons.

## 7. Serial troubleshooting
**ESP32 not detected** — try a data-capable USB cable; install the CP210x or CH340 driver for your board;
check the port appears in Arduino IDE; confirm the correct board is selected; on Linux add yourself to `dialout`
(`sudo usermod -aG dialout $USER`, then log out/in).

**Python cannot connect** — close Arduino Serial Monitor (two programs cannot share a port); confirm 115200 baud;
run `--test-controller` to see connection state and `last_error`; try `--port`; unplug/replug the board.
The game never needs the ESP32 to start: it shows "Keyboard controls enabled" and keeps retrying every 2 s.

**Buttons do nothing / wrong command** — check wiring to GND and the pin table in `config.h`.

Logs are written to `neon_runner.log`.

## 8. Project layout
```
esp32_controller/   firmware (config, Button, StatusLed, Controller, .ino)
game/core/          game loop + state machine, GameSession, EventBus, clock
game/player/        player physics, lane tween, procedural animation
game/world/         world, spawner (patterns + fairness check), lanes
game/entities/      obstacle, coin
game/systems/       collision, scoring/high score, difficulty
game/controller/    serial, keyboard, InputManager, diagnostics
game/rendering/     projection, background, shapes, effects, renderer
game/ui/            menus, HUD, pause, game over
game/audio/         synthesized audio + optional file overrides
tests/              pytest suite
```
Custom assets are optional: drop `jump.wav`, `coin.ogg`, `menu_music.ogg`, `game_music.ogg`... into `assets/sounds/`
(names listed in `audio_manager.py`) or a `.ttf` into `assets/fonts/`.

## 9. Roadmap
Power-ups (magnet, shield) · moving obstacles · sprite-sheet player · settings persistence ·
dedicated pause/start button on the controller · rumble/buzzer feedback · wireless (BLE) controller.
