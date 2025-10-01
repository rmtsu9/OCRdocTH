# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

block_cipher = None

# เพิ่ม data files ที่ต้องรวม
added_files = [
    ('Lib/Tesseract-OCR', 'Lib/Tesseract-OCR'),
    ('Lib/poppler-25.07.0', 'Lib/poppler-25.07.0'),
    ('Model', 'Model'),
    ('credentials.json', '.'),
    ('Export/ref', 'Export/ref'),
]

# Hidden imports - modules ที่ PyInstaller อาจพลาด
hidden_imports = [
    'pytesseract',
    'easyocr',
    'paddleocr',
    'cv2',
    'PIL',
    'openpyxl',
    'pandas',
    'tkinter',
    'tkinter.ttk',
    'tkinter.messagebox',
    'tkinter.filedialog',
    'pdf2image',
    'numpy',
    'torch',
    'torchvision',
    'openai',
    'anthropic',
]

a = Analysis(
    ['desktop_gui.py'],
    pathex=[],
    binaries=[],
    datas=added_files,
    hiddenimports=hidden_imports,
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
    name='OCR_TaxInvoice',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # ไม่แสดง console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if Path('icon.ico').exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='OCR_TaxInvoice',
)
