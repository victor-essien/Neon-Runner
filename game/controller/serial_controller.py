"""Background-thread serial reader for the ESP32 controller.

The pygame loop never blocks on serial: a worker thread owns the port, pushes
decoded Actions into a queue and the game drains it with ``poll()``.
"""
from __future__ import annotations

import logging
import queue
import threading
from typing import Optional

from game import config
from game.controller.actions import (
    OUTGOING_MESSAGES, SERIAL_ACTIONS, STATUS_MESSAGES, Action, parse_serial_line,
)

try:  # pyserial is optional at import time so the game still launches without it
    import serial
    from serial.tools import list_ports
except ImportError:  # pragma: no cover
    serial = None  # type: ignore[assignment]
    list_ports = None  # type: ignore[assignment]

log = logging.getLogger(__name__)

_KEYWORDS = ("cp210", "ch340", "ch910", "ch9102", "usb-serial", "usb serial", "uart",
             "silicon labs", "esp32", "ftdi", "usbserial", "wchusb", "slab")
_KNOWN_VIDS = {0x10C4, 0x1A86, 0x303A, 0x0403, 0x067B}


def list_candidate_ports() -> list[str]:
    """Return serial ports that look like an ESP32 dev board, best match first."""
    if list_ports is None:
        return []
    scored: list[tuple[int, str]] = []
    for p in list_ports.comports():
        text = " ".join(filter(None, [p.description, p.manufacturer, p.hwid, p.product])).lower()
        device = p.device
        if "bluetooth" in text or "bthenum" in text or device.startswith("/dev/ttyS"):
            continue
        score = 0
        if p.vid in _KNOWN_VIDS:
            score += 2
        if any(k in text for k in _KEYWORDS):
            score += 1
        if any(k in device.lower() for k in ("usb", "acm", "slab")):
            score += 1
        if score:
            scored.append((score, device))
    scored.sort(key=lambda t: -t[0])
    return [d for _, d in scored]


class SerialController:
    """Reads commands from the ESP32 and sends LED state messages back."""

    def __init__(self, port: Optional[str] = None, baudrate: Optional[int] = None,
                 enabled: bool = True) -> None:
        self.enabled = enabled
        self._port_override = port if port is not None else config.SERIAL_PORT
        self._baudrate = baudrate or config.SERIAL_BAUDRATE
        self._in: "queue.Queue[Action]" = queue.Queue(maxsize=64)
        self._out: "queue.Queue[str]" = queue.Queue(maxsize=16)
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._connected = False
        self._ready_flag = False
        self.port_name: Optional[str] = None
        self.last_error = ""
        self.last_command: Optional[Action] = None
        self.last_status: Optional[str] = None
        self.unknown_lines = 0
        self.stats: dict[Action, int] = {a: 0 for a in SERIAL_ACTIONS.values()}

    # -- public API -----------------------------------------------------------
    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def status_text(self) -> str:
        if not self.enabled:
            return "DISABLED (keyboard mode)"
        if serial is None:
            return "pyserial not installed"
        if self._connected:
            return f"CONNECTED ({self.port_name})"
        return "SEARCHING..."

    def start(self) -> None:
        if not self.enabled or serial is None or self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run, name="serial-controller", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=1.0)
            self._thread = None

    def poll(self) -> list[Action]:
        """Drain decoded actions (non-blocking)."""
        actions: list[Action] = []
        while True:
            try:
                actions.append(self._in.get_nowait())
            except queue.Empty:
                return actions

    def send(self, message: str) -> None:
        """Queue a known LED-state message for the ESP32."""
        if message in OUTGOING_MESSAGES and self._connected:
            try:
                self._out.put_nowait(message)
            except queue.Full:
                pass

    def consume_ready(self) -> bool:
        """True once after the firmware announces READY (e.g. after a reset)."""
        flag, self._ready_flag = self._ready_flag, False
        return flag

    # -- worker thread --------------------------------------------------------
    def _run(self) -> None:
        ser = None
        buffer = b""
        while not self._stop.is_set():
            if ser is None:
                ser = self._try_connect()
                if ser is None:
                    self._stop.wait(config.SERIAL_RECONNECT_S)
                    continue
                buffer = b""
            try:
                self._flush_outgoing(ser)
                data = ser.read(ser.in_waiting or 1)
                if data:
                    buffer += data
                    while b"\n" in buffer:
                        line, buffer = buffer.split(b"\n", 1)
                        self._handle_line(line.decode("ascii", errors="ignore"))
                    if len(buffer) > 128:       # garbage without newline
                        buffer = b""
            except (serial.SerialException, OSError) as exc:
                log.warning("Serial connection lost: %s", exc)
                self.last_error = str(exc)
                self._connected = False
                try:
                    ser.close()
                except Exception:  # noqa: BLE001
                    pass
                ser = None
        if ser is not None:
            try:
                ser.close()
            except Exception:  # noqa: BLE001
                pass
        self._connected = False

    def _try_connect(self):
        ports = [self._port_override] if self._port_override else list_candidate_ports()
        for port in ports:
            try:
                ser = serial.Serial()
                ser.port = port
                ser.baudrate = self._baudrate
                ser.timeout = 0.05
                ser.write_timeout = 0.2
                ser.dtr = False          # avoid resetting the ESP32 on open
                ser.rts = False
                ser.open()
                self.port_name = port
                self._connected = True
                self.last_error = ""
                log.info("ESP32 controller connected on %s", port)
                return ser
            except (serial.SerialException, OSError, ValueError) as exc:
                self.last_error = f"{port}: {exc}"
        return None

    def _flush_outgoing(self, ser) -> None:
        while True:
            try:
                msg = self._out.get_nowait()
            except queue.Empty:
                return
            ser.write((msg + "\n").encode("ascii"))

    def _handle_line(self, text: str) -> None:
        text = text.strip()
        if not text:
            return
        action = parse_serial_line(text)
        if action is not None:
            self.stats[action] += 1
            self.last_command = action
            try:
                self._in.put_nowait(action)
            except queue.Full:
                pass
        elif text.upper() in STATUS_MESSAGES:
            self.last_status = text.upper()
            if self.last_status == "READY":
                self._ready_flag = True
        else:
            self.unknown_lines += 1     # boot-ROM noise, debug comments, junk
