import os
import sys

from paver.easy import task, needs, options, cmdopts, path
from paver.setuputils import setup

# add the current directory as the first listing on the python path
# so that we import the correct version.py
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import version
import base_node


# Setup script for path

setup(name='wheeler.base-node',
      version=version.getVersion(),
      description='Common base class/API for embedded hardware devices.',
      author='Ryan Fobel',
      author_email='ryan@fobel.net',
      url='http://microfluidics.utoronto.ca/git/firmware___base_node.git',
      license='GPLv2',
      packages=['base_node']
)


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
    except IOError, error:
        print str(error)

@task
@cmdopts([('sconsflags=', 'f', 'Flags to pass to SCons.')])
def build_firmware():
    sh('scons %s' % getattr(options, 'sconsflags', ''))

@task
@needs('generate_setup', 'minilib', 'setuptools.command.sdist')
def sdist():
    """Overrides sdist to make sure that our setup.py is generated."""
    pass
