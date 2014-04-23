from paver.easy import task, needs
from paver.setuputils import setup

import version

# Setup script for path

setup(name='base_node',
      version=version.getVersion(),
      description='Common base class/API for embedded hardware devices.',
      author='Ryan Fobel',
      author_email='ryan@fobel.net',
      url='http://microfluidics.utoronto.ca/git/firmware___base_node.git',
      license='GPLv2',
      packages=['base_node'],
      package_data={'base_node': ['Arduino/BaseNode/*.*']})


@task
@needs('generate_setup', 'minilib', 'setuptools.command.sdist')
def sdist():
    """Overrides sdist to make sure that our setup.py is generated."""
    pass
