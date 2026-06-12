@echo off
REM PrivateClaw installation script for Windows

echo ========================================
echo PrivateClaw Installation
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
echo Installing dependencies...
echo.

REM Install core dependencies only (without proxy issues)
pip install --no-cache-dir langchain langchain-core langchain-openai langchain-anthropic langchain-community langgraph openai anthropic chromadb fastapi uvicorn websockets click rich pydantic pydantic-settings python-dotenv httpx PyYAML

if errorlevel 1 (
    echo.
    echo Installation failed. Trying without proxy...
    echo.
    pip install --no-cache-dir --proxy "" langchain langchain-core langchain-openai langchain-anthropic langchain-community langgraph openai anthropic chromadb fastapi uvicorn websockets click rich pydantic pydantic-settings python-dotenv httpx PyYAML
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
