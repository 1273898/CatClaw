@echo off
REM Fix proxy configuration for pip

echo ========================================
echo Fixing Proxy Configuration
echo ========================================
echo.

echo [1] Checking current proxy settings...
echo.

REM Check environment variables
echo Environment Variables:
echo   HTTP_PROXY=%HTTP_PROXY%
echo   HTTPS_PROXY=%HTTPS_PROXY%
echo   http_proxy=%http_proxy%
echo   https_proxy=%https_proxy%
echo.

REM Check pip config
echo [2] Checking pip configuration...
echo.

if exist "%APPDATA%\pip\pip.ini" (
    echo Current pip.ini:
    type "%APPDATA%\pip\pip.ini"
    echo.
) else (
    echo No pip.ini found at: %APPDATA%\pip\pip.ini
    echo.
)

REM Create/fix pip config
echo [3] Creating clean pip configuration...
echo.

if not exist "%APPDATA%\pip" mkdir "%APPDATA%\pip"
(
echo [global]
echo timeout = 60
echo trusted-host = pypi.org
echo                pypi.python.org
echo                files.pythonhosted.org
) > "%APPDATA%\pip\pip.ini"

echo Created: %APPDATA%\pip\pip.ini
echo.

REM Clear proxy environment variables for this session
echo [4] Clearing proxy environment variables...
echo.

set HTTP_PROXY=
set HTTPS_PROXY=
set http_proxy=
set https_proxy=

echo Proxy cleared for this session.
echo.

echo ========================================
echo Proxy configuration fixed!
echo ========================================
echo.
echo Now run: install_no_proxy.bat
echo.
pause
