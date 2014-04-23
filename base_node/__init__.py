from struct import pack, unpack
import os
import glob


def get_sketch_directory():
    '''
    Return directory containing the `base_node` Arduino sketch.
    '''
    import base_node
    return os.path.join(os.path.abspath(os.path.dirname(base_node.__file__)),
                        'Arduino', 'BaseNode')


def get_includes():
    '''
    Return directories containing the `base_node` Arduino header files.

    Modules that need to compile against `base_node` should use this function
    to locate the appropriate include directories.

    Notes
    =====

    For example:

        import base_node
        ...
        print ' '.join(['-I%s' % i for i in base_node.get_includes()])
        ...

    '''
    return [get_sketch_directory()]


def get_sources():
    '''
    Return `base_node` Arduino source file paths.

    Modules that need to compile against `base_node` should use this function
    to locate the appropriate source files to compile.

    Notes
    =====

    For example:

        import base_node
        ...
        print ' '.join(base_node.get_sources())
        ...

    '''
    return glob.glob(os.path.join(get_sketch_directory(), '*.c*'))


def install_as_arduino_library(sketchbook_home, overwrite=False):
    '''
    Provided with an Arduino sketchbook home directory, install `BaseNode` as a
    library.
    '''
    from path_helpers import path

    sketch_path = path(get_sketch_directory())
    library_path = path(sketchbook_home).joinpath('libraries',
                                                  sketch_path.name)
    if library_path.exists():
        if overwrite:
            library_path.rmtree()
        else:
            raise IOError('Library already exists: "%s"' % library_path)
    sketch_path.copytree(library_path)


# command codes
CMD_GET_PROTOCOL_NAME       = 0x80
CMD_GET_PROTOCOL_VERSION    = 0x81
CMD_GET_DEVICE_NAME         = 0x82
CMD_GET_MANUFACTURER        = 0x83
CMD_GET_HARDWARE_VERSION    = 0x84
CMD_GET_SOFTWARE_VERSION    = 0x85
CMD_GET_URL                 = 0x86
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


class BaseNode():
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

    def read_uint8(self):
        return self.data.pop(0)

    def serialize_uint8(self, num):
        self.write_buffer.append(num)

    def serialize_float(self, num):
        self.write_buffer.extend(unpack('BBBB', pack('f', num)))
