#ifndef NO_WATCHDOG
#include <avr/wdt.h>
#endif  // #ifndef NO_WATCHDOG
#include <EEPROM.h>
#include <Wire.h>
#include <BaseNode.h>

#ifndef ___HARDWARE_VERSION___
#define ___HARDWARE_VERSION___ "1.0"
#endif
#ifndef ___SOFTWARE_VERSION___
#define ___SOFTWARE_VERSION___ "0.1"
#endif

BaseNode Node;

const char BaseNode::PROTOCOL_NAME_[] PROGMEM = "Extension module protocol";
const char BaseNode::PROTOCOL_VERSION_[] PROGMEM = "0.1";
const char BaseNode::MANUFACTURER_[] PROGMEM = "Sci-bots Inc.";
const char BaseNode::NAME_[] PROGMEM = "Extension Module Proto Board";
const char BaseNode::HARDWARE_VERSION_[] PROGMEM = ___HARDWARE_VERSION___;
const char BaseNode::SOFTWARE_VERSION_[] PROGMEM = ___SOFTWARE_VERSION___;
const char BaseNode::URL_[] PROGMEM = "https://github.com/sci-bots/dropbot";


void setup() {
  Node.begin();
}

void loop() {
  Node.listen();
}
