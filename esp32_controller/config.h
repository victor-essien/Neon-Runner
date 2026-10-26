#pragma once
// ============================================================================
//  NEON RUNNER - ESP32 controller configuration
//  Every pin, timing and protocol constant lives here. Edit ONLY this file
//  if your wiring differs.
// ============================================================================
#include <Arduino.h>

namespace Config {

// --- Serial -----------------------------------------------------------------
constexpr unsigned long SERIAL_BAUD = 115200;

// Set true to print "# ..." comment lines (the Python side ignores them).
// Keep false during normal gameplay so the stream contains only commands.
constexpr bool DEBUG_SERIAL = false;

// --- Button pins (buttons wired GPIO -> button -> GND, INPUT_PULLUP) --------
// LEFT GROUP
constexpr uint8_t PIN_LEFT_LEFT  = 13;  // -> LEFT
constexpr uint8_t PIN_LEFT_UP    = 14;  // -> JUMP
constexpr uint8_t PIN_LEFT_DOWN  = 27;  // -> SLIDE
// RIGHT GROUP
constexpr uint8_t PIN_RIGHT_RIGHT = 26; // -> RIGHT
constexpr uint8_t PIN_RIGHT_UP    = 25; // -> JUMP
constexpr uint8_t PIN_RIGHT_DOWN  = 33; // -> SLIDE

// --- Status LED (GPIO -> resistor -> green LED -> GND) -----------------------
constexpr uint8_t PIN_STATUS_LED = 18;

// --- Timing -----------------------------------------------------------------
constexpr unsigned long DEBOUNCE_MS  = 25;   // signal must be stable this long
constexpr unsigned long LED_BLINK_MS = 350;  // PAUSED blink half-period

// --- Protocol strings (ESP32 -> PC) ------------------------------------------
constexpr const char* CMD_LEFT  = "LEFT";
constexpr const char* CMD_RIGHT = "RIGHT";
constexpr const char* CMD_JUMP  = "JUMP";
constexpr const char* CMD_SLIDE = "SLIDE";
constexpr const char* MSG_READY = "READY";

}  // namespace Config
