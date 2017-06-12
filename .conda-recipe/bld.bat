@echo off
set PKG_NAME=base-node
set ARDUINO_NAME=BaseNode
set PLATFORMIO_ENVS=uno teensy31

setlocal enableextensions
md "%PREFIX%"\Library\include\Arduino
FOR %%i IN (%PLATFORMIO_ENVS%) DO (
  md "%PREFIX%"\Library\bin\platformio\%PKG_NAME%\%%i
)
endlocal

REM REM Build firmware
pio run
if errorlevel 1 exit 1
# Copy Arduino library to Conda include directory
xcopy /S /Y /I /Q "%SRC_DIR%"\lib\%ARDUINO_NAME% "%PREFIX%"\Library\include\Arduino\%ARDUINO_NAME%
REM REM Copy compiled firmware to Conda bin directory
copy "%SRC_DIR%"\platformio.ini "%PREFIX%"\Library\bin\platformio\%PKG_NAME%
FOR %%i IN (%PLATFORMIO_ENVS%) DO (
  copy "%SRC_DIR%"\.pioenvs\%%i\firmware.hex "%PREFIX%"\Library\bin\platformio\%PKG_NAME%\%%i\firmware.hex
)
if errorlevel 1 exit 1

REM Generate `setup.py` from `pavement.py` definition.
"%PYTHON%" -m paver generate_setup
if errorlevel 1 exit 1

REM **Workaround** `conda build` runs a copy of `setup.py` named
REM `conda-build-script.py` with the recipe directory as the only argument.
REM This causes paver to fail, since the recipe directory is not a valid paver
REM task name.
REM
REM We can work around this by wrapping the original contents of `setup.py` in
REM an `if` block to only execute during package installation.
"%PYTHON%" -c "from __future__ import print_function; input_ = open('setup.py', 'r'); data = input_.read(); input_.close(); output_ = open('setup.py', 'w'); output_.write('\n'.join(['import sys', 'import path_helpers as ph', '''if ph.path(sys.argv[0]).name == 'conda-build-script.py':''', '    sys.argv.pop()', 'else:', '\n'.join([('    ' + d) for d in data.splitlines()])])); output_.close(); print(open('setup.py', 'r').read())"
if errorlevel 1 exit 1

REM Install source directory as Python package.
echo "Install source directory as Python package."
"%PYTHON%" setup.py install --single-version-externally-managed --record record.txt
if errorlevel 1 exit 1
