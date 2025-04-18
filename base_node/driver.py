# -*- encoding: utf-8 -*-
import uuid

import numpy as np

from struct import pack, unpack

PERSISTENT_UUID_ADDRESS = 8

INPUT = 0
OUTPUT = 1
INPUT_PULLUP = 2
LOW = 0
HIGH = 1

A0 = 14
A1 = 15
A2 = 16
A3 = 17
A4 = 18
A5 = 19
A6 = 20
A7 = 21

# command codes
CMD_GET_PROTOCOL_NAME = 0x80
CMD_GET_PROTOCOL_VERSION = 0x81
CMD_GET_DEVICE_NAME = 0x82
CMD_GET_MANUFACTURER = 0x83
CMD_GET_HARDWARE_VERSION = 0x84
CMD_GET_SOFTWARE_VERSION = 0x85
CMD_GET_URL = 0x86

# avoid command codes 0x88-0x8F to prevent conflicts with
# boards emulating PCA9505 GPIO chips (e.g.,
# http://microfluidics.utoronto.ca/git/firmware___hv_switching_board.git)

CMD_PERSISTENT_READ = 0x90
CMD_PERSISTENT_WRITE = 0x91
CMD_LOAD_CONFIG = 0x92
CMD_SET_PIN_MODE = 0x93
CMD_DIGITAL_READ = 0x94
CMD_DIGITAL_WRITE = 0x95
CMD_ANALOG_READ = 0x96
CMD_ANALOG_WRITE = 0x97

# avoid command codes 0x98-0x9F to prevent conflicts with
# boards emulating PCA9505 GPIO chips (e.g.,
# http://microfluidics.utoronto.ca/git/firmware___hv_switching_board.git)

CMD_SET_PROGRAMMING_MODE = 0xA0

# reserved return codes
RETURN_OK = 0x00
RETURN_GENERAL_ERROR = 0x01
RETURN_UNKNOWN_COMMAND = 0x02
RETURN_TIMEOUT = 0x03
RETURN_NOT_CONNECTED = 0x04
RETURN_BAD_INDEX = 0x05
RETURN_BAD_PACKET_SIZE = 0x06
RETURN_BAD_CRC = 0x07
RETURN_BAD_VALUE = 0x08
RETURN_MAX_PAYLOAD_EXCEEDED = 0x09

# numpy data type corresponding to version 0.3.0 HV switching board
# configuration
CONFIG_DTYPE = np.dtype([('version', [('major', 'uint16'),
                                      ('minor', 'uint16'),
                                      ('micro', 'uint16')]),
                         ('i2c_address', 'uint8'),
                         ('programming_mode', 'uint8'),
                         ('uuid', 'S16'),
                         ('pin_mode', 'S9'),
                         ('pin_state', 'S9')])


