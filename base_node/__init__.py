# -*- encoding: utf-8 -*-
import path_helpers as ph

from typing import List, Dict, Optional
from .driver import BaseNode, HIGH, LOW, INPUT, OUTPUT, INPUT_PULLUP

from ._version import get_versions

__version__ = get_versions()['version']
del get_versions

__all__ = ['__version__', 'BaseNode', 'HIGH', 'INPUT', 'INPUT_PULLUP', 'LOW',
           'OUTPUT', 'get_firmwares', 'get_includes', 'get_sources',
           'install_as_arduino_library', 'package_path']


def package_path() -> ph.path:
    return ph.path(__file__).parent


def get_sketch_directory() -> ph.path:
    """
    Return directory containing the `basic` Arduino sketch.
    """
    return package_path().joinpath('Arduino', 'BaseNode', 'examples', 'basic')


def get_includes() -> List[ph.path]:
    """
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

    """
    return [package_path().joinpath('Arduino', 'BaseNode')]


def get_sources() -> List[str]:
    """
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

    """
    sources = get_sketch_directory().files('*.c*')
    for p in get_includes():
        sources = ph.path(p).files('*.c*')
    return sources


def get_firmwares() -> Dict:
    """
    Return compiled Arduino hex file paths.

    This function may be used to locate firmware binaries that are available
    for flashing to [Arduino][1] boards.

    [1]: http://arduino.cc
    """
    return {'uno': package_path().joinpath('firmware', 'basic.hex')}


def install_as_arduino_library(sketchbook_home: str, overwrite: Optional[bool] = False) -> None:
    """
    Provided with an Arduino sketchbook home directory, install `BaseNode` as a
    library.
    """
    sketch_path = ph.path(get_sketch_directory())
    library_path = ph.path(sketchbook_home).joinpath('libraries', sketch_path.name)
    if library_path.exists():
        if overwrite:
            library_path.rmtree()
        else:
            raise IOError(f'Library already exists: `{library_path}`')
    sketch_path.copytree(library_path)
