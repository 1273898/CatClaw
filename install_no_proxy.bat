@echo off
REM PrivateClaw installation script - No Proxy version

echo ========================================
echo PrivateClaw Installation (No Proxy)
echo ========================================
echo.

REM Check Python version
python --version 2>NUL
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.11 or higher from https://www.python.org/
    pause
    exit /b 1
)

echo.
echo [Step 1] Disabling proxy for pip...
echo.

REM Create pip config to disable proxy
if not exist "%APPDATA%\pip" mkdir "%APPDATA%\pip"
echo [global] > "%APPDATA%\pip\pip.ini"
echo proxy = >> "%APPDATA%\pip\pip.ini"
echo.
echo Proxy disabled in: %APPDATA%\pip\pip.ini
echo.

echo [Step 2] Installing dependencies...
echo.

REM Install with explicit no-proxy
pip install --proxy "" --no-cache-dir langchain langchain-core langchain-openai langchain-anthropic langchain-community langgraph openai anthropic chromadb fastapi uvicorn websockets click rich pydantic pydantic-settings python-dotenv httpx PyYAML

if errorlevel 1 (
    echo.
    echo [Step 2b] Trying alternative method...
    echo.
    python -m pip install --proxy "" --no-cache-dir langchain langchain-core langchain-openai langchain-anthropic langchain-community langgraph openai anthropic chromadb fastapi uvicorn websockets click rich pydantic pydantic-settings python-dotenv httpx PyYAML
)

echo.
echo ========================================
echo Installation complete!
echo ========================================
echo.
echo To start PrivateClaw, run:
echo   run.bat serve
echo.
pause