class BaseNode:
    def __init__(self, proxy, address):
        self.proxy = proxy
        self.address = address
        self.write_buffer = []
        self.data = None

    def protocol_name(self) -> bytes:
        return self._get_string(CMD_GET_PROTOCOL_NAME)

    def protocol_version(self) -> bytes:
        return self._get_string(CMD_GET_PROTOCOL_VERSION)

    def name(self) -> bytes:
        return self._get_string(CMD_GET_DEVICE_NAME)

    def manufacturer(self) -> bytes:
        return self._get_string(CMD_GET_MANUFACTURER)

    def hardware_version(self) -> bytes:
        return self._get_string(CMD_GET_HARDWARE_VERSION)

    def software_version(self) -> bytes:
        return self._get_string(CMD_GET_SOFTWARE_VERSION)

    def url(self) -> bytes:
        return self._get_string(CMD_GET_URL)

    def pin_mode(self, pin: int, mode: int):
        self.serialize_uint8(pin)
        self.serialize_uint8(mode)
        self.send_command(CMD_SET_PIN_MODE)

    def digital_read(self, pin: int) -> int:
        self.serialize_uint8(pin)
        self.send_command(CMD_DIGITAL_READ)
        return self.read_uint8()

    def digital_write(self, pin: int, value: int):
        self.serialize_uint8(pin)
        self.serialize_uint8(value)
        self.send_command(CMD_DIGITAL_WRITE)

    def analog_read(self, pin: int) -> int:
        self.serialize_uint8(pin)
        self.send_command(CMD_ANALOG_READ)
        return self.read_uint16()

    def analog_write(self, pin: int, value: int):
        self.serialize_uint8(pin)
        self.serialize_uint16(value)
        self.send_command(CMD_ANALOG_WRITE)

    def persistent_read(self, address: int) -> int:
        # pack the address into a 16 bits
        self.serialize_uint16(address)
        self.send_command(CMD_PERSISTENT_READ)
        return self.read_uint8()

    def persistent_write(self, address: int, byte: int, refresh_config: bool = False):
        """
        Write a single byte to an address in persistent memory.

        If refresh_config is True, load_config() is called afterward to
        refresh the configuration settings.
        """
        # pack the address into a 16 bits
        data = list(unpack('BB', pack('H', address)))
        data.append(byte)
        self.write_buffer.extend(data)
        self.send_command(CMD_PERSISTENT_WRITE)
        if refresh_config:
            self.load_config(False)

    def persistent_read_multibyte(self, address: int, count: int = None, dtype=np.uint8):
        nbytes = np.dtype(dtype).itemsize
        if count is not None:
            nbytes *= count

        # Read enough bytes starting at specified address to match the
        # requested number of the specified data type.
        data_bytes = np.array([self.persistent_read(address + i)
                               for i in range(nbytes)], dtype=np.uint8)

        # Cast byte array as array of specified data type.
        result = data_bytes.view(dtype)

        # If no count was specified, we return a scalar value rather than the
        # resultant array.
        if count is None:
            return result[0]
        return result

    def persistent_write_multibyte(self, address: int, data: np.ndarray, refresh_config: bool = False):
        """
        Write multiple bytes to an address in persistent memory.

        If refresh_config is True, load_config() is called afterward to
        refresh the configuration settings.
        """
        for i, byte in enumerate(data.view(np.uint8)):
            self.persistent_write(address + i, int(byte))
        if refresh_config:
            self.load_config(False)

    @property
    def uuid(self) -> uuid.UUID:
        return uuid.UUID(bytes=self.persistent_read_multibyte(
            PERSISTENT_UUID_ADDRESS, 16).tobytes())

    def load_config(self, use_defaults: bool = False):
        self.write_buffer.append((0, 1)[use_defaults])
        self.send_command(CMD_LOAD_CONFIG)

    def set_programming_mode(self, on: bool):
        self.write_buffer.append(on)
        self.send_command(CMD_SET_PROGRAMMING_MODE)

    def send_command(self, cmd):
        self.data = self.proxy.i2c_send_command(self.address, cmd, self.write_buffer).tolist()
        self.write_buffer = []

    def _get_string(self, cmd) -> bytes:
        self.send_command(cmd)
        return pack('B' * len(self.data), *self.data)

    def read_uint8(self) -> int:
        return self.data.pop(0)

    def read_uint16(self) -> int:
        num = self.data[0:2]
        self.data = self.data[2:]
        return unpack('H', pack('BB', *num))[0]

    def read_uint32(self) -> int:
        num = self.data[0:4]
        self.data = self.data[4:]
        return unpack('I', pack('BBBB', *num))[0]

    def read_float(self) -> float:
        num = self.data[0:4]
        self.data = self.data[4:]
        return unpack('f', pack('BBBB', *num))[0]

    def serialize_uint8(self, num: int):
        self.serialize(np.array([num], dtype=np.uint8))

    def serialize_uint16(self, num: int):
        self.serialize(np.array([num], dtype=np.uint16))

    def serialize_uint32(self, num: int):
        self.serialize(np.array([num], dtype=np.uint32))

    def serialize_float(self, num: float):
        self.serialize(np.array([num], dtype=np.float32))

    def serialize(self, data: np.array):
        for byte in data.view(np.uint8):
            self.write_buffer.append(byte)
