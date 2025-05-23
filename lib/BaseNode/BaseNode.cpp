#ifndef NO_WATCHDOG
#include <avr/wdt.h>
#endif  // #ifndef NO_WATCHDOG
#include "Arduino.h"
#ifndef NO_EEPROM
#include <avr/eeprom.h>
#endif
#include <math.h>
#ifndef NO_EEPROM
#include <EEPROM.h>
#endif

#include "BaseNode.h"

#define P(str) (strcpy_P(p_buffer_, PSTR(str)), p_buffer_)


#ifndef NO_WATCHDOG
void wdt_init(void) __attribute__((naked)) __attribute__((section(".init3")));

void wdt_init(void) {
  MCUSR = 0;
  wdt_disable();
  return;
}
#endif  // #ifndef NO_WATCHDOG


// initialize static members
bool BaseNode::send_payload_length_ = false;
uint8_t BaseNode::cmd_ = 0;
uint16_t BaseNode::bytes_read_ = 0;
uint16_t BaseNode::bytes_written_ = 0;
uint16_t BaseNode::payload_length_ = 0;
bool BaseNode::wire_command_received_ = false;
char BaseNode::buffer_[MAX_PAYLOAD_LENGTH];
char BaseNode::p_buffer_[100];

void BaseNode::handle_wire_receive(int n_bytes) {
  cmd_ = Wire.read();
  n_bytes--;
  payload_length_ = n_bytes;
  uint16_t bytes = static_cast<uint16_t>(n_bytes);
  if (bytes <= MAX_PAYLOAD_LENGTH) {
    for (uint16_t i = 0; i < bytes; i++) {
      buffer_[i] = Wire.read();
    }
  }
  wire_command_received_ = true;
}

void BaseNode::handle_wire_request() {
  if (send_payload_length_) {
    Wire.write((uint8_t*)&bytes_written_,
               sizeof(bytes_written_));
    send_payload_length_ = false;
  } else {
    Wire.write((uint8_t*)buffer_, bytes_written_);
  }
}

/* Initialize the communications for the extension module. */
void BaseNode::begin(uint32_t baudrate) {
    if (supports_isp()) {
      // The reset latch is used for programming over the communictions bus.
      // Pull it low to enter programming mode.
      digitalWrite(RESET_LATCH, HIGH);
      pinMode(RESET_LATCH, OUTPUT);
    }
#ifndef NO_SERIAL
    Serial.begin(baudrate);
#endif
#ifndef NO_EEPROM
    load_config();
#ifndef NO_SERIAL
    dump_config();
#endif
#endif
    Wire.onRequest(handle_wire_request);
    Wire.onReceive(handle_wire_receive);

#ifdef I2C_CLOCK
    // set the i2c clock
    Wire.setClock(I2C_CLOCK);
#endif  // #ifdef I2C_CLOCK

#if !defined(NO_BROADCAST) and !defined(NO_BROADCAST_API)
    // By default, enable receiving of broadcast messages (i.e., messages sent to
    // address 0).  This can be enabled/disabled through the
    // `CMD_SET_GENERAL_CALL_ENABLED` I2C command.
    general_call(true);
#endif  // #if !defined(NO_BROADCAST) and !defined(NO_BROADCAST_API)
}

#ifndef NO_SERIAL
bool BaseNode::read_serial_command() {
  if (Serial.available()) {
    byte len = Serial.readBytesUntil('\n', buffer_,
                                     sizeof(buffer_));
    buffer_[len] = 0;
    bytes_read_ = 0;
    return true;
  }
  return false;
}
#endif

