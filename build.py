#!/usr/bin/env python3
"""
Llama.cpp Manager - 跨平台构建脚本
支持 Windows (PyInstaller), Linux, macOS
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path


def ensure_deps():
    """确保依赖已安装"""
    required = ["pyinstaller", "PyQt6", "requests"]
    for pkg in required:
        try:
            __import__(pkg.replace("-", "_").lower())
        except ImportError:
            print(f"安装 {pkg}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])


def write_spec_file():
    """生成 PyInstaller spec 文件"""
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-
import sys
import os
from pathlib import Path

block_cipher = None

project_dir = Path(__file__).parent.resolve()
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
        "json",
        "os",
        "subprocess",
        "threading",
        "pathlib",
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
'''
    spec_path = Path(__file__).parent / "llama_manager.spec"
    with open(spec_path, "w", encoding="utf-8") as f:
        f.write(spec_content)
    print(f"Spec 文件已生成: {spec_path}")
    return spec_path


def build():
    """执行构建"""
    print("=" * 50)
    print("  Llama.cpp Manager - 构建脚本")
    print("=" * 50)
    
    # 确保在项目根目录
    project_dir = Path(__file__).parent.resolve()
    os.chdir(project_dir)
    
    # 清理旧构建
    print("\n[1/4] 清理旧构建...")
    for d in ["build", "dist"]:
        if Path(d).exists():
            shutil.rmtree(d)
    
    # 确保依赖
    print("\n[2/4] 确保依赖...")
    ensure_deps()
    
    # 生成 spec
    print("\n[3/4] 生成 PyInstaller 配置...")
    write_spec_file()
    
    # 构建
    print("\n[4/4] 执行打包...")
    result = subprocess.run(
        [sys.executable, "-m", "PyInstaller", "llama_manager.spec", "--noconfirm"],
        cwd=project_dir
    )
    
    if result.returncode != 0:
        print("\n[错误] 打包失败!")
        sys.exit(1)
    
    # 整理输出
    output_dir = project_dir / "output" / "LlamaCppManager-win"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    src_dist = project_dir / "dist" / "LlamaCppManager"
    if src_dist.exists():
        for item in src_dist.iterdir():
            dest = output_dir / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)
    
    # 复制 README
    readme = project_dir / "README.md"
    if readme.exists():
        shutil.copy2(readme, output_dir)
    
    # 创建版本说明
    version_txt = output_dir / "版本说明.txt"
    with open(version_txt, "w", encoding="utf-8") as f:
        f.write("""Llama.cpp Manager for Windows
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

配置文件位置: %APPDATA%\\LlamaCppManager\\config.json
""")
    
    print("\n" + "=" * 50)
    print(f"  构建完成!")
    print(f"  输出目录: {output_dir}")
    print("=" * 50)


if __name__ == "__main__":
    build()
