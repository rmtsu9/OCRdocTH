"""
ทดสอบ LLM-Enhanced OCR กับรูปภาพใบกำกับภาษี
เปรียบเทียบผลลัพธ์ระหว่าง:
1. OCR + Rule-based Parser (แบบเดิม)
2. OCR + LLM Post-Processing (แบบใหม่)
"""

import sys
import json
from pathlib import Path
from OCR import DocumentOCR

def test_llm_enhanced_ocr():
    """ทดสอบ LLM-Enhanced OCR"""
    
    print("="*80)
    print("🧪 ทดสอบ LLM-Enhanced OCR System")
    print("="*80)
    
    # ไฟล์รูปภาพทดสอบ
    test_image = Path("input/clear_invoice_new.jpg")
    
    if not test_image.exists():
        print(f"⚠️ ไม่พบไฟล์: {test_image}")
        print("🔄 ใช้ไฟล์ทดสอบเดิม...")
        test_image = Path("input/f6f1a183-5b0b-4e47-8265-f9b0aa1b55e9.jpg")
    
    if not test_image.exists():
        print(f"❌ ไม่พบไฟล์ทดสอบ")
        return
    
    print(f"📄 Testing with: {test_image.name}\n")
    
    # ===============================================================
    # TEST 1: แบบเดิม (ไม่ใช้ LLM)
    # ===============================================================
    print("\n" + "="*80)
    print("📋 TEST 1: OCR + Rule-based Parser (ไม่ใช้ LLM)")
    print("="*80)
    
    ocr_system = DocumentOCR(use_llm=False)
    
    print("\n🔄 กำลังประมวลผล...")
    result_no_llm = ocr_system.process_and_parse_invoice(
        file_path=str(test_image),
        engine='easyocr',
        enhance_images=False
    )
    
    print("\n✅ ผลลัพธ์ (ไม่ใช้ LLM):")
    print("-" * 80)
    
    parsed = result_no_llm.get('parsed_data', {})
    print(f"  📋 เลขที่ใบกำกับ: {parsed.get('invoice_number', 'ไม่พบ')}")
    print(f"  📅 วันที่: {parsed.get('issue_date', 'ไม่พบ')}")
    print(f"  🏢 ชื่อบริษัท: {parsed.get('organization', 'ไม่พบ')[:60]}...")
    print(f"  🔢 เลขผู้เสียภาษี: {parsed.get('tax_id', 'ไม่พบ')}")
    print(f"  📞 โทรศัพท์: {parsed.get('telephone', 'ไม่พบ')}")
    print(f"  💰 ยอดรวมก่อนภาษี: {parsed.get('subtotal', 'ไม่พบ')}")
    print(f"  💵 ภาษี VAT: {parsed.get('vat_amount', 'ไม่พบ')}")
    print(f"  💳 ยอดรวมสุทธิ: {parsed.get('total_amount', 'ไม่พบ')}")
    
    filled_count = len([v for v in parsed.values() if v and str(v).strip()])
    print(f"\n  📊 ฟิลด์ที่มีข้อมูล: {filled_count}/27")
    
    # ===============================================================
    # TEST 2: แบบใหม่ (ใช้ LLM)
    # ===============================================================
    print("\n" + "="*80)
    print("🧠 TEST 2: OCR + LLM Post-Processing (ใช้ LLM)")
    print("="*80)
    
    # ตรวจสอบ API Key
    import os
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("\n⚠️ ไม่พบ OPENAI_API_KEY")
        print("💡 วิธีตั้งค่า API Key:")
        print("   Windows PowerShell:")
        print('   $env:OPENAI_API_KEY="sk-..."')
        print("\n📋 กำลังใช้ Rule-based Fallback...")
        
        # ใช้ LLM แบบ fallback (rule-based)
        ocr_system_llm = DocumentOCR(use_llm=True, llm_provider="openai")
    else:
        print("✅ พบ OPENAI_API_KEY")
        print("🧠 กำลังเริ่ม LLM Processor...\n")
        ocr_system_llm = DocumentOCR(
            use_llm=True,
            llm_provider="openai",
            llm_model="gpt-4o-mini"
        )
    
    print("\n🔄 กำลังประมวลผล (พร้อม LLM)...")
    result_with_llm = ocr_system_llm.process_and_parse_invoice(
        file_path=str(test_image),
        engine='easyocr',
        enhance_images=False
    )
    
    print("\n✨ ผลลัพธ์ (ใช้ LLM):")
    print("-" * 80)
    
    parsed_llm = result_with_llm.get('parsed_data', {})
    print(f"  📋 เลขที่ใบกำกับ: {parsed_llm.get('invoice_number', 'ไม่พบ')}")
    print(f"  📅 วันที่: {parsed_llm.get('issue_date', 'ไม่พบ')}")
    print(f"  🏢 ชื่อบริษัท: {parsed_llm.get('organization', 'ไม่พบ')[:60]}...")
    print(f"  🔢 เลขผู้เสียภาษี: {parsed_llm.get('tax_id', 'ไม่พบ')}")
    print(f"  📞 โทรศัพท์: {parsed_llm.get('telephone', 'ไม่พบ')}")
    print(f"  💰 ยอดรวมก่อนภาษี: {parsed_llm.get('subtotal', 'ไม่พบ')}")
    print(f"  💵 ภาษี VAT: {parsed_llm.get('vat_amount', 'ไม่พบ')}")
    print(f"  💳 ยอดรวมสุทธิ: {parsed_llm.get('total_amount', 'ไม่พบ')}")
    
    filled_count_llm = len([v for v in parsed_llm.values() if v and str(v).strip()])
    print(f"\n  📊 ฟิลด์ที่มีข้อมูล: {filled_count_llm}/27")
    
    # ===============================================================
    # COMPARISON
    # ===============================================================
    print("\n" + "="*80)
    print("📊 เปรียบเทียบผลลัพธ์")
    print("="*80)
    
    critical_fields = [
        ('invoice_number', 'เลขที่ใบกำกับ'),
        ('issue_date', 'วันที่'),
        ('organization', 'ชื่อบริษัท'),
        ('tax_id', 'เลขผู้เสียภาษี'),
        ('subtotal', 'ยอดรวมก่อนภาษี'),
        ('vat_amount', 'ภาษี VAT'),
        ('total_amount', 'ยอดรวมสุทธิ')
    ]
    
    improvements = []
    for field, label in critical_fields:
        old_value = parsed.get(field, '')
        new_value = parsed_llm.get(field, '')
        
        # Check if improved
        if not old_value and new_value:
            improvements.append(f"✅ {label}: เพิ่มข้อมูล")
        elif old_value != new_value and new_value:
            # Check if it's actually better
            if field == 'invoice_number':
                if 'CT' in new_value or 'ct' in new_value:
                    improvements.append(f"✨ {label}: {old_value} → {new_value}")
            elif field == 'issue_date':
                # Check year is reasonable
                if '2025' in new_value or '2024' in new_value:
                    improvements.append(f"✨ {label}: {old_value} → {new_value}")
            elif field == 'organization':
                # Check if shorter and cleaner
                if len(new_value) < len(old_value) and 'บริษัท' in new_value:
                    improvements.append(f"✨ {label}: ทำความสะอาด")
            else:
                if new_value != old_value:
                    improvements.append(f"✨ {label}: {old_value} → {new_value}")
    
    if improvements:
        print("\n🎯 การปรับปรุงที่สำคัญ:")
        for imp in improvements:
            print(f"  {imp}")
    else:
        print("\n📋 ไม่มีการเปลี่ยนแปลงใหญ่")
    
    print(f"\n📈 คะแนนการเติมข้อมูล:")
    print(f"  ไม่ใช้ LLM: {filled_count}/27 ({filled_count/27*100:.1f}%)")
    print(f"  ใช้ LLM:     {filled_count_llm}/27 ({filled_count_llm/27*100:.1f}%)")
    
    improvement_rate = ((filled_count_llm - filled_count) / 27 * 100)
    if improvement_rate > 0:
        print(f"  ⬆️ ปรับปรุง: +{improvement_rate:.1f}%")
    elif improvement_rate < 0:
        print(f"  ⬇️ ลดลง: {improvement_rate:.1f}%")
    else:
        print(f"  ➡️ เท่าเดิม")
    
    # บันทึกผลลัพธ์
    comparison_result = {
        'test_image': str(test_image),
        'without_llm': {
            'filled_fields': filled_count,
            'data': parsed
        },
        'with_llm': {
            'filled_fields': filled_count_llm,
            'data': parsed_llm
        },
        'improvements': improvements,
        'improvement_rate': improvement_rate
    }
    
    output_file = Path("test_llm_comparison.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(comparison_result, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 บันทึกผลการเปรียบเทียบ: {output_file}")
    print("\n" + "="*80)
    

if __name__ == "__main__":
    try:
        test_llm_enhanced_ocr()
    except KeyboardInterrupt:
        print("\n\n⚠️ ยกเลิกการทดสอบ")
    except Exception as e:
        print(f"\n\n❌ เกิดข้อผิดพลาด: {e}")
        import traceback
        traceback.print_exc()
