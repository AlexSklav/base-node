import os
import glob

from .driver import BaseNode


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
