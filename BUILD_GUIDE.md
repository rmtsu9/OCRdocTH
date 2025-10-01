# OCR Tax Invoice System - คู่มือการ Build เป็น .exe

## 📋 ข้อกำหนดของระบบ

- Windows 10/11 (64-bit)
- Python 3.9 หรือสูงกว่า
- RAM อย่างน้อย 8GB (สำหรับ build)
- พื้นที่ว่างอย่างน้อย 5GB

## 🚀 วิธี Build เป็น .exe

### วิธีที่ 1: ใช้ Batch File (แนะนำ - ง่ายที่สุด)

```batch
# ดับเบิลคลิก build_exe.bat
```

### วิธีที่ 2: ใช้ Python Script

```bash
# 1. ติดตั้ง PyInstaller
pip install pyinstaller

# 2. รัน build script
python build_exe.py
```

### วิธีที่ 3: Manual (สำหรับผู้เชี่ยวชาญ)

```bash
# 1. สร้าง .spec file
pyi-makespec --onedir --windowed --name="OCR_TaxInvoice" desktop_gui.py

# 2. แก้ไข .spec file (เพิ่ม data files และ hidden imports)

# 3. Build
pyinstaller OCR_TaxInvoice.spec --clean
```

## 📦 โครงสร้างไฟล์ที่ได้

```
dist/OCR_TaxInvoice/
├── OCR_TaxInvoice.exe          # โปรแกรมหลัก (ให้ลูกค้าดับเบิลคลิก)
├── README_คู่มือการใช้งาน.txt  # คู่มือสำหรับลูกค้า
├── _internal/                  # Dependencies (อย่าลบ!)
├── Lib/                        # Tesseract, Poppler
│   ├── Tesseract-OCR/
│   └── poppler-25.07.0/
├── Model/                      # AI Models
├── input/                      # วางไฟล์ที่ต้องการ OCR
├── outputs/                    # ผลลัพธ์ JSON, TXT
├── Export/                     # ผลลัพธ์ Excel
│   └── ref/
└── credentials.json            # Config file
```

## 🔧 การแก้ไขปัญหาที่พบบ่อย

### ปัญหา: Build ล้มเหลว

```bash
# แก้ไข: อัพเดต PyInstaller
pip install --upgrade pyinstaller

# หรือใช้ version เฉพาะ
pip install pyinstaller==6.3.0
```

### ปัญหา: ไม่พบ Tesseract หรือ Poppler

ตรวจสอบว่ามี folders เหล่านี้:
- `Lib/Tesseract-OCR/`
- `Lib/poppler-25.07.0/`

### ปัญหา: .exe ขนาดใหญ่เกินไป (>1GB)

ปกติ: ขนาดประมาณ 1.5-2GB เนื่องจากรวม:
- Tesseract OCR (200MB)
- Poppler (100MB)
- EasyOCR Models (500MB)
- Python Dependencies (500MB)

ถ้าต้องการลดขนาด:
```python
# แก้ไข build_exe.py - ลบ PaddleOCR
hidden_imports = [
    # 'paddleocr',  # ←── comment ออก
]
```

### ปัญหา: Antivirus บล็อค .exe

เพิ่ม exception ใน Windows Defender:
1. เปิด Windows Security
2. Virus & threat protection
3. Manage settings
4. Add exclusion
5. เลือกโฟลเดอร์ `dist/OCR_TaxInvoice`

## 📝 Customization

### เปลี่ยน Icon

```bash
# 1. เตรียมไฟล์ icon.ico (256x256)
# 2. วางไฟล์ในโฟลเดอร์ project
# 3. Build ใหม่
```

### เปลี่ยนชื่อ Program

แก้ไขใน `build_exe.py`:
```python
name='OCR_TaxInvoice',  # ←── เปลี่ยนชื่อตรงนี้
```

### เพิ่ม Data Files

แก้ไขใน `build_exe.py`:
```python
added_files = [
    ('your_folder', 'your_folder'),  # ←── เพิ่มตรงนี้
]
```

## 🚢 การ Deploy ให้ลูกค้า

### แบบ Portable (แนะนำ)

1. ZIP ทั้งโฟลเดอร์ `dist/OCR_TaxInvoice`
2. ส่งให้ลูกค้า
3. ลูกค้า Extract แล้วดับเบิลคลิก `OCR_TaxInvoice.exe`

### แบบ Installer (ขั้นสูง)

ใช้ Inno Setup สร้าง installer:
```
# 1. ดาวน์โหลด Inno Setup
https://jrsoftware.org/isinfo.php

# 2. สร้าง script.iss
# 3. Compile เป็น setup.exe
```

## 🔐 ความปลอดภัย

### เข้ารหัส Python Code

```bash
# ใช้ PyInstaller กับ key
pyinstaller --key="your-secret-key" OCR_TaxInvoice.spec
```

### ซ่อน Console Window

```python
# ใน .spec file
console=False,  # ←── ตั้งเป็น False
```

## 📊 ขนาดไฟล์โดยประมาณ

| Component | ขนาด |
|-----------|------|
| Python Runtime | 50 MB |
| Tesseract OCR | 200 MB |
| Poppler | 100 MB |
| EasyOCR | 500 MB |
| Dependencies | 300 MB |
| **รวม** | **~1.5 GB** |

## ⏱️ เวลาที่ใช้ Build

- เครื่องปกติ: 5-10 นาที
- เครื่อง SSD เร็ว: 3-5 นาที
- เครื่อง HDD ช้า: 10-20 นาที

## 🧪 การทดสอบ

```bash
# ทดสอบ .exe ที่ build แล้ว
cd dist/OCR_TaxInvoice
OCR_TaxInvoice.exe
```

### Checklist
- [ ] Login ได้ (admin/pass)
- [ ] เลือกไฟล์ได้
- [ ] OCR ทำงาน
- [ ] Export Excel ได้
- [ ] ไม่มี error pop-up

## 📞 ช่วยเหลือเพิ่มเติม

### Build ไม่สำเร็จ
```bash
# Clean ทุกอย่างแล้วลองใหม่
rmdir /s /q build dist
del *.spec
python build_exe.py
```

### หาข้อมูลเพิ่มเติม
- PyInstaller Docs: https://pyinstaller.org/
- GitHub Issues: https://github.com/rmtsu9/OCR-DocTH/issues

---

**อัพเดตล่าสุด:** October 2025  
**Version:** 1.0.0
