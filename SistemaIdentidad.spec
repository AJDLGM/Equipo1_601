# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_submodules, collect_data_files

pil_imports = collect_submodules('PIL')
pil_datas   = collect_data_files('PIL')

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('assets/logo.png', 'assets'), *pil_datas],
    hiddenimports=[
        *pil_imports,
        'PIL', 'PIL.Image', 'PIL.ImageTk', 'PIL._imaging',
        'zoneinfo', 'tzdata',
        'requests', 'requests.adapters', 'requests.auth', 'requests.models',
        'urllib3', 'certifi', 'charset_normalizer', 'idna',
        'docx', 'docx.oxml', 'docx.oxml.ns', 'docx.parts', 'docx.shared',
        'docx.enum.text', 'docx.enum.table', 'lxml', 'lxml.etree',
        'pypdf', 'pypdf.generic', 'pypdf.filters',
        'reportlab', 'reportlab.lib', 'reportlab.lib.pagesizes',
        'reportlab.lib.units', 'reportlab.lib.colors', 'reportlab.lib.enums',
        'reportlab.lib.styles', 'reportlab.lib.utils',
        'reportlab.platypus', 'reportlab.platypus.paragraph',
        'reportlab.platypus.flowables', 'reportlab.platypus.doctemplate',
        'reportlab.platypus.tables', 'reportlab.pdfgen',
        'reportlab.pdfgen.canvas', 'reportlab.pdfbase',
        'reportlab.pdfbase.ttfonts', 'reportlab.pdfbase.pdfmetrics',
    ],
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
    [],
    exclude_binaries=True,
    name='SistemaIdentidad',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
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
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SistemaIdentidad',
)
