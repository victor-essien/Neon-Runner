#include "status_led.h"
#include "config.h"

StatusLed::StatusLed(uint8_t pin)
    : _pin(pin), _state(LedState::Off), _level(false), _lastToggleMs(0) {}

void StatusLed::begin() {
  pinMode(_pin, OUTPUT);
  digitalWrite(_pin, LOW);
}

void StatusLed::setState(LedState state) {
  _state = state;
  _lastToggleMs = millis();
  _level = (state != LedState::Off);   // Blink starts in the lit phase
  digitalWrite(_pin, _level ? HIGH : LOW);
}

void StatusLed::update() {
  if (_state != LedState::Blink) return;
  if (millis() - _lastToggleMs >= Config::LED_BLINK_MS) {
    _lastToggleMs = millis();
    _level = !_level;
    digitalWrite(_pin, _level ? HIGH : LOW);
  }
}

void StatusLed::playStartupSequence() {
  for (int i = 0; i < 3; ++i) {
    digitalWrite(_pin, HIGH);
    delay(120);
    digitalWrite(_pin, LOW);
    delay(120);
  }
}
