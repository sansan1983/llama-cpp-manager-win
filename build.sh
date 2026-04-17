#!/bin/bash
# ================================================
# Llama.cpp Manager for Windows - 构建脚本 (Linux/macOS)
# 在 Linux/macOS 上交叉编译 Windows 版本
# ================================================

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "================================================"
echo "  Llama.cpp Manager - Windows 构建脚本"
echo "================================================"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 Python3"
    exit 1
fi

PYTHON=$(command -v python3)

# 检查 pip
if ! $PYTHON -m pip --version &> /dev/null; then
    echo "[错误] 未找到 pip"
    exit 1
fi

# 虚拟环境
VENV_DIR="$PROJECT_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "[1/5] 创建虚拟环境..."
    $PYTHON -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

# 安装依赖
echo "[2/5] 安装 Python 依赖..."
pip install --upgrade pip
pip install pyinstaller PyQt6 requests

# 创建 spec 文件
echo "[3/5] 生成 PyInstaller 配置..."
cat > "$PROJECT_DIR/llama_manager.spec" << 'SPEC'
# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path

block_cipher = None
project_dir = Path(__file__).parent
src_dir = project_dir / "src"
resources_dir = project_dir / "resources"

a = Analysis(
    [str(src_dir / "main.py")],
    pathex=[str(src_dir)],
    binaries=[],
    datas=[
        (str(resources_dir), "resources"),
    ],
    hiddenimports=[
        "PyQt6.QtCore",
        "PyQt6.QtGui",
        "PyQt6.QtWidgets",
        "requests",
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
    name='LlamaCppManager',
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
    name='LlamaCppManager',
)
SPEC

# PyInstaller 构建
echo "[4/5] 打包应用程序..."
pyinstaller llama_manager.spec --noconfirm

# 整理输出
echo "[5/5] 整理输出..."
OUTPUT_DIR="$PROJECT_DIR/dist/LlamaCppManager-win"
mkdir -p "$OUTPUT_DIR"

# 复制构建产物
cp -r "$PROJECT_DIR/dist/LlamaCppManager/"* "$OUTPUT_DIR/"

# 复制 README
cp "$PROJECT_DIR/README.md" "$OUTPUT_DIR/"

# 创建版本说明
cat > "$OUTPUT_DIR/版本说明.txt" << 'VERSION'
Llama.cpp Manager for Windows
=============================

版本: 1.0.0
平台: Windows x64

使用说明:
1. 运行 LlamaCppManager.exe
2. 如果提示找不到 llama-server，点击"设置" -> "下载 llama.cpp"
3. 或者手动从 https://github.com/ggerganov/llama.cpp/releases 下载

推荐下载:
- Vulkan 版本 (有显卡加速): llama-*-bin-win-vulkan-x64.zip
- CUDA 版本 (NVIDIA): llama-*-bin-win-cublas-x64.zip
- CPU 版本: llama-*-bin-win-cpu-x64.zip

配置文件位置: %APPDATA%\LlamaCppManager\config.json
VERSION

echo ""
echo "================================================"
echo "  构建完成!"
echo "  输出目录: $OUTPUT_DIR"
echo "================================================"
echo ""
