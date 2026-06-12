@echo off
echo ========================================
echo PrivateClaw Installation
echo ========================================
echo.

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

pip install langchain langchain-core langchain-openai langchain-anthropic langchain-community langgraph openai anthropic chromadb fastapi uvicorn websockets click rich pydantic pydantic-settings python-dotenv httpx PyYAML

echo.
echo ========================================
echo Installation complete!
echo ========================================
echo.
echo To start PrivateClaw, run:
echo   run.bat serve
echo.
pause
