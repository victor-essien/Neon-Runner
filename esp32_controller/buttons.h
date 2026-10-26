#pragma once
#include <Arduino.h>

// A debounced push button wired between a GPIO and GND (INPUT_PULLUP).
//   HIGH = released, LOW = pressed.
// update() returns true exactly ONCE per physical press (on the press edge),
// so holding a button never floods the serial port.
class Button {
 public:
  Button(uint8_t pin, const char* command);

  void begin();
  bool update();                       // call every loop(); true on a new press
  const char* command() const { return _command; }
  bool isDown() const { return _stableLevel == LOW; }

 private:
  uint8_t _pin;
  const char* _command;
  int _stableLevel;                    // debounced level
  int _lastReading;                    // last raw level
  unsigned long _lastChangeMs;         // when the raw level last changed
};
