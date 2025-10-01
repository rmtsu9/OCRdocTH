"""
สคริปต์ทดสอบ OCR สำหรับเอกสารชัด
ใช้ทดสอบหลาย OCR engine พร้อมกัน
"""

from OCR import DocumentOCR
from pathlib import Path
import json

def test_ocr_engines(image_path):
    """ทดสอบ OCR หลาย engine"""
    
    if not Path(image_path).exists():
        print(f"❌ ไม่พบไฟล์: {image_path}")
        print("\n📝 กรุณาบันทึกรูปภาพใบกำกับภาษีลงใน:")
        print(f"   {Path(image_path).absolute()}")
        return
    
    print("=" * 80)
    print("🔍 ทดสอบ OCR หลาย Engine")
    print("=" * 80)
    
    ocr = DocumentOCR()
    engines = ['tesseract', 'easyocr']
    
    best_result = None
    best_score = 0
    
    for engine in engines:
        print(f"\n{'='*80}")
        print(f"🔧 Engine: {engine.upper()}")
        print(f"{'='*80}")
        
        try:
            # ทดสอบทั้ง enhancement on และ off
            for enhance in [True, False]:
                enhance_label = "เปิด Enhancement" if enhance else "ปิด Enhancement"
                print(f"\n📊 {enhance_label}")
                print("-" * 80)
                
                result = ocr.process_and_parse_invoice(
                    image_path,
                    engine=engine,
                    enhance_images=enhance
                )
                
                if result.get('success'):
                    parsed_data = result['parsed_data']
                    ocr_text = result['raw_ocr_text']
                    
                    # นับฟิลด์ที่มีข้อมูล
                    filled_fields = {k: v for k, v in parsed_data.items() 
                                   if v and str(v).strip() and str(v).strip() != '0.00'}
                    
                    score = len(filled_fields)
                    
                    print(f"✅ ประมวลผลสำเร็จ")
                    print(f"📝 OCR Text: {len(ocr_text)} ตัวอักษร")
                    print(f"📊 ฟิลด์ที่แยกได้: {score}/{len(parsed_data)}")
                    
                    # แสดงข้อมูลสำคัญ
                    important_fields = {
                        'invoice_number': 'เลขที่ใบกำกับ',
                        'tax_id': 'เลขผู้เสียภาษี',
                        'issue_date': 'วันที่',
                        'organization': 'ชื่อองค์กร',
                        'subtotal': 'ยอดรวมก่อนภาษี',
                        'vat_amount': 'ภาษี VAT',
                        'total_amount': 'ยอดรวมสุทธิ',
                        'telephone': 'เบอร์โทร'
                    }
                    
                    print("\n🔍 ข้อมูลสำคัญที่แยกได้:")
                    for field, label in important_fields.items():
                        value = filled_fields.get(field, 'ไม่พบ')
                        status = "✅" if field in filled_fields else "❌"
                        print(f"  {status} {label}: {value}")
                    
                    # เก็บผลลัพธ์ที่ดีที่สุด
                    if score > best_score:
                        best_score = score
                        best_result = {
                            'engine': engine,
                            'enhancement': enhance,
                            'result': result,
                            'score': score
                        }
                    
                    # แสดง raw OCR text บางส่วน
                    print("\n📄 OCR Text (100 ตัวอักษรแรก):")
                    print("-" * 80)
                    print(ocr_text[:200].replace('\n', ' '))
                    print("...")
                    
                else:
                    print(f"❌ ประมวลผลไม่สำเร็จ: {result.get('error', 'Unknown error')}")
                    
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # แสดงผลลัพธ์ที่ดีที่สุด
    if best_result:
        print("\n" + "=" * 80)
        print("🏆 ผลลัพธ์ที่ดีที่สุด")
        print("=" * 80)
        print(f"Engine: {best_result['engine'].upper()}")
        print(f"Enhancement: {'เปิด' if best_result['enhancement'] else 'ปิด'}")
        print(f"Score: {best_result['score']}/{len(best_result['result']['parsed_data'])} ฟิลด์")
        
        print("\n📋 ข้อมูลที่แยกได้ทั้งหมด:")
        print("-" * 80)
        parsed_data = best_result['result']['parsed_data']
        for key, value in parsed_data.items():
            if value and str(value).strip() and str(value).strip() != '0.00':
                print(f"  • {key}: {value}")
        
        # บันทึกผลลัพธ์
        output_file = Path('test_results.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(best_result['result'], f, ensure_ascii=False, indent=2, default=str)
        print(f"\n💾 บันทึกผลลัพธ์ที่: {output_file}")
        
    else:
        print("\n❌ ไม่สามารถประมวลผลได้")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    # ใช้รูปภาพที่ผู้ใช้บันทึก
    test_image = "input/tax_invoice_clear.jpg"
    
    # ถ้าไม่มี ให้ใช้รูปเดิม
    if not Path(test_image).exists():
        print("⚠️ ไม่พบไฟล์ tax_invoice_clear.jpg")
        print("🔄 ใช้ไฟล์ทดสอบเดิม...")
        test_image = "input/f6f1a183-5b0b-4e47-8265-f9b0aa1b55e9.jpg"
    
    test_ocr_engines(test_image)
