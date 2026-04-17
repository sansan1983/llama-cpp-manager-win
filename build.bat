@echo off
chcp 65001 >nul
echo ==================================================
echo   Llama.cpp Manager - Windows 构建脚本
echo ==================================================
echo.

:: 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 安装依赖
echo [1/4] 安装依赖...
pip install pyinstaller PyQt6 requests -q
if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)

:: 清理旧构建
echo.
echo [2/4] 清理旧构建...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "LlamaCppManager.exe" del /q LlamaCppManager.exe

:: 执行打包
echo.
echo [3/4] 执行打包...
pyinstaller ^
    --name=LlamaCppManager ^
    --windowed ^
    --onefile ^
    --noconfirm ^
    --distpath=dist ^
    --workpath=build ^
    --add-data=resources;resources ^
    --hidden-import=PyQt6 ^
    --hidden-import=PyQt6.QtCore ^
    --hidden-import=PyQt6.QtGui ^
    --hidden-import=PyQt6.QtWidgets ^
    --hidden-import=requests ^
    --collect-submodules=PyQt6 ^
    --collect-binaries=PyQt6 ^
    src\main.py

if errorlevel 1 (
    echo.
    echo [错误] 打包失败!
    pause
    exit /b 1
)

:: 整理输出
echo.
echo [4/4] 整理输出...
if not exist "output" mkdir output
if not exist "output\LlamaCppManager-win" mkdir output\LlamaCppManager-win

:: 复制文件
copy dist\LlamaCppManager.exe output\LlamaCppManager-win\ /y
copy README.md output\LlamaCppManager-win\ /y 2>nul
copy requirements.txt output\LlamaCppManager-win\ /y 2>nul
copy 版本说明.txt output\LlamaCppManager-win\ /y 2>nul

:: 复制 resources
if exist "resources" (
    if not exist "output\LlamaCppManager-win\resources" mkdir output\LlamaCppManager-win\resources
    xcopy /s /y resources\* output\LlamaCppManager-win\resources\ >nul 2>&1
)

echo.
echo ==================================================
echo   构建完成!
echo   输出目录: %CD%\output\LlamaCppManager-win
echo   可执行文件: %CD%\output\LlamaCppManager-win\LlamaCppManager.exe
echo ==================================================
echo.
pause
