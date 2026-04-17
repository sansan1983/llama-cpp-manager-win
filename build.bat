@echo off
setlocal EnableDelayedExpansion

echo.
echo ================================================
echo   Llama.cpp Manager - Windows 构建脚本
echo ================================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 安装依赖
echo [1/4] 安装依赖...
pip install pyinstaller PyQt6 requests
if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)

REM 生成 spec 文件
echo [2/4] 生成配置...
python -c "
import os, sys
from pathlib import Path

project_dir = Path(sys.argv[1])
spec_content = '''# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path

block_cipher = None
project_dir = Path(r\"%s\")
src_dir = project_dir / \"src\"
resources_dir = project_dir / \"resources\"

a = Analysis(
    [str(src_dir / \"main.py\")],
    pathex=[str(src_dir)],
    binaries=[],
    datas=[
        (str(resources_dir), \"resources\"),
    ],
    hiddenimports=[
        \"PyQt6.QtCore\",
        \"PyQt6.QtGui\",
        \"PyQt6.QtWidgets\",
        \"requests\",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=\"LlamaCppManager\",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name=\"LlamaCppManager\",
)
''' % project_dir

with open(project_dir / 'llama_manager.spec', 'w', encoding='utf-8') as f:
    f.write(spec_content)
print('Spec file created')
' "%cd%"

REM PyInstaller 构建
echo [3/4] 打包应用程序...
pyinstaller llama_manager.spec --noconfirm

echo [4/4] 整理输出...
if not exist "output" mkdir output
xcopy /E /Y /I "dist\LlamaCppManager" "output\LlamaCppManager-win"
copy README.md "output\LlamaCppManager-win\"

echo.
echo ================================================
echo   构建完成!
echo   输出目录: %cd%\output\LlamaCppManager-win
echo ================================================
echo.

pause
