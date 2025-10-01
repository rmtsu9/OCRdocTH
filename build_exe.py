"""
Build Script สำหรับสร้าง .exe จาก OCR Tax Invoice System
ใช้ PyInstaller แปลง Python + GUI เป็น .exe standalone

Features:
- รวม Tesseract OCR, Poppler, และ Models
- รวม dependencies ทั้งหมด
- รวม icon และ resources
- สร้าง installer พร้อมใช้งาน
"""

import os
import sys
import shutil
from pathlib import Path
import subprocess

def check_pyinstaller():
    """ตรวจสอบว่ามี PyInstaller หรือไม่"""
    try:
        import PyInstaller
        print("✅ PyInstaller พร้อมใช้งาน")
        return True
    except ImportError:
        print("❌ ไม่พบ PyInstaller")
        print("💡 กำลังติดตั้ง PyInstaller...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
        print("✅ ติดตั้ง PyInstaller สำเร็จ")
        return True

def create_spec_file():
    """สร้าง .spec file สำหรับ PyInstaller"""
    
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

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
"""
    
    spec_file = Path('OCR_TaxInvoice.spec')
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print(f"✅ สร้าง {spec_file} สำเร็จ")
    return spec_file

def build_exe():
    """Build .exe ด้วย PyInstaller"""
    
    print("\n" + "="*80)
    print("🔨 กำลัง Build OCR Tax Invoice System เป็น .exe")
    print("="*80 + "\n")
    
    # 1. ตรวจสอบ PyInstaller
    if not check_pyinstaller():
        print("❌ ไม่สามารถติดตั้ง PyInstaller ได้")
        return False
    
    # 2. ตรวจสอบไฟล์หลัก
    if not Path('desktop_gui.py').exists():
        print("❌ ไม่พบไฟล์ desktop_gui.py")
        return False
    
    print("✅ พบไฟล์หลัก desktop_gui.py")
    
    # 3. สร้าง .spec file
    spec_file = create_spec_file()
    
    # 4. ทำความสะอาด build folders เก่า
    for folder in ['build', 'dist']:
        if Path(folder).exists():
            print(f"🧹 ลบ folder {folder} เก่า...")
            shutil.rmtree(folder)
    
    # 5. Build ด้วย PyInstaller
    print("\n🔨 กำลัง Build... (อาจใช้เวลา 5-10 นาที)")
    print("=" * 80)
    
    # ใช้ python -m PyInstaller แทน pyinstaller command โดยตรง
    cmd = [
        sys.executable,
        '-m',
        'PyInstaller',
        str(spec_file),
        '--clean',  # Clean cache
        '--noconfirm',  # Replace output without asking
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print("\n" + "=" * 80)
        print("✅ Build สำเร็จ!")
        print("=" * 80)
        return True
        
    except subprocess.CalledProcessError as e:
        print("\n" + "=" * 80)
        print("❌ Build ล้มเหลว")
        print(f"Error: {e}")
        print("=" * 80)
        return False

def create_portable_package():
    """สร้าง package พร้อมใช้งาน"""
    
    dist_folder = Path('dist/OCR_TaxInvoice')
    
    if not dist_folder.exists():
        print("❌ ไม่พบ dist folder")
        return False
    
    print("\n📦 กำลังสร้าง Portable Package...")
    
    # สร้าง folders ที่จำเป็น
    folders_to_create = [
        'input',
        'outputs',
        'Export',
        'tmp',
    ]
    
    for folder in folders_to_create:
        target = dist_folder / folder
        target.mkdir(exist_ok=True)
        print(f"  ✅ สร้าง folder: {folder}")
    
    # คัดลอกไฟล์ตัวอย่าง
    ref_folder = Path('Export/ref')
    if ref_folder.exists():
        target_ref = dist_folder / 'Export' / 'ref'
        target_ref.mkdir(exist_ok=True)
        for file in ref_folder.glob('*'):
            if file.is_file():
                shutil.copy2(file, target_ref)
        print(f"  ✅ คัดลอก reference files")
    
    # คัดลอก README สำหรับลูกค้า
    customer_readme = Path('README_สำหรับลูกค้า.md')
    if customer_readme.exists():
        shutil.copy2(customer_readme, dist_folder)
        print(f"  ✅ คัดลอก README สำหรับลูกค้า")
    
    # สร้าง README สำหรับลูกค้า
    create_user_readme(dist_folder)
    
    print("\n✨ Portable Package พร้อมใช้งาน!")
    print(f"📁 ตำแหน่ง: {dist_folder.absolute()}")
    
    return True

def create_user_readme(dist_folder: Path):
    """สร้าง README สำหรับผู้ใช้งาน"""
    
    readme_content = """
╔══════════════════════════════════════════════════════════════════════════╗
║                  OCR Tax Invoice System - คู่มือการใช้งาน                 ║
╚══════════════════════════════════════════════════════════════════════════╝

📋 คำอธิบาย
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
โปรแกรม OCR Tax Invoice System เป็นระบบอ่านและแยกข้อมูลจากใบกำกับภาษีไทย
อัตโนมัติ รองรับทั้งไฟล์ PDF และรูปภาพ


🚀 วิธีเริ่มใช้งาน
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. เปิดโปรแกรม
   ───────────────────────────────────────────────────────────────────────
   • ดับเบิลคลิก OCR_TaxInvoice.exe
   • หน้าต่าง Login จะเปิดขึ้น

2. Login เข้าระบบ
   ───────────────────────────────────────────────────────────────────────
   Username: admin
   Password: pass

3. เลือกไฟล์ที่ต้องการประมวลผล
   ───────────────────────────────────────────────────────────────────────
   • คลิกปุ่ม "เลือกไฟล์"
   • รองรับ: PDF, JPG, PNG, JPEG

4. ตั้งค่า OCR Engine (ถ้าต้องการ)
   ───────────────────────────────────────────────────────────────────────
   • Auto: ระบบเลือกเอง (แนะนำ)
   • Tesseract: เร็ว แต่อาจไม่แม่นมาก
   • EasyOCR: แม่นยำสูง (แนะนำ)

5. ตั้งค่า TRCloud Format (ถ้าต้องการ)
   ───────────────────────────────────────────────────────────────────────
   • เลือกรูปแบบเลขที่รันอัตโนมัติ
   • ตัวอย่าง: YYMMx = 250100001 (ปี + เดือน + เลขรัน)

6. เริ่มประมวลผล
   ───────────────────────────────────────────────────────────────────────
   • คลิกปุ่ม "เริ่มประมวลผล"
   • รอสักครู่ (ประมาณ 10-30 วินาที)
   • ผลลัพธ์จะแสดงในแท็บ Structured Data


📂 โครงสร้าง Folders
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

input/          ใส่ไฟล์ที่ต้องการประมวลผล (PDF/Image)
outputs/        ผลลัพธ์ OCR (JSON, TXT)
Export/         ไฟล์ Excel ที่ส่งออก
tmp/            ไฟล์ชั่วคราว (ลบได้)
Lib/            Libraries ที่จำเป็น (อย่าลบ!)
Model/          AI Models (อย่าลบ!)


📊 ไฟล์ผลลัพธ์
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1. JSON File (outputs/)
   ───────────────────────────────────────────────────────────────────────
   • ข้อมูล structured สำหรับ API
   • รูปแบบ: invoice_parsed_20251001_120000.json

2. TXT File (outputs/)
   ───────────────────────────────────────────────────────────────────────
   • ข้อความที่อ่านได้จาก OCR
   • รูปแบบ: invoice_parsed_20251001_120000.txt

3. Excel File (Export/)
   ───────────────────────────────────────────────────────────────────────
   • พร้อมนำเข้าระบบบัญชี
   • 3 Sheets: Tax Invoice Data, Processing Summary, Raw OCR Text
   • รูปแบบ: invoice_tax_invoice_20251001_120000.xlsx


🔧 การตั้งค่าขั้นสูง
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

เปิดใช้ LLM (ตัวช่วยปรับปรุงความแม่นยำ)
───────────────────────────────────────────────────────────────────────
1. สร้างไฟล์ .env ในโฟลเดอร์โปรแกรม
2. เพิ่มบรรทัด: OPENAI_API_KEY=sk-your-key-here
3. Restart โปรแกรม


⚠️ ข้อควรระวัง
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• อย่าลบ folder Lib/ และ Model/
• อย่าแก้ไขไฟล์ credentials.json
• ควรมี RAM อย่างน้อย 4GB
• ควรมีพื้นที่ว่าง 2GB สำหรับไฟล์ชั่วคราว


❓ แก้ไขปัญหา
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ปัญหา: โปรแกรมเปิดไม่ได้
  → ลอง Run as Administrator
  → ตรวจสอบ Windows Defender / Antivirus

ปัญหา: OCR ช้า
  → ลดขนาดรูปภาพก่อนประมวลผล
  → ปิด Enhancement (ถ้าไม่จำเป็น)

ปัญหา: OCR ไม่แม่นยำ
  → ลองเปลี่ยน OCR Engine
  → ตรวจสอบคุณภาพรูปภาพ (ควรชัด, ความละเอียดสูง)
  → เปิดใช้ LLM (ถ้ามี API Key)


📞 ติดต่อสอบถาม
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

GitHub: https://github.com/rmtsu9/OCR-DocTH
Version: 1.0.0
Build Date: October 2025


═══════════════════════════════════════════════════════════════════════════
                        ขอบคุณที่ใช้งาน! 🙏
═══════════════════════════════════════════════════════════════════════════
"""
    
    readme_file = dist_folder / 'README_คู่มือการใช้งาน.txt'
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"  ✅ สร้าง README สำหรับผู้ใช้งาน")

def main():
    """Main build process"""
    
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║               OCR Tax Invoice System - Build to EXE                      ║
║                     PyInstaller Build Script                             ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    # ตรวจสอบว่าอยู่ใน project folder
    if not Path('desktop_gui.py').exists():
        print("❌ กรุณารันสคริปต์นี้ในโฟลเดอร์ project")
        return
    
    # Build
    if build_exe():
        # สร้าง portable package
        if create_portable_package():
            print("\n" + "="*80)
            print("🎉 สำเร็จ! โปรแกรม .exe พร้อมใช้งาน")
            print("="*80)
            print("\n📁 ไฟล์โปรแกรม:")
            print("   dist/OCR_TaxInvoice/OCR_TaxInvoice.exe")
            print("\n📝 คู่มือการใช้งาน:")
            print("   dist/OCR_TaxInvoice/README_คู่มือการใช้งาน.txt")
            print("   dist/OCR_TaxInvoice/README_สำหรับลูกค้า.md")
            print("\n💡 วิธีใช้:")
            print("   1. คัดลอกทั้งโฟลเดอร์ dist/OCR_TaxInvoice ไปที่เครื่องลูกค้า")
            print("   2. ดับเบิลคลิก OCR_TaxInvoice.exe")
            print("   3. Login: admin / pass")
            print("\n" + "="*80)
    else:
        print("\n❌ Build ล้มเหลว")
        print("\n💡 แนะนำ:")
        print("   1. ตรวจสอบว่าติดตั้ง dependencies ครบ (pip install -r requirements.txt)")
        print("   2. ลองรัน: pip install pyinstaller --upgrade")
        print("   3. ตรวจสอบ error message ด้านบน")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ ยกเลิกการ build")
    except Exception as e:
        print(f"\n\n❌ เกิดข้อผิดพลาด: {e}")
        import traceback
        traceback.print_exc()
