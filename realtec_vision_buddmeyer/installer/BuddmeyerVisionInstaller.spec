# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Realtec_Vision_Buddmeyer\\realtec_vision_buddmeyer\\installer\\install.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Realtec_Vision_Buddmeyer\\realtec_vision_buddmeyer', 'realtec_vision_buddmeyer')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='BuddmeyerVisionInstaller',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
