# -*- mode: python ; coding: utf-8 -*-
import sys
import os

block_cipher = None

# 获取项目根目录 (兼容 PyInstaller)
if getattr(sys, 'frozen', False):
    # 打包后
    bundle_dir = sys._MEIPASS
    project_dir = os.path.dirname(sys.executable)
else:
    # 开发时
    project_dir = os.path.dirname(os.path.abspath(__file__))

src_main = os.path.join(project_dir, 'src', 'main.py')
resources_dir = os.path.join(project_dir, 'resources')

hiddenimports = [
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'requests',
    'json',
    'os',
    'subprocess',
    'threading',
    'pathlib',
]

a = Analysis(
    [src_main],
    pathex=[os.path.join(project_dir, 'src')],
    binaries=[],
    datas=[
        (resources_dir, 'resources'),
    ],
    hiddenimports=hiddenimports,
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
