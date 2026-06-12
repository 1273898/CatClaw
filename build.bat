@echo off
echo ========================================
echo PrivateClaw Build Script
echo ========================================
echo.

echo [1/3] Installing frontend dependencies...
cd frontend
call npm install
if errorlevel 1 (
    echo Frontend dependency installation failed!
    pause
    exit /b 1
)

echo.
echo [2/3] Building frontend...
call npm run build
if errorlevel 1 (
    echo Frontend build failed!
    pause
    exit /b 1
)

echo.
echo [3/3] Copying to backend...
cd ..
if exist privateclaw\channels\web\static\ (
    rmdir /S /Q privateclaw\channels\web\static\
)
xcopy /E /I frontend\dist\* privateclaw\channels\web\static\
if errorlevel 1 (
    echo Copy failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build complete!
echo ========================================
echo.
echo Now run: run.bat serve
echo Then visit: http://localhost:8000
echo.
pause
