@echo off
REM Store the version of the firmware in a variable.
REM See https://stackoverflow.com/a/2340018/345236
for /f %%i in ('python -c "import versioneer; print(versioneer.get_version())"') do set VERSION=%%i

REM Use define build flags to set the following during build:
REM
REM  - Firmware software version (``___SOFTWARE_VERSION___``)
REM  - Hardware major version (``___HARDWARE_MAJOR_VERSION``)
REM  - Hardware minor version (``___HARDWARE_MINOR_VERSION``)
REM  - Serial baud rate (``HV_SWITCHING_BOARD_BAUD_RATE``)
REM
REM .. versionchanged:: 0.9
REM     Add serial baud rate (``HV_SWITCHING_BOARD_BAUD_RATE``).
for /f "tokens=1-4*" %%a in ("%*") do (
    set HARDWARE_MAJOR_VERSION=%%a
    set HARDWARE_MINOR_VERSION=%%b
    set HV_SWITCHING_BOARD_BAUD_RATE=%%c
    set HV_SWITCHING_BOARD_I2C_RATE=%%d
    set therest=%%e
)
set FLAGS="-D___SOFTWARE_VERSION___=\"%VERSION%\"" -D___HARDWARE_MAJOR_VERSION___=%HARDWARE_MAJOR_VERSION% -D___HARDWARE_MINOR_VERSION___=%HARDWARE_MINOR_VERSION% -DHV_SWITCHING_BOARD_BAUD_RATE=%HV_SWITCHING_BOARD_BAUD_RATE% -DHV_SWITCHING_BOARD_I2C_RATE=%HV_SWITCHING_BOARD_I2C_RATE% %therest%
echo %FLAGS%
