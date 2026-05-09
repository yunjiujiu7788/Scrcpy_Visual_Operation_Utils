@echo off
chcp 65001 >nul
title Scrcpy 视觉操作通用工具

echo ========================================
echo   Scrcpy 视觉操作通用工具
echo   MaaFramework + OpenCV + PaddleOCR
echo ========================================
echo.

:: 检查 Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请安装 Python 3.10+
    pause
    exit /b 1
)

:: 检查并安装依赖
echo [检查] 依赖包...
python -c "import maa, cv2, paddleocr" >nul 2>&1
if %errorlevel% neq 0 (
    echo [提示] 正在安装必要依赖...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)

:: 检查 ADB
adb --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] ADB 未在 PATH 中找到，请确保 ADB 已安装
)

echo [启动] 正在启动...
echo.

python main.py %*

if %errorlevel% neq 0 (
    echo.
    echo [错误] 程序异常退出，请查看日志文件
)

pause
