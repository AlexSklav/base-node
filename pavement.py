# -*- encoding: utf-8 -*-
# from paver.easy import task, needs, options, cmdopts, sh
# from paver.setuputils import setup
#
# import base_node
# import versioneer
from setuptools import setup
from setuptools.command.build_py import build_py
from distutils.cmd import Command
import versioneer
import base_node


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
      include_package_data=True,
      python_requires='>=3.6',
      install_requires=['paver']
      )


# @task
# @cmdopts([('sketchbook_home=', 'S', 'Arduino sketchbook home.'),
#           ('overwrite', 'o', 'Overwrite existing library')])
# def install_as_arduino_library():
#     """
#     Provided with an Arduino sketchbook home directory, install `BaseNode` as a
#     library.
#     """
#     try:
#         base_node.install_as_arduino_library(options.sketchbook_home,
#                                              getattr(options, 'overwrite', False))
#     except IOError as error:
#         print(str(error))
#
#
# @task
# @cmdopts([('sconsflags=', 'f', 'Flags to pass to SCons.')])
# def build_firmware():
#     sh('scons %s' % getattr(options, 'sconsflags', ''))
#
#
# @task
# @needs('generate_setup', 'minilib', 'setuptools.command.sdist',
#        'build_firmware')
# def sdist():
#     """Overrides sdist to make sure that our setup.py is generated."""
#     pass

# Custom 'install_as_arduino_library' command
class InstallArduinoLibrary(Command):
    description = "Install `BaseNode` as an Arduino library"
    user_options = [
        ('sketchbook-home=', 'S', 'Arduino sketchbook home.'),
        ('overwrite', 'o', 'Overwrite existing library'),
    ]

    def initialize_options(self):
        self.sketchbook_home = None
        self.overwrite = False

    def finalize_options(self):
        pass

    def run(self):
        try:
            base_node.install_as_arduino_library(self.sketchbook_home, self.overwrite)
        except IOError as error:
            print(str(error))


# Custom 'build_firmware' command
class BuildFirmware(Command):
    description = "Build firmware using SCons"
    user_options = [('sconsflags=', 'f', 'Flags to pass to SCons.')]

    def initialize_options(self):
        self.sconsflags = ''

    def finalize_options(self):
        pass

    def run(self):
        import subprocess
        subprocess.run(f'scons {self.sconsflags}', shell=True)


# Override sdist to ensure setup.py is generated and include custom build commands
class SDistCommand(build_py):
    def run(self):
        self.run_command('build_firmware')
        super().run()


# Update the setup() function with custom commands
setup(
    # ...
    cmdclass={
        'sdist': SDistCommand,
        'install_as_arduino_library': InstallArduinoLibrary,
        'build_firmware': BuildFirmware,
    },
)
