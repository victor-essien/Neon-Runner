#include "controller.h"
#include <string.h>

// Physical button -> game command. Duplicated UP/DOWN buttons are intentional.
Controller::Controller()
    : _buttons{Button(Config::PIN_LEFT_LEFT,   Config::CMD_LEFT),
               Button(Config::PIN_LEFT_UP,     Config::CMD_JUMP),
               Button(Config::PIN_LEFT_DOWN,   Config::CMD_SLIDE),
               Button(Config::PIN_RIGHT_RIGHT, Config::CMD_RIGHT),
               Button(Config::PIN_RIGHT_UP,    Config::CMD_JUMP),
               Button(Config::PIN_RIGHT_DOWN,  Config::CMD_SLIDE)},
      _led(Config::PIN_STATUS_LED),
      _rxLen(0) {}

void Controller::begin() {
  Serial.begin(Config::SERIAL_BAUD);
  _led.begin();
  for (uint8_t i = 0; i < BUTTON_COUNT; ++i) _buttons[i].begin();

  _led.playStartupSequence();
  _led.setState(LedState::On);         // READY = solid green
  Serial.println(Config::MSG_READY);
}

void Controller::update() {
  for (uint8_t i = 0; i < BUTTON_COUNT; ++i) {
    if (_buttons[i].update()) sendCommand(_buttons[i].command());
  }
  readIncoming();
  _led.update();
}

void Controller::sendCommand(const char* command) {
  Serial.println(command);             // "LEFT\r\n", "JUMP\r\n", ...
  if (Config::DEBUG_SERIAL) {
    Serial.print("# sent ");
    Serial.println(command);
  }
}

void Controller::readIncoming() {
  while (Serial.available() > 0) {
    const char c = static_cast<char>(Serial.read());
    if (c == '\n') {
      _rx[_rxLen] = '\0';
      if (_rxLen > 0) handleMessage(_rx);
      _rxLen = 0;
    } else if (c != '\r') {
      if (_rxLen < RX_BUFFER_SIZE - 1) _rx[_rxLen++] = c;
      else _rxLen = 0;                 // overflow: discard garbage line
    }
  }
}

// Only known messages are acted on; everything else is ignored.
void Controller::handleMessage(const char* message) {
  if (strcmp(message, "READY") == 0 || strcmp(message, "GAME_START") == 0) {
    _led.setState(LedState::On);
  } else if (strcmp(message, "PAUSED") == 0) {
    _led.setState(LedState::Blink);
  } else if (strcmp(message, "GAME_OVER") == 0) {
    _led.setState(LedState::Off);
  }
}
