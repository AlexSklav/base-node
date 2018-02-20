from __future__ import absolute_import
from __future__ import print_function

from paver.easy import task, needs, options, cmdopts, sh
from paver.setuputils import setup

import base_node
import versioneer


# Setup script for path

setup(name='base-node',
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
      description='Common base class/API for embedded hardware devices.',
      author='Ryan Fobel and Christian Fobel',
      author_email='ryan@fobel.net and christian@fobel.net',
      url='https://github.com/sci-bots/base-node',
      license='GPLv2',
      packages=['base_node'],
      include_package_data=True)


@task
@cmdopts([('sketchbook_home=', 'S', 'Arduino sketchbook home.'),
          ('overwrite', 'o', 'Overwrite existing library')])
def install_as_arduino_library():
    '''
    Provided with an Arduino sketchbook home directory, install `BaseNode` as a
    library.
    '''
    try:
        base_node.install_as_arduino_library(options.sketchbook_home,
                                             getattr(options, 'overwrite',
                                                     False))
    except IOError as error:
        print(str(error))


@task
@cmdopts([('sconsflags=', 'f', 'Flags to pass to SCons.')])
def build_firmware():
    sh('scons %s' % getattr(options, 'sconsflags', ''))


@task
@needs('generate_setup', 'minilib', 'setuptools.command.sdist',
       'build_firmware')
def sdist():
    """Overrides sdist to make sure that our setup.py is generated."""
    pass
