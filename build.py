#!/usr/bin/env python3
"""
Llama.cpp Manager - 跨平台构建脚本
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


def build():
    """执行构建"""
    print("=" * 50)
    print("  Llama.cpp Manager - 构建脚本")
    print("=" * 50)
    
    # 确保在项目根目录
    project_dir = Path(__file__).parent.resolve()
    os.chdir(project_dir)
    
    # 清理旧构建
    print("\n[1/5] 清理旧构建...")
    for d in ["build", "dist"]:
        if Path(d).exists():
            shutil.rmtree(d)
    
    # 确保依赖
    print("\n[2/5] 确保依赖...")
    ensure_deps()
    
    # 直接调用 pyinstaller，不依赖 spec 文件
    print("\n[3/5] 执行打包...")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name=LlamaCppManager",
        "--console",  # 先用控制台模式，方便看到错误
        "--onefile",
        "--noconfirm",
        "--distpath=dist",
        "--workpath=build",
        "--specpath=.",
        "--add-data=resources;resources",
        "--hidden-import=PyQt6.QtCore",
        "--hidden-import=PyQt6.QtGui",
        "--hidden-import=PyQt6.QtWidgets",
        "--hidden-import=requests",
        "--hidden-import=json",
        "--hidden-import=os",
        "--hidden-import=subprocess",
        "--hidden-import=threading",
        "--hidden-import=pathlib",
        "--collect-submodules=PyQt6",
        "--collect-submodules=PyQt6.Qt5",
        "src/main.py",
    ]
    
    result = subprocess.run(cmd, cwd=project_dir)
    
    if result.returncode != 0:
        print("\n[错误] 打包失败!")
        sys.exit(1)
    
    # 整理输出
    print("\n[4/5] 整理输出...")
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
    
    # 复制 README 和资源
    for f in ["README.md", "requirements.txt"]:
        src = project_dir / f
        if src.exists():
            shutil.copy2(src, output_dir)
    
    # 复制 resources
    resources_src = project_dir / "resources"
    resources_dst = output_dir / "resources"
    if resources_src.exists():
        shutil.copytree(resources_src, resources_dst, dirs_exist_ok=True)
    
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

快速开始:
1. 运行程序
2. 点击"设置" -> "下载 llama.cpp"
3. 选择 HuggingFace GGUF 模型 (如 Qwen3.5-9B-GGUF)
4. 点击"启动服务器"
5. 使用 http://localhost:8080 访问 API
""")
    
    print("\n[5/5] 完成!")
    print("\n" + "=" * 50)
    print(f"  构建完成!")
    print(f"  输出目录: {output_dir}")
    print(f"  可执行文件: {output_dir / 'LlamaCppManager.exe'}")
    print("=" * 50)


if __name__ == "__main__":
    build()
