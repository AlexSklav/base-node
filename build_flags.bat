@echo off
REM Store the version of the firmware in a variable.
REM See https://stackoverflow.com/a/2340018/345236
for /f %%i in ('python -c "import versioneer; print(versioneer.get_version())"') do set VERSION=%%i

set FLAGS="-D___SOFTWARE_VERSION___=\"%VERSION%\"" %*
echo %FLAGS%
