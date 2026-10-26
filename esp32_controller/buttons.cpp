#include "buttons.h"
#include "config.h"

Button::Button(uint8_t pin, const char* command)
    : _pin(pin),
      _command(command),
      _stableLevel(HIGH),
      _lastReading(HIGH),
      _lastChangeMs(0) {}

void Button::begin() {
  pinMode(_pin, INPUT_PULLUP);
  _stableLevel = digitalRead(_pin);
  _lastReading = _stableLevel;
  _lastChangeMs = millis();
}

bool Button::update() {
  const int reading = digitalRead(_pin);
  const unsigned long now = millis();

  // Raw level changed: restart the stability timer.
  if (reading != _lastReading) {
    _lastReading = reading;
    _lastChangeMs = now;
  }

  // Raw level has been stable long enough and differs from the accepted one.
  if ((now - _lastChangeMs) >= Config::DEBOUNCE_MS && reading != _stableLevel) {
    _stableLevel = reading;
    return _stableLevel == LOW;        // report presses only, not releases
  }
  return false;
}
