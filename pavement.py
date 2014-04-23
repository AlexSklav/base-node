from paver.easy import task, needs, options, cmdopts, path
from paver.setuputils import setup

import version
import base_node

# Setup script for path

setup(name='wheeler.base_node',
      version=version.getVersion(),
      description='Common base class/API for embedded hardware devices.',
      author='Ryan Fobel',
      author_email='ryan@fobel.net',
      url='http://microfluidics.utoronto.ca/git/firmware___base_node.git',
      license='GPLv2',
      packages=['base_node'],
      package_data={'base_node': ['Arduino/BaseNode/*.*']})


@task
@cmdopts([('sketchbook_home=', 'S', 'Arduino sketchbook home.'),
          ('overwrite', 'o', 'Overwrite existing library')])
def install_as_arduino_library():
    '''
    Provided with an Arduino sketchbook home directory, install `BaseNode` as a
    library.
    '''
    sketch_path = path(base_node.get_sketch_directory())
    library_path = path(options.sketchbook_home).joinpath('libraries',
                                                          sketch_path.name)
    if library_path.exists():
        if not getattr(options, 'overwrite', False):
            print 'Library already exists: "%s"' % library_path
            return
        else:
            print 'Removing existing library: "%s"' % library_path
            library_path.rmtree()
    sketch_path.copytree(library_path)


@task
@needs('generate_setup', 'minilib', 'setuptools.command.sdist')
def sdist():
    """Overrides sdist to make sure that our setup.py is generated."""
    pass
