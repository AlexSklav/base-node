#ifndef ___BASE_NODE__H___
#define ___BASE_NODE__H___

#include "Arduino.h"
#define __PROG_TYPES_COMPAT__
#include <avr/pgmspace.h>  // `prog_char`
#include <Wire.h>
#include <stdint.h>


class BaseNode {
public:
  static const uint8_t RESET_LATCH = 7;

  struct Version {
      uint16_t major;
      uint16_t minor;
      uint16_t micro;
  };

  struct BaseConfigSettings {
      Version version;
      uint8_t i2c_address;
      uint8_t programming_mode;
      uint32_t serial_number;
      uint8_t pin_mode[9];
      uint8_t pin_state[9];
  };

  // Persistent storage _(e.g., EEPROM)_ addresses.
  static const uint16_t EEPROM_CONFIG_SETTINGS =      	    0;
  static const uint16_t PERSISTENT_SERIAL_NUMBER_ADDRESS =  8;
  static const uint16_t PERSISTENT_PIN_MODE_ADDRESS =      12;
  static const uint16_t PERSISTENT_PIN_STATE_ADDRESS =     21;

  // reserved commands
  static const uint8_t CMD_GET_PROTOCOL_NAME =        0x80;
  static const uint8_t CMD_GET_PROTOCOL_VERSION =     0x81;
  static const uint8_t CMD_GET_DEVICE_NAME =          0x82;
  static const uint8_t CMD_GET_MANUFACTURER =         0x83;
  static const uint8_t CMD_GET_HARDWARE_VERSION =     0x84;
  static const uint8_t CMD_GET_SOFTWARE_VERSION =     0x85;
  static const uint8_t CMD_GET_URL =                  0x86;

  static const uint8_t CMD_PERSISTENT_READ =          0x90;
  static const uint8_t CMD_PERSISTENT_WRITE =         0x91;
  static const uint8_t CMD_LOAD_CONFIG =              0x92;
  static const uint8_t CMD_SET_PIN_MODE =             0x93;
  static const uint8_t CMD_DIGITAL_READ =             0x94;
  static const uint8_t CMD_DIGITAL_WRITE =            0x95;
  static const uint8_t CMD_ANALOG_READ =              0x96;
  static const uint8_t CMD_ANALOG_WRITE =             0x97;

  static const uint8_t CMD_SET_PROGRAMMING_MODE =     0x9C;

  // reserved return codes
  static const uint8_t RETURN_OK =                    0x00;
  static const uint8_t RETURN_GENERAL_ERROR =         0x01;
  static const uint8_t RETURN_UNKNOWN_COMMAND =       0x02;
  static const uint8_t RETURN_TIMEOUT =               0x03;
  static const uint8_t RETURN_NOT_CONNECTED =         0x04;
  static const uint8_t RETURN_BAD_INDEX =             0x05;
  static const uint8_t RETURN_BAD_PACKET_SIZE =       0x06;
  static const uint8_t RETURN_BAD_CRC =               0x07;
  static const uint8_t RETURN_BAD_VALUE =             0x08;
  static const uint8_t RETURN_MAX_PAYLOAD_EXCEEDED =  0x09;

  static const uint16_t MAX_PAYLOAD_LENGTH = 100;
  static const uint32_t BAUD_RATE = 115200;

  static void handle_wire_receive(int n_bytes);
  static void handle_wire_request();

  BaseNode() { debug_ = false; }
  virtual void begin();
  // local accessors
  const char* prog_string(const char* str) { strcpy_P(buffer_, str); return buffer_; }
  const char* name() { return prog_string(NAME_); }
  const char* hardware_version() { return prog_string(HARDWARE_VERSION_); }
  const char* url() { return prog_string(URL_); }
  const char* software_version() { return prog_string(SOFTWARE_VERSION_); }
  const char* protocol_name() { return prog_string(PROTOCOL_NAME_); }
  const char* protocol_version() { return prog_string(PROTOCOL_VERSION_); }
  const char* manufacturer() { return prog_string(MANUFACTURER_); }

  virtual void listen();
  void set_i2c_address(uint8_t address);
  void set_serial_number(uint32_t serial_number);
  Version base_config_version();
  bool match_function(const char* function_name);
  void set_debug(bool debug) { debug_ = debug; }
  /* The following two `persistent...` methods provide sub-classes a mechanism
   * to customize persistent storage.  For example, the Arduino DUE does not
   * support the `EEPROM` library used by the AVR chips. */
  virtual uint8_t persistent_read(uint16_t address);
  virtual void persistent_write(uint16_t address, uint8_t value);
  static uint16_t payload_length() { return payload_length_; }

  static bool send_payload_length_;
  static uint8_t cmd_;
  static uint16_t bytes_read_; // bytes that have been read (by Read methods)
  static uint16_t bytes_written_; // bytes that have been written (by Serialize method)
  static uint16_t payload_length_;
  static bool wire_command_received_;
  static char buffer_[MAX_PAYLOAD_LENGTH];
  static char p_buffer_[100];
protected:
  virtual void process_wire_command();
  virtual bool process_serial_input();
  // inheritted classes should override this method if they support ISP
  virtual bool supports_isp() { return false; }
  void set_programming_mode(bool on);
  void update_programming_mode_state();
  BaseConfigSettings base_config_settings_;
  uint8_t return_code_;
  template<typename T> void serialize(T data, uint16_t size) {
    serialize((const uint8_t*)data, size); }
  void serialize(const uint8_t* u, const uint16_t size);
  const char* read_string();
  template <typename T> T read() {
    T result = *(T *)(buffer_ + bytes_read_);
    uint32_t size = sizeof(T);
    bytes_read_ += size;
    return result;
  }

  String version_string(Version version);
  bool read_value(char* &str, char* &end);
  bool read_int(int32_t &value);
  bool read_float(float &value);
  bool read_serial_command();
  void error(uint8_t code);
  virtual void dump_config();
  virtual void load_config(bool use_defaults=false);
  virtual void save_config();

  static const char SOFTWARE_VERSION_[] PROGMEM;
  static const char NAME_[] PROGMEM;
  static const char HARDWARE_VERSION_[] PROGMEM;
  static const char MANUFACTURER_[] PROGMEM;
  static const char URL_[] PROGMEM;
  static const char PROTOCOL_NAME_[] PROGMEM;
  static const char PROTOCOL_VERSION_[] PROGMEM;

  bool debug_;
};

#endif // ___BASE_NODE__H___
