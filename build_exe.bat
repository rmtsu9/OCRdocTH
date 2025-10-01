@echo off
REM ========================================================================
REM  Build Script สำหรับ OCR Tax Invoice System
REM  สร้าง .exe พร้อม dependencies ทั้งหมด
REM ========================================================================

echo.
echo ╔══════════════════════════════════════════════════════════════════════════╗
echo ║               OCR Tax Invoice System - Build to EXE                      ║
echo ║                  Windows Batch Build Script                              ║
echo ╚══════════════════════════════════════════════════════════════════════════╝
echo.

REM ตรวจสอบ Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ไม่พบ Python! กรุณาติดตั้ง Python ก่อน
    pause
    exit /b 1
)

echo ✅ พบ Python
python --version

REM ตรวจสอบว่าอยู่ในโฟลเดอร์ที่ถูกต้อง
if not exist "desktop_gui.py" (
    echo ❌ ไม่พบ desktop_gui.py
    echo 💡 กรุณารันสคริปต์นี้ในโฟลเดอร์ project
    pause
    exit /b 1
)

echo ✅ พบไฟล์หลัก desktop_gui.py

REM ติดตั้ง dependencies
echo.
echo 📦 กำลังติดตั้ง dependencies...
echo ────────────────────────────────────────────────────────────────────────
python -m pip install --upgrade pip
python -m pip install pyinstaller
python -m pip install -r requirements.txt

if errorlevel 1 (
    echo ❌ ติดตั้ง dependencies ล้มเหลว
    pause
    exit /b 1
)

echo ✅ ติดตั้ง dependencies สำเร็จ

REM รัน build script
echo.
echo 🔨 กำลัง Build...
echo ────────────────────────────────────────────────────────────────────────
python build_exe.py

if errorlevel 1 (
    echo.
    echo ❌ Build ล้มเหลว
    pause
    exit /b 1
)

echo.
echo ════════════════════════════════════════════════════════════════════════
echo  🎉 Build สำเร็จ!
echo ════════════════════════════════════════════════════════════════════════
echo.
echo 📁 โปรแกรมอยู่ที่: dist\OCR_TaxInvoice\OCR_TaxInvoice.exe
echo.
echo 💡 ขั้นตอนถัดไป:
echo    1. เปิดโฟลเดอร์: dist\OCR_TaxInvoice
echo    2. คัดลอกทั้งโฟลเดอร์ไปใช้งาน
echo    3. ดับเบิลคลิก OCR_TaxInvoice.exe
echo    4. Login: admin / pass
echo.
echo ════════════════════════════════════════════════════════════════════════

REM เปิดโฟลเดอร์ผลลัพธ์
if exist "dist\OCR_TaxInvoice" (
    echo.
    set /p open="เปิดโฟลเดอร์ผลลัพธ์เลยไหม? (Y/N): "
    if /i "%open%"=="Y" (
        explorer dist\OCR_TaxInvoice
    )
)

pause