/* Process any available requests on the serial port, or through Wire/I2C. */
void BaseNode::listen() {
#ifndef NO_SERIAL
  if (read_serial_command()) {
    // A new-line-terminated command was successfully read into the buffer.
    // Call `ProcessSerialInput` to handle process command string.
    if (!process_serial_input()) {
      error(RETURN_UNKNOWN_COMMAND);
    }
  }
#endif
  if (wire_command_received_) {
    bytes_written_ = 0;
    bytes_read_ = 0;
    send_payload_length_ = true;
    return_code_ = RETURN_GENERAL_ERROR;
    process_wire_command();
    if (send_payload_length_) {
      serialize(&return_code_, sizeof(return_code_));
    }
    wire_command_received_ = false;

#ifndef NO_EEPROM
    if (supports_isp()) {
      // If this command is changing the programming mode, wait for
      // a specified delay before setting/resetting the latch; otherwise,
      // the i2c communication will interfere.
      if (cmd_ == CMD_SET_PROGRAMMING_MODE) {
        delay(1000);
        update_programming_mode_state();
      }
    }
#endif
  }
}

/* Write a sequence of `size` bytes to the buffer. */
void BaseNode::serialize(const uint8_t* u, const uint16_t size) {
    for (uint16_t i = 0; i < size; i++) {
      buffer_[bytes_written_+i] = u[i];
    }
    bytes_written_ += size;
}

#ifndef NO_EEPROM
#ifndef NO_SERIAL
/* Print the configuration of the extension module to the serial port. */
void BaseNode::dump_config() {
    Serial.println(String(name()) + " v" + String(hardware_version()));
    Serial.println(P("Firmware v") + String(software_version()));
    Serial.println(url());
    Serial.println(P("base_config_version=") + version_string(base_config_version()));
    Serial.println(P("i2c_address=") +
                   String(base_config_settings_.i2c_address, DEC));
    Serial.println(P("programming_mode=") +
                   String(base_config_settings_.programming_mode, DEC));
    print_uuid();
    if (supports_isp()) {
      Serial.println(P("supports_ISP=true"));
    } else {
      Serial.println(P("supports_ISP=false"));
    }
}
#endif  // #ifndef NO_SERIAL

void BaseNode::set_programming_mode(bool on) {
  base_config_settings_.programming_mode = on;
  Serial.println(P("programming_mode=") +
                 String(base_config_settings_.programming_mode, DEC));
  save_config();
}

void BaseNode::update_programming_mode_state() {
  if (base_config_settings_.programming_mode == 0) {
    // pull SDA low to reset latch
    pinMode(A5, OUTPUT);
    digitalWrite(A5, LOW);
    pinMode(A5, INPUT);
  } else {
    // set latch
    digitalWrite(RESET_LATCH, LOW);
    digitalWrite(RESET_LATCH, HIGH);
  }
}
#endif

#ifndef NO_SERIAL
/* If there is a request pending on the serial port, process it. */
bool BaseNode::process_serial_input() {
#ifndef NO_EEPROM
    if (match_function(P("reset_config()"))) {
        load_config(true);
        dump_config();
        return true;
    }

    if (match_function(P("config()"))) {
        dump_config();
        return true;
    }

    if (match_function(P("set_i2c_address("))) {
      int32_t value;
      if (read_int(value)) {
        set_i2c_address(value);
      }
      return true;
    }

    if (match_function(P("set_uuid("))) {
      int32_t b;
      uint8_t uuid[16];
      for (uint8_t i = 0; i < 16; i++) {
        if (read_hex(b)) {
          uuid[i] = b;
        } else {
        return false;
        }
      }
      set_uuid(uuid);
      return true;
    }

    if (supports_isp() && match_function(P("set_programming_mode("))) {
      int32_t value;
      if (read_int(value)) {
        set_programming_mode(value > 0);
      }
      return true;
    }
#endif

    /* Command was not processed */
    return false;
}
#endif  // #ifndef NO_SERIAL

bool BaseNode::match_function(const char* function_name) {
  if (strstr(buffer_, "()")) {
    return strcmp(buffer_, function_name)==0;
  } else {
    char* substr = strstr(buffer_, function_name);
    if (substr != NULL && substr == buffer_
        && substr[strlen(substr) - 1] == ')') {
      buffer_[strlen(substr) - 1] = 0;
      bytes_read_ += strlen(function_name);
      return true;
    } else {
      return false;
    }
  }
}

#ifndef NO_EEPROM
uint8_t BaseNode::persistent_read(uint16_t address) {
  return EEPROM.read(address);
}

