from struct import pack, unpack

import numpy as np

PERSISTENT_SERIAL_NUMBER_ADDRESS = 8

# command codes
CMD_GET_PROTOCOL_NAME       = 0x80
CMD_GET_PROTOCOL_VERSION    = 0x81
CMD_GET_DEVICE_NAME         = 0x82
CMD_GET_MANUFACTURER        = 0x83
CMD_GET_HARDWARE_VERSION    = 0x84
CMD_GET_SOFTWARE_VERSION    = 0x85
CMD_GET_URL                 = 0x86

# avoid command codes 0x88-8F to prevent conflicts with
# boards emulating PCA9505 GPIO chips (e.g., 
# http://microfluidics.utoronto.ca/git/firmware___hv_switching_board.git)

CMD_PERSISTENT_READ         = 0x90
CMD_PERSISTENT_WRITE        = 0x91
CMD_LOAD_CONFIG             = 0x92
CMD_SET_PROGRAMMING_MODE    = 0x9F

# reserved return codes
RETURN_OK                   = 0x00
RETURN_GENERAL_ERROR        = 0x01
RETURN_UNKNOWN_COMMAND      = 0x02
RETURN_TIMEOUT              = 0x03
RETURN_NOT_CONNECTED        = 0x04
RETURN_BAD_INDEX            = 0x05
RETURN_BAD_PACKET_SIZE      = 0x06
RETURN_BAD_CRC              = 0x07
RETURN_BAD_VALUE            = 0x08
RETURN_MAX_PAYLOAD_EXCEEDED = 0x09


class BaseNode(object):
    def __init__(self, proxy, address):
        self.proxy = proxy
        self.address = address
        self.write_buffer = []

    def protocol_name(self):
        return self._get_string(CMD_GET_PROTOCOL_NAME)

    def protocol_version(self):
        return self._get_string(CMD_GET_PROTOCOL_VERSION)

    def name(self):
        return self._get_string(CMD_GET_DEVICE_NAME)

    def manufacturer(self):
        return self._get_string(CMD_GET_MANUFACTURER)

    def hardware_version(self):
        return self._get_string(CMD_GET_HARDWARE_VERSION)

    def software_version(self):
        return self._get_string(CMD_GET_SOFTWARE_VERSION)

    def url(self):
        return self._get_string(CMD_GET_URL)

    def persistent_read(self, address):
        # pack the address into a 16 bits
        data = unpack('BB', pack('H', address))
        self.write_buffer.extend(data)
        self.send_command(CMD_PERSISTENT_READ)
        return self.read_uint8()

    def persistent_write(self, address, byte, refresh_config=False):
        '''
        Write a single byte to an address in persistent memory.
        
        If refresh_config is True, load_config() is called afterward to
        refresh the configuration settings.
        '''        
        # pack the address into a 16 bits
        data = list(unpack('BB', pack('H', address)))
        data.append(byte)
        self.write_buffer.extend(data)
        self.send_command(CMD_PERSISTENT_WRITE)
        if refresh_config:
            self.load_config(False)

    def persistent_read_multibyte(self, address, count=None,
                                  dtype=np.uint8):
        nbytes = np.dtype(dtype).itemsize
        if count is not None:
            nbytes *= count

        # Read enough bytes starting at specified address to match the
        # requested number of the specified data type.
        data_bytes = np.array([self.persistent_read(address + i)
                               for i in xrange(nbytes)], dtype=np.uint8)

        # Cast byte array as array of specified data type.
        result = data_bytes.view(dtype)

        # If no count was specified, we return a scalar value rather than the
        # resultant array.
        if count is None:
            return result[0]
        return result

    def persistent_write_multibyte(self, address, data, refresh_config=False):
        '''
        Write multiple bytes to an address in persistent memory.
        
        If refresh_config is True, load_config() is called afterward to
        refresh the configuration settings.
        '''        
        for i, byte in enumerate(data.view(np.uint8)):
            self.persistent_write(address + i, int(byte))
        if refresh_config:
            self.load_config(False)

    @property
    def serial_number(self):
        return self.persistent_read_multibyte(
            PERSISTENT_SERIAL_NUMBER_ADDRESS, dtype=np.uint32)

    @serial_number.setter
    def serial_number(self, value):
        self.persistent_write_multibyte(PERSISTENT_SERIAL_NUMBER_ADDRESS,
                                        np.array([value], dtype=np.uint32),
                                        True)
        self.__serial_number = value

    def load_config(self, use_defaults=False):
        self.write_buffer.append((0,1)[use_defaults])
        self.send_command(CMD_LOAD_CONFIG)

    def set_programming_mode(self, on):
        self.write_buffer.append(on)
        self.send_command(CMD_SET_PROGRAMMING_MODE)

    def send_command(self, cmd):
        self.data = (self.proxy.i2c_send_command(self.address, cmd,
                                                 self.write_buffer)
                     .tolist())
        self.write_buffer = []

    def _get_string(self, cmd):
        self.send_command(cmd)
        return pack('B' * len(self.data), *self.data)

    def read_float(self):
        num = self.data[0:4]
        self.data = self.data[4:]
        return unpack('f', pack('BBBB', *num))[0]

    def read_uint16(self):
        num = self.data[0:2]
        self.data = self.data[2:]
        return unpack('H', pack('BB', *num))[0]

    def read_uint32(self):
        num = self.data[0:4]
        self.data = self.data[4:]
        return unpack('I', pack('BBBB', *num))[0]

    def read_uint8(self):
        return self.data.pop(0)

    def serialize_uint8(self, num):
        self.write_buffer.append(num)

    def serialize_float(self, num):
        self.write_buffer.extend(unpack('BBBB', pack('f', num)))
