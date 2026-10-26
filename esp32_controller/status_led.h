#pragma once
#include <Arduino.h>

enum class LedState : uint8_t { Off, On, Blink };

// Green status LED driven by the firmware.
//   READY / RUNNING -> On,  PAUSED -> Blink,  GAME_OVER -> Off
class StatusLed {
 public:
  explicit StatusLed(uint8_t pin);

  void begin();
  void setState(LedState state);
  void update();                       // call every loop(); drives blinking
  void playStartupSequence();          // short blocking blink-blink-blink

 private:
  uint8_t _pin;
  LedState _state;
  bool _level;
  unsigned long _lastToggleMs;
};
