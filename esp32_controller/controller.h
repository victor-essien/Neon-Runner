#pragma once
#include <Arduino.h>
#include "buttons.h"
#include "config.h"
#include "status_led.h"

// Owns the six buttons and the status LED. Converts physical presses into
// serial commands and applies LED state messages sent by the PC.
class Controller {
 public:
  Controller();

  void begin();
  void update();

 private:
  static constexpr uint8_t BUTTON_COUNT = 6;
  static constexpr uint8_t RX_BUFFER_SIZE = 32;

  Button _buttons[BUTTON_COUNT];
  StatusLed _led;
  char _rx[RX_BUFFER_SIZE];
  uint8_t _rxLen;

  void sendCommand(const char* command);
  void readIncoming();
  void handleMessage(const char* message);
};
