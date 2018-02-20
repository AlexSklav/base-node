@echo off
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
REM Copy Arduino library to Conda include directory
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

REM Install source directory as Python package.
echo "Install source directory as Python package."
"%PYTHON%" setup.py install --single-version-externally-managed --record record.txt
if errorlevel 1 exit 1