void BaseNode::persistent_write(uint16_t address, uint8_t value) {
  EEPROM.write(address, value);
}
#endif

/* If there is a request pending from the I2C bus, process it. */
void BaseNode::process_wire_command() {
  switch (cmd_) {
  case CMD_GET_PROTOCOL_NAME:
    if (payload_length() == 0) {
      serialize(protocol_name(), strlen(protocol_name()));
      return_code_ = RETURN_OK;
    } else {
      return_code_ = RETURN_BAD_PACKET_SIZE;
    }
    break;
  case CMD_GET_PROTOCOL_VERSION:
    if (payload_length() == 0) {
      serialize(protocol_version(), strlen(protocol_version()));
      return_code_ = RETURN_OK;
    } else {
      return_code_ = RETURN_BAD_PACKET_SIZE;
    }
    break;
  case CMD_GET_DEVICE_NAME:
    if (payload_length() == 0) {
      serialize(name(), strlen(name()));
      return_code_ = RETURN_OK;
    } else {
      return_code_ = RETURN_BAD_PACKET_SIZE;
    }
    break;
  case CMD_GET_MANUFACTURER:
    if (payload_length() == 0) {
      serialize(manufacturer(), strlen(manufacturer()));
      return_code_ = RETURN_OK;
    } else {
      return_code_ = RETURN_BAD_PACKET_SIZE;
    }
    break;
  case CMD_GET_SOFTWARE_VERSION:
    if (payload_length() == 0) {
      serialize(software_version(), strlen(software_version()));
      return_code_ = RETURN_OK;
    } else {
      return_code_ = RETURN_BAD_PACKET_SIZE;
    }
    break;
  case CMD_GET_HARDWARE_VERSION:
    if (payload_length() == 0) {
      serialize(hardware_version(), strlen(hardware_version()));
      return_code_ = RETURN_OK;
    } else {
      return_code_ = RETURN_BAD_PACKET_SIZE;
    }
    break;
  case CMD_GET_URL:
    if (payload_length() == 0) {
      serialize(url(), strlen(url()));
      return_code_ = RETURN_OK;
    } else {
      return_code_ = RETURN_BAD_PACKET_SIZE;
    }
    break;
#ifndef NO_EEPROM
  case CMD_SET_PROGRAMMING_MODE:
    if (supports_isp()) {
      if (payload_length() == 1) {
        set_programming_mode(read<uint8_t>() > 0);
        return_code_ = RETURN_OK;
      } else {
        return_code_ = RETURN_BAD_PACKET_SIZE;
      }
    } else {
      return_code_ = RETURN_GENERAL_ERROR;
    }
    break;
  case CMD_PERSISTENT_READ:
    if (payload_length() == 2) {
      uint16_t address = read<uint16_t>();
      uint8_t value = persistent_read(address);
      serialize(&value, sizeof(value));
      return_code_ = RETURN_OK;
    } else {
      return_code_ = RETURN_BAD_PACKET_SIZE;
    }
    break;
  case CMD_PERSISTENT_WRITE:
    if (payload_length() == 3) {
      uint16_t address = read<uint16_t>();
      uint8_t value = read<uint8_t>();
      persistent_write(address, value);
      return_code_ = RETURN_OK;
    } else {
      return_code_ = RETURN_BAD_PACKET_SIZE;
    }
    break;
  case CMD_LOAD_CONFIG:
    if (payload_length() == 1) {
      return_code_ = RETURN_OK;
      bool use_defaults = read<uint8_t>() > 0;
      load_config(use_defaults);
    } else {
      return_code_ = RETURN_BAD_PACKET_SIZE;
    }
    break;
#endif
  case CMD_SET_PIN_MODE:
    if (payload_length() == 2) {
      uint8_t pin = read<uint8_t>();
      uint8_t mode = read<uint8_t>();
#ifndef NO_SERIAL
      Serial.println("pinMode(" + String(pin) + ", " + String(mode) + ")");
#endif
      pinMode(pin, mode);
      return_code_ = RETURN_OK;
    } else {
      return_code_ = RETURN_BAD_PACKET_SIZE;
    }
    break;
  case CMD_DIGITAL_WRITE:
    if (payload_length() == 2) {
      uint8_t pin = read<uint8_t>();
      uint8_t value = read<uint8_t>();
#ifndef NO_SERIAL
      Serial.println("digitalWrite(" + String(pin) + ", " + String(value) + \
        ")");
#endif
      digitalWrite(pin, value);
      return_code_ = RETURN_OK;
    } else {
      return_code_ = RETURN_BAD_PACKET_SIZE;
    }
    break;
  case CMD_DIGITAL_READ:
    if (payload_length() == 1) {
      uint8_t pin = read<uint8_t>();
      uint8_t value = digitalRead(pin);
#ifndef NO_SERIAL
      Serial.println("digitalRead(" + String(pin) + ") = " + String(value));
#endif
      serialize(&value, sizeof(value));
      return_code_ = RETURN_OK;
    } else {
      return_code_ = RETURN_BAD_PACKET_SIZE;
    }
    break;
  case CMD_ANALOG_WRITE:
    if (payload_length() == 2) {
      uint8_t pin =  read<uint8_t>();
      uint16_t value = read<uint16_t>();
#ifndef NO_SERIAL
      Serial.println("analogWrite(" + String(pin) + ", " + String(value) + ")");
#endif
      analogWrite(pin, value);
      return_code_ = RETURN_OK;
    } else {
      return_code_ = RETURN_BAD_PACKET_SIZE;
    }
    break;
  case CMD_ANALOG_READ:
    if (payload_length() == 1) {
      uint8_t pin = read<uint8_t>();
      uint16_t value = analogRead(pin);
#ifndef NO_SERIAL
      Serial.println("analogRead(" + String(pin) + ") = " + String(value));
#endif
      serialize(&value, sizeof(value));
      return_code_ = RETURN_OK;
    } else {
      return_code_ = RETURN_BAD_PACKET_SIZE;
    }
    break;
#ifndef NO_BROADCAST_API
  case CMD_GET_GENERAL_CALL_ENABLED:
    {
      const uint8_t general_call_enabled = general_call();
      serialize(&general_call_enabled, sizeof(general_call_enabled));
    }
    return_code_ = RETURN_OK;
    break;
  case CMD_SET_GENERAL_CALL_ENABLED:
    {
      const uint8_t general_call_enabled = read<uint8_t>();
      general_call(general_call_enabled);
    }
    return_code_ = RETURN_OK;
    break;
#endif  // #ifndef NO_BROADCAST_API
#ifndef NO_WATCHDOG
  case CMD_REBOOT:
      // Reboot.
#ifndef NO_SERIAL
      Serial.println("Rebooting...");
#endif  // #ifndef NO_SERIAL
      do {
        wdt_enable(WDTO_15MS);
        for(;;) {}
      } while(0);
      break;
#endif  // #ifndef NO_WATCHDOG
  case CMD_RESET_CONFIG:
    load_config(true);
    break;
  default:
    break;
  }
}

