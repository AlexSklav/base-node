from collections import OrderedDict, namedtuple
import gc
import struct
import time


# command codes
CMD_GET_PROTOCOL_NAME       = 0x80
CMD_GET_PROTOCOL_VERSION    = 0x81
CMD_GET_DEVICE_NAME         = 0x82
CMD_GET_MANUFACTURER        = 0x83
CMD_GET_HARDWARE_VERSION    = 0x84
CMD_GET_SOFTWARE_VERSION    = 0x85
CMD_GET_URL                 = 0x86

# avoid command codes 0x88-0x8F to prevent conflicts with
# boards emulating PCA9505 GPIO chips (e.g.,
# http://microfluidics.utoronto.ca/git/firmware___hv_switching_board.git)

CMD_PERSISTENT_READ         = 0x90
CMD_PERSISTENT_WRITE        = 0x91
CMD_LOAD_CONFIG             = 0x92
CMD_SET_PIN_MODE            = 0x93
CMD_DIGITAL_READ            = 0x94
CMD_DIGITAL_WRITE           = 0x95
CMD_ANALOG_READ             = 0x96
CMD_ANALOG_WRITE            = 0x97

# avoid command codes 0x98-0x9F to prevent conflicts with
# boards emulating PCA9505 GPIO chips (e.g.,
# http://microfluidics.utoronto.ca/git/firmware___hv_switching_board.git)

CMD_SET_PROGRAMMING_MODE    = 0xA0

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


def replace(self, **kwargs):
    dict_ = OrderedDict(zip(dir(self)[1:], self))
    dict_.update(**kwargs)
    return self.__class__(**dict_)


class Driver:
    def __init__(self, i2c, addr):
        self.i2c = i2c
        self.addr = addr

    def _run_command(self, cmd, *args, ignore_response=False):
        self.i2c.writeto(self.addr, bytes((cmd, ) + args))
        gc.collect()

        if ignore_response:
            return None

        time.sleep(.001)
        response = self.i2c.readfrom(self.addr, 2)

        payload_length, return_code = response
        if return_code == RETURN_OK:
            error = None
        elif return_code == RETURN_GENERAL_ERROR:
            error = 'RETURN_GENERAL_ERROR'
        elif return_code == RETURN_UNKNOWN_COMMAND:
            error = 'RETURN_UNKNOWN_COMMAND'
        elif return_code == RETURN_TIMEOUT:
            error = 'RETURN_TIMEOUT'
        elif return_code == RETURN_NOT_CONNECTED:
            error = 'RETURN_NOT_CONNECTED'
        elif return_code == RETURN_BAD_INDEX:
            error = 'RETURN_BAD_INDEX'
        elif return_code == RETURN_BAD_PACKET_SIZE:
            error = 'RETURN_BAD_PACKET_SIZE'
        elif return_code == RETURN_BAD_CRC:
            error = 'RETURN_BAD_CRC'
        elif return_code == RETURN_BAD_VALUE:
            error = 'RETURN_BAD_VALUE'
        elif return_code == RETURN_MAX_PAYLOAD_EXCEEDED:
            error = 'RETURN_MAX_PAYLOAD_EXCEEDED'

        if error:
            raise RuntimeError('Error executing command. `%s`' % error)
        else:
            return self.i2c.readfrom(self.addr, payload_length)[:-1]


class BaseDriver(Driver):
    CONFIG_STRUCT_STR = '<hhhBB16s9s9s'
    CONFIG_STRUCT_SIZE = struct.calcsize(CONFIG_STRUCT_STR)
    Config = namedtuple('Config', 'version_major version_minor version_patch i2c_address programming_mode uuid pin_mode_bytes pin_state_bytes')

    @property
    def config(self):
        data = b''.join([self.persistent_read(i)
                         for i in range(self.CONFIG_STRUCT_SIZE)])
        return self.Config(*struct.unpack(self.CONFIG_STRUCT_STR, data))

    @config.setter
    def config(self, value):
        for i, byte in enumerate(struct.pack(self.CONFIG_STRUCT_STR, *value)):
            self.persistent_write(i, byte)

    def load_config(self, use_defaults=False):
        self._run_command(CMD_LOAD_CONFIG, 1 if use_defaults else 0,
                          ignore_response=True)

    def _get_string(self, cmd):
        return self._run_command(cmd).decode('utf-8')

    def protocol_name(self):
        return self._get_string(CMD_GET_PROTOCOL_NAME)

    def protocol_version(self):
        return self._get_string(CMD_GET_PROTOCOL_VERSION)

    def device_name(self):
        return self._get_string(CMD_GET_DEVICE_NAME)

    def manufacturer(self):
        return self._get_string(CMD_GET_MANUFACTURER)

    def hardware_version(self):
        return self._get_string(CMD_GET_HARDWARE_VERSION)

    def software_version(self):
        return self._get_string(CMD_GET_SOFTWARE_VERSION)

    def url(self):
        return self._get_string(CMD_GET_URL)

    def digital_read(self, pin):
        response = self._run_command(CMD_DIGITAL_READ, pin)
        return (response[0] != 0)

    def digital_write(self, pin, value):
        self._run_command(CMD_DIGITAL_WRITE, pin, value, ignore_response=True)

    def analog_read(self, pin):
        response = self._run_command(CMD_ANALOG_READ, pin)
        return struct.unpack('<h', response)

    def analog_write(self, pin, value):
        self._run_command(CMD_ANALOG_WRITE, pin, value, ignore_response=True)

    def pin_mode(self, pin, mode):
        self._run_command(CMD_SET_PIN_MODE, pin, mode, ignore_response=True)

    def persistent_read(self, address):
        return self._run_command(CMD_PERSISTENT_READ,
                                 *tuple(struct.pack('<h', address)))

    def persistent_write(self, address, value):
        self._run_command(CMD_PERSISTENT_WRITE, *tuple(struct.pack('<hB',
                                                                   address,
                                                                   value)),
                          ignore_response=True)
