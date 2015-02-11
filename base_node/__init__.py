import os
import glob

from path_helpers import path

from .driver import BaseNode, HIGH, LOW, INPUT, OUTPUT, INPUT_PULLUP


def package_path():
    return path(__file__).parent


def get_sketch_directory():
    '''
    Return directory containing the `basic` Arduino sketch.
    '''
    return package_path().joinpath('Arduino', 'BaseNode', 'examples', 'basic')


def get_includes():
    '''
    Return directories containing the `BaseNode.h` Arduino header file.

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
    return [package_path().joinpath('Arduino', 'BaseNode')]


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
    sources = get_sketch_directory().files('*.c*')
    for p in get_includes():
        sources = path(p).files('*.c*')
    return sources


def get_firmwares():

    '''
    Return compiled Arduino hex file paths.

    This function may be used to locate firmware binaries that are available
    for flashing to [Arduino][1] boards.

    [1]: http://arduino.cc
    '''
    return {'uno': package_path().joinpath('firmware', 'basic.hex')}


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
