@echo off
echo ========================================
echo PrivateClaw 构建脚本
echo ========================================
echo.

echo [1/3] 安装前端依赖...
cd frontend
call npm install
if errorlevel 1 (
    echo 前端依赖安装失败!
    pause
    exit /b 1
)

echo.
echo [2/3] 构建前端...
call npm run build
if errorlevel 1 (
    echo 前端构建失败!
    pause
    exit /b 1
)

echo.
echo [3/3] 复制到后端...
cd ..
if exist privateclaw\channels\web\static\ (
    rmdir /S /Q privateclaw\channels\web\static\
)
xcopy /E /I frontend\dist\* privateclaw\channels\web\static\
if errorlevel 1 (
    echo 复制失败!
    pause
    exit /b 1
)

echo.
echo ========================================
echo 构建完成!
echo ========================================
echo.
echo 现在运行: run.bat serve
echo 然后访问: http://localhost:8000
echo.
pause