void BaseNode::error(uint8_t code) {
#ifndef NO_SERIAL
  Serial.println(P("Error ") + String(code, DEC));
#endif
}

bool BaseNode::read_int(int32_t &value) {
  char* str;
  char* end;
  if (read_value(str, end)) {
    char val_str[end - str + 1];
    memcpy(val_str, str, end - str);
    val_str[end - str] = 0;
    value = atol(val_str);
    return true;
  }
  return false;
}

bool BaseNode::read_hex(int32_t &value) {
  char* str;
  char* end;
  if (read_value(str, end)) {
    char val_str[end - str + 1];
    memcpy(val_str, str, end - str);
    val_str[end - str] = 0;
    value = strtol(val_str, NULL, 16);
    return true;
  }
  return false;
}

bool BaseNode::read_float(float &value) {
  char* str;
  char* end;
  if (read_value(str, end)) {
    char val_str[end - str + 1];
    memcpy(val_str, str, end - str);
    val_str[end - str] = 0;
    value = atof(val_str);
    return true;
  }
  return false;
}

bool BaseNode::read_value(char* &str, char* &end) {
  str = buffer_ + bytes_read_;
  end = strstr(str, ",");
  uint8_t len;
  if (end==NULL) { // no comma (convert whole string)
    len = strlen(str);
    end = str + len;
  } else { // convert up to (and including) comma
    len = end - str + 1;
  }
  if (len > 0) {
    bytes_read_ += len;
    return true;
  }
  error(RETURN_BAD_VALUE);
  return false;
}

