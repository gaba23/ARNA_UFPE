# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['executa.py'],
    pathex=[],
    binaries=[],
    datas=[
    ('api/static', 'api/static'),
    ('api/templates', 'api/templates'),
    ('api/resultadosCpm', 'api/resultadosCpm'),
    ('api/resultadosMontecarlo', 'api/resultadosMontecarlo'),
    ('api/resultadosPert', 'api/resultadosPert')
],
    hiddenimports=['uvicorn', 'fastapi'],
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
    name='executa',
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
