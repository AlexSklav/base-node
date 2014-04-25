#include "Arduino.h"
#include <avr/eeprom.h>
#include <math.h>
#include <Wire.h>

#include "BaseNode.h"

#define P(str) (strcpy_P(p_buffer_, PSTR(str)), p_buffer_)


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
  if (n_bytes <= MAX_PAYLOAD_LENGTH) {
    for (int i = 0; i < n_bytes; i++) {
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
void BaseNode::begin() {
    // The reset latch is used for programming over the communictions bus.
    // Pull it low to enter programming mode.
    digitalWrite(RESET_LATCH, HIGH);
    pinMode(RESET_LATCH, OUTPUT);
    Serial.begin(115200);
    load_config();
    dump_config();
    Wire.onRequest(handle_wire_request);
    Wire.onReceive(handle_wire_receive);
}

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

/* Process any available requests on the serial port, or through Wire/I2C. */
void BaseNode::listen() {
  if (read_serial_command()) {
    // A new-line-terminated command was successfully read into the buffer.
    // Call `ProcessSerialInput` to handle process command string.
    if (!process_serial_input()) {
      error(RETURN_UNKNOWN_COMMAND);
    }
  }
  if (wire_command_received_) {
    bytes_written_ = 0;
    bytes_read_ = 0;
    send_payload_length_ = true;
    return_code_ = RETURN_GENERAL_ERROR;
    process_wire_command();
    serialize(&return_code_, sizeof(return_code_));
    wire_command_received_ = false;

    // If this command is changing the programming mode, wait for
    // a specified delay before setting/resetting the latch; otherwise,
    // the i2c communication will interfere.
    if (cmd_ == CMD_SET_PROGRAMMING_MODE) {
      delay(1000);
      update_programming_mode_state();
    }
  }
}

/* Write a sequence of `size` bytes to the buffer. */
void BaseNode::serialize(const uint8_t* u, const uint16_t size) {
    for (uint16_t i = 0; i < size; i++) {
      buffer_[bytes_written_+i] = u[i];
    }
    bytes_written_ += size;
}

/* Print the configuration of the extension module to the serial port. */
void BaseNode::dump_config() {
    Serial.println(String(name()) + " v" + String(hardware_version()));
    Serial.println(P("Firmware v") + String(software_version()));
    Serial.println(url());
    Serial.println(P("config_version=") + version_string(config_version()));
    Serial.println(P("i2c_address=") +
                   String(config_settings_.i2c_address, DEC));
    Serial.println(P("programming_mode=") +
                   String(config_settings_.programming_mode, DEC));
}

void BaseNode::set_programming_mode(bool on) {
  config_settings_.programming_mode = on;
  update_programming_mode_state();
  Serial.println(P("programming_mode=") +
                 String(config_settings_.programming_mode, DEC));
  save_config();
}

void BaseNode::update_programming_mode_state() {
  if (config_settings_.programming_mode == 0) {
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

/* If there is a request pending on the serial port, process it. */
bool BaseNode::process_serial_input() {
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
    
    if (match_function(P("set_programming_mode("))) {
      int32_t value;
      if (read_int(value)) {
        set_programming_mode(value > 0);
      }
      return true;
    }
    /* Command was not processed */
    return false;
}

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

/* If there is a request pending from the I2C bus, process it. */
void BaseNode::process_wire_command() {
  switch (cmd_) {
  case CMD_GET_PROTOCOL_NAME:
    if (payload_length_ == 0) {
      serialize(protocol_name(), strlen(protocol_name()));
      return_code_ = RETURN_OK;
    } else {
      return_code_ = RETURN_BAD_PACKET_SIZE;
    }
    break;
  case CMD_GET_PROTOCOL_VERSION:
    if (payload_length_ == 0) {
      serialize(protocol_version(), strlen(protocol_version()));
      return_code_ = RETURN_OK;
    } else {
      return_code_ = RETURN_BAD_PACKET_SIZE;
    }
    break;
  case CMD_GET_DEVICE_NAME:
    if (payload_length_ == 0) {
      serialize(name(), strlen(name()));
      return_code_ = RETURN_OK;
    } else {
      return_code_ = RETURN_BAD_PACKET_SIZE;
    }
    break;
  case CMD_GET_MANUFACTURER:
    if (payload_length_ == 0) {
      serialize(manufacturer(), strlen(manufacturer()));
      return_code_ = RETURN_OK;
    } else {
      return_code_ = RETURN_BAD_PACKET_SIZE;
    }
    break;
  case CMD_GET_SOFTWARE_VERSION:
    if (payload_length_ == 0) {
      serialize(software_version(), strlen(software_version()));
      return_code_ = RETURN_OK;
    } else {
      return_code_ = RETURN_BAD_PACKET_SIZE;
    }
    break;
  case CMD_GET_HARDWARE_VERSION:
    if (payload_length_ == 0) {
      serialize(hardware_version(), strlen(hardware_version()));
      return_code_ = RETURN_OK;
    } else {
      return_code_ = RETURN_BAD_PACKET_SIZE;
    }
    break;
  case CMD_GET_URL:
    if (payload_length_ == 0) {
      serialize(url(), strlen(url()));
      return_code_ = RETURN_OK;
    } else {
      return_code_ = RETURN_BAD_PACKET_SIZE;
    }
    break;
  case CMD_SET_PROGRAMMING_MODE:
    if (payload_length_ == 1) {
      set_programming_mode(read<uint8_t>() > 0);
      return_code_ = RETURN_OK;
    } else {
      return_code_ = RETURN_BAD_PACKET_SIZE;
    }
    break;
  default:
    break;
  }
}

void BaseNode::error(uint8_t code) {
  Serial.println(P("Error ") + String(code, DEC));
}

bool BaseNode::read_int(int32_t &value) {
  char* str;
  char* end;
  if (read_value(str, end)) {
    char val_str[end - str + 1];
    memcpy(val_str, str, end - str);
    val_str[end - str] = 0;
    value = atoi(val_str);
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

BaseNode::Version BaseNode::config_version() {
  Version config_version;
  eeprom_read_block((void*)&config_version, (void*)EEPROM_CONFIG_SETTINGS,
                    sizeof(config_version));
  return config_version;
}

void BaseNode::load_config(bool use_defaults) {
  eeprom_read_block((void*)&config_settings_,
                    (void*)EEPROM_CONFIG_SETTINGS, sizeof(config_settings_));

  // If we're not at the expected version by the end of the upgrade path,
  // set everything to default values.
  if (!(config_settings_.version.major==0 &&
     config_settings_.version.minor==0 &&
     config_settings_.version.micro==0) || use_defaults) {

    config_settings_.version.major=0;
    config_settings_.version.minor=0;
    config_settings_.version.micro=0;
    config_settings_.i2c_address = 10;
    config_settings_.programming_mode = 0;
    save_config();
  }
  update_programming_mode_state();
  Wire.begin(config_settings_.i2c_address);
}

void BaseNode::save_config() {
  eeprom_write_block((void*)&config_settings_,
                     (void*)EEPROM_CONFIG_SETTINGS, sizeof(config_settings_));
}

void BaseNode::set_i2c_address(uint8_t address) {
  config_settings_.i2c_address = address;
  Wire.begin(config_settings_.i2c_address);
  Serial.println(P("i2c_address=") + String(config_settings_.i2c_address,
                 DEC));
  save_config();
}