String BaseNode::version_string(Version version) {
  return String(version.major) + "." + String(version.minor) + "." +
         String(version.micro);
}

#ifndef NO_EEPROM
BaseNode::Version BaseNode::base_config_version() {
  Version base_config_version;
  eeprom_read_block((void*)&base_config_version, (void*)EEPROM_CONFIG_SETTINGS,
                    sizeof(base_config_version));
  return base_config_version;
}

void BaseNode::load_config(bool use_defaults) {
  eeprom_read_block((void*)&base_config_settings_,
                    (void*)EEPROM_CONFIG_SETTINGS, sizeof(base_config_settings_));

  // If we're not at the expected version by the end of the upgrade path,
  // set everything to default values.
  if (!(base_config_settings_.version.major==0 &&
     base_config_settings_.version.minor==0 &&
     base_config_settings_.version.micro==3) || use_defaults) {
    base_config_settings_.version.major=0;
    base_config_settings_.version.minor=0;
    base_config_settings_.version.micro=3;
    base_config_settings_.i2c_address = 70;
    base_config_settings_.programming_mode = 0;
    memset(base_config_settings_.uuid, 0, 16);
    memset(base_config_settings_.pin_mode, 0, 9);
    memset(base_config_settings_.pin_state, 0, 9);
    save_config();
  }

  // Initialize pin mode and state of digital pins from persistent storage
  // _(i.e., EEPROM on AVR)_.
  for (uint8_t i = 0; i < ceil(float(NUM_DIGITAL_PINS) / 8.0); i++) {
    for (uint8_t j = 0; j < 8; j++) {
      if (i * 8 + j < NUM_DIGITAL_PINS) {
    	uint8_t mode = (base_config_settings_.pin_mode[i] >> j) & 0x01;
    	uint8_t state = (base_config_settings_.pin_state[i] >> j) & 0x01;

    	/*
    	Serial.print("pin " + String(i * 8 + j) + " (");
        if (mode==0) {
          if (state) {
            Serial.println("INPUT_PULLUP)");
          } else {
            Serial.println("INPUT)");
          }
    	} else {
          Serial.println("OUTPUT): " + String(state));
    	}
        */

        pinMode(i * 8 + j, mode);
        digitalWrite(i * 8 + j, state);
      }
    }
  }

#ifndef NO_EEPROM
  if (supports_isp()) {
    update_programming_mode_state();
  }
#endif

  Wire.begin(base_config_settings_.i2c_address);
}

void BaseNode::save_config() {
  eeprom_write_block((void*)&base_config_settings_,
                     (void*)EEPROM_CONFIG_SETTINGS,
                     sizeof(base_config_settings_));
}

void BaseNode::set_uuid(uint8_t uuid[16]) {
  memcpy(base_config_settings_.uuid, uuid, 16);
#ifndef NO_SERIAL
  print_uuid();
#endif
  save_config();
}

#ifndef NO_SERIAL
void BaseNode::print_uuid() {
  Serial.print(P("uuid="));
  for (uint8_t i = 0; i < 16; i++) {
    Serial.print(base_config_settings_.uuid[i], HEX);
    if (i < 15) {
      Serial.print("-");
    }
  }
  Serial.println();
}
#endif

void BaseNode::set_i2c_address(uint8_t address) {
  base_config_settings_.i2c_address = address;
  Wire.begin(base_config_settings_.i2c_address);
  Serial.println(P("i2c_address=") + String(base_config_settings_.i2c_address,
                 DEC));
  save_config();
}
#endif  // #ifndef NO_EEPROM

