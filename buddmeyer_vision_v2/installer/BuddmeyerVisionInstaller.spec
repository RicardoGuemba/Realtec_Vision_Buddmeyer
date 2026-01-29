# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['C:\\Vision_Buddmeyer_PySide\\buddmeyer_vision_v2\\installer\\install.py'],
    pathex=[],
    binaries=[],
    datas=[('C:\\Vision_Buddmeyer_PySide\\buddmeyer_vision_v2', 'buddmeyer_vision_v2')],
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
