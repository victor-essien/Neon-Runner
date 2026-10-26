// NEON RUNNER - ESP32 physical controller firmware
// Board: any ESP32 DevKit (ESP32 Dev Module). Serial: 115200 baud.
// See README.md for wiring and upload instructions.
#include "controller.h"

Controller controller;

void setup() {
  controller.begin();
}

void loop() {
  controller.update();
}
