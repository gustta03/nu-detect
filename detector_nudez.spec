# -*- mode: python ; coding: utf-8 -*-
# Arquivo de especificação para PyInstaller
# Gera executável standalone para Linux e Windows

block_cipher = None

a = Analysis(
    ['gui/gui_main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Inclui modelos (se existirem localmente)
        # ('models', 'models'),
        # Inclui código fonte se necessário
        # ('src', 'src'),
    ],
    hiddenimports=[
        # Módulos do detector
        'detector_nudez_v2',
        'nudity_pipeline',
        'human_detector',
        'nudity_analyzer',
        'severity_classifier',
        'temporal_aggregator',
        'observability',
        # Dependências customtkinter
        'customtkinter',
        'PIL._tkinter_finder',
        # Dependências do detector
        'nudenet',
        'ultralytics',
        'tensorflow',
        'cv2',
        'numpy',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'pandas',
        'jupyter',
        'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='DetectorNudez',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compressão UPX (pode causar problemas com alguns antivírus)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # False = GUI mode (sem console)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Adicione caminho para .ico (Windows) ou .png (Linux) se tiver
)


