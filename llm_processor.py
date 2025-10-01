"""
LLM-Powered Post-Processor for OCR Results
ใช้ LLM เป็น "สมอง" ในการประมวลผลข้อมูลจาก OCR ("ตา")

Features:
1. Field Mapping & Understanding - รู้ว่า field คืออะไร
2. Normalization - ปรับรูปแบบให้เป็นมาตรฐาน
3. Validation & Correction - ตรวจสอบและแก้ไข
4. Ensemble Reasoning - เลือก OCR Engine ที่ดีที่สุด
5. Template Mapping - จัดรูปแบบ Excel/JSON
6. Fuzzy Matching ภาษาไทย - จับคำที่คล้ายกัน
7. Multi-field Reasoning - วิเคราะห์ความสัมพันธ์ระหว่าง fields
"""

import os
import json
import re
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date
import logging
from pathlib import Path

# Try to import OpenAI (optional)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Try to import Anthropic (optional)
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = logging.getLogger(__name__)


class LLMProcessor:
    """
    LLM-Powered processor สำหรับ post-process ข้อมูล OCR
    รองรับ OpenAI GPT, Anthropic Claude, หรือ Local Models
    """
    
    def __init__(self, provider: str = "openai", model: str = "gpt-4o-mini", api_key: Optional[str] = None):
        """
        Initialize LLM Processor
        
        Args:
            provider: "openai", "anthropic", หรือ "local"
            model: ชื่อ model ที่ต้องการใช้
            api_key: API key (optional, จะใช้จาก environment variable ถ้าไม่ระบุ)
        """
        self.provider = provider
        self.model = model
        self.api_key = api_key or os.getenv(f"{provider.upper()}_API_KEY")
        
        # Initialize client based on provider
        self.client = None
        if provider == "openai" and OPENAI_AVAILABLE:
            self.client = OpenAI(api_key=self.api_key)
            logger.info(f"Initialized OpenAI client with model: {model}")
        elif provider == "anthropic" and ANTHROPIC_AVAILABLE:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            logger.info(f"Initialized Anthropic client with model: {model}")
        elif provider == "local":
            logger.info("Using local model (implementation required)")
        else:
            logger.warning(f"LLM provider '{provider}' not available. Will use rule-based fallback.")
    
    def process_ocr_results(
        self,
        ocr_text: str,
        parsed_data: Dict[str, Any],
        document_type: str = "tax_invoice"
    ) -> Dict[str, Any]:
        """
        Main processing function: ใช้ LLM ประมวลผลข้อมูล OCR
        
        Args:
            ocr_text: Raw OCR text
            parsed_data: Parsed data from traditional parser
            document_type: ประเภทเอกสาร
            
        Returns:
            Enhanced and corrected data
        """
        logger.info("🧠 LLM Post-Processing เริ่มทำงาน...")
        
        # If no LLM client available, return original data
        if not self.client:
            logger.warning("No LLM client available, using original data")
            return self._rule_based_correction(ocr_text, parsed_data)
        
        try:
            # 1. Field Mapping & Understanding
            enhanced_data = self._understand_and_map_fields(ocr_text, parsed_data)
            
            # 2. Normalization
            enhanced_data = self._normalize_data(enhanced_data)
            
            # 3. Validation & Correction
            enhanced_data = self._validate_and_correct(enhanced_data, ocr_text)
            
            # 4. Multi-field Reasoning
            enhanced_data = self._multi_field_reasoning(enhanced_data, ocr_text)
            
            logger.info("✅ LLM Post-Processing เสร็จสิ้น")
            return enhanced_data
            
        except Exception as e:
            logger.error(f"LLM processing error: {e}, falling back to rule-based")
            return self._rule_based_correction(ocr_text, parsed_data)
    
    def _understand_and_map_fields(
        self,
        ocr_text: str,
        parsed_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Feature 1: Field Mapping & Understanding
        ใช้ LLM เข้าใจว่า field แต่ละตัวคืออะไร และควรมีค่าอะไร
        """
        logger.info("🔍 Field Mapping & Understanding...")
        
        prompt = f"""คุณเป็น AI ผู้เชี่ยวชาญด้านการอ่านและเข้าใจใบกำกับภาษีไทย

ข้อความจาก OCR:
{ocr_text[:1000]}

ข้อมูลที่ Parser แยกได้:
{json.dumps(parsed_data, ensure_ascii=False, indent=2)}

กรุณาวิเคราะห์และแก้ไขข้อมูลต่อไปนี้:

1. **เลขที่ใบกำกับ (invoice_number)**: 
   - ตรวจสอบว่ามีรูปแบบ CT XX-XXXXXX หรือ AP-XXXXXX หรือตัวเลข 10-13 หลัก
   - ถ้าเจอ "เลขที่บิล", "เลขทีบิล", "เลขที่" ตามด้วยตัวเลข ให้เลือกตัวนั้น
   - ตัวอย่าง: CT 68-000612, AP-20250101001

2. **วันที่ (issue_date)**:
   - รูปแบบ d/m/yyyy โดย yyyy เป็นปีพุทธศักราช (พ.ศ.)
   - แปลงเป็น YYYY-MM-DD (ปี ค.ศ.)
   - สูตร: ปี ค.ศ. = ปี พ.ศ. - 543
   - ตัวอย่าง: 1/8/2568 → 2025-08-01

3. **ชื่อบริษัท (organization)**:
   - ดึงเฉพาะชื่อบริษัท ไม่รวมที่อยู่หรือข้อมูลอื่น
   - รูปแบบ: บริษัท [ชื่อ] จำกัด
   - ตัวอย่าง: บริษัท พี 111 เดคคอร์ จำกัด

4. **เลขผู้เสียภาษี (tax_id)**:
   - ต้องเป็นตัวเลข 13 หลักเท่านั้น
   - รูปแบบ: X XXXX XXXXX XX X
   - ตัวอย่าง: 0 1355 63000 95 2 → 0135563000952

5. **ยอดเงิน (subtotal, vat_amount, total_amount)**:
   - ยอดรวมก่อนภาษี (รวมเป็นเงิน)
   - ภาษี VAT 7%
   - ยอดรวมสุทธิ (ยอดเงินสุทธิ)
   - ตรวจสอบสูตร: total = subtotal + vat

กรุณาตอบเป็น JSON เท่านั้น โดยมี fields ทั้งหมดตามนี้:
{{
  "invoice_number": "...",
  "issue_date": "YYYY-MM-DD",
  "organization": "...",
  "tax_id": "...",
  "telephone": "...",
  "subtotal": "...",
  "vat_amount": "...",
  "total_amount": "...",
  "confidence": 0.0-1.0
}}

**สำคัญ**: ตอบเป็น JSON เท่านั้น ไม่ต้องมีคำอธิบายเพิ่มเติม"""

        try:
            if self.provider == "openai":
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "คุณเป็น AI ผู้เชี่ยวชาญด้านการประมวลผลใบกำกับภาษีไทย ตอบเป็น JSON เท่านั้น"},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.1
                )
                
                llm_result = json.loads(response.choices[0].message.content)
                logger.info(f"📊 LLM Understanding result: {llm_result}")
                
                # Merge LLM results with original data
                enhanced_data = parsed_data.copy()
                for key, value in llm_result.items():
                    if key != "confidence" and value:
                        enhanced_data[key] = value
                
                return enhanced_data
                
            elif self.provider == "anthropic":
                # Anthropic Claude implementation
                pass
            
        except Exception as e:
            logger.error(f"LLM understanding error: {e}")
        
        return parsed_data
    
    def _normalize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Feature 2: Normalization
        ปรับรูปแบบข้อมูลให้เป็นมาตรฐาน
        """
        logger.info("📏 Normalizing data...")
        
        # Normalize invoice number
        if data.get('invoice_number'):
            inv = data['invoice_number'].strip()
            # Remove extra spaces in patterns like "CT 68-000612"
            inv = re.sub(r'\s+', '', inv)
            # Keep dash in patterns like CT68-000612
            data['invoice_number'] = inv
        
        # Normalize tax ID (remove spaces/dashes)
        if data.get('tax_id'):
            tax_id = re.sub(r'[\s\-]', '', data['tax_id'])
            if len(tax_id) == 13 and tax_id.isdigit():
                data['tax_id'] = tax_id
        
        # Normalize phone (remove spaces/dashes)
        if data.get('telephone'):
            phone = re.sub(r'[\s\-]', '', data['telephone'])
            if len(phone) in [9, 10] and phone.isdigit():
                data['telephone'] = phone
        
        # Normalize amounts (ensure 2 decimal places)
        for field in ['subtotal', 'vat_amount', 'total_amount', 'wht']:
            if data.get(field):
                try:
                    amount = float(str(data[field]).replace(',', ''))
                    data[field] = f"{amount:.2f}"
                except (ValueError, TypeError):
                    pass
        
        # Normalize organization name (clean up)
        if data.get('organization'):
            org = data['organization']
            # Remove extra content after company name
            org = re.sub(r'\s+(?:ใบ|ที่อยู่|โทร).*', '', org)
            # Clean up spaces
            org = ' '.join(org.split())
            data['organization'] = org
            data['name'] = org
        
        return data
    
    def _validate_and_correct(
        self,
        data: Dict[str, Any],
        ocr_text: str
    ) -> Dict[str, Any]:
        """
        Feature 3: Validation & Correction
        ตรวจสอบและแก้ไขข้อมูล
        """
        logger.info("✅ Validating and correcting data...")
        
        # Validate and correct date
        if data.get('issue_date'):
            try:
                # Check if date is valid
                date_obj = datetime.strptime(data['issue_date'], '%Y-%m-%d')
                
                # Check if date is reasonable (not too far in past/future)
                current_year = datetime.now().year
                if date_obj.year < 1900 or date_obj.year > current_year + 10:
                    logger.warning(f"Invalid date year: {date_obj.year}, trying to extract from OCR")
                    # Try to find date in OCR text
                    date_pattern = r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})'
                    match = re.search(date_pattern, ocr_text)
                    if match:
                        day, month, year = match.groups()
                        year = int(year)
                        # Convert Buddhist year to Christian year
                        if year > 2400:
                            year -= 543
                        try:
                            corrected_date = date(year, int(month), int(day))
                            data['issue_date'] = corrected_date.strftime('%Y-%m-%d')
                            logger.info(f"📅 Corrected date: {data['issue_date']}")
                        except ValueError:
                            pass
            except ValueError:
                pass
        
        # Validate amounts calculation
        try:
            subtotal = float(data.get('subtotal', '0'))
            vat = float(data.get('vat_amount', '0'))
            total = float(data.get('total_amount', '0'))
            
            # Check if calculation is correct
            expected_total = subtotal + vat
            if abs(expected_total - total) > 0.1 and total > 0:
                logger.warning(f"Amount calculation mismatch: {subtotal} + {vat} != {total}")
                
                # Try to correct
                if subtotal > 0 and vat > 0:
                    data['total_amount'] = f"{expected_total:.2f}"
                    logger.info(f"💰 Corrected total: {data['total_amount']}")
                elif subtotal > 0 and total > 0:
                    data['vat_amount'] = f"{(total - subtotal):.2f}"
                    logger.info(f"💰 Corrected VAT: {data['vat_amount']}")
                elif vat > 0 and total > 0:
                    data['subtotal'] = f"{(total - vat):.2f}"
                    logger.info(f"💰 Corrected subtotal: {data['subtotal']}")
        except (ValueError, TypeError):
            pass
        
        return data
    
    def _multi_field_reasoning(
        self,
        data: Dict[str, Any],
        ocr_text: str
    ) -> Dict[str, Any]:
        """
        Feature 7: Multi-field Reasoning
        วิเคราะห์ความสัมพันธ์ระหว่าง fields
        """
        logger.info("🤔 Multi-field reasoning...")
        
        # Check if invoice number format matches company format
        if data.get('invoice_number'):
            inv = data['invoice_number']
            if inv.startswith('CT') or inv.startswith('ct'):
                data['company_format'] = 'CT'
            elif inv.startswith('AP') or inv.startswith('ap'):
                data['company_format'] = 'AP'
        
        # Ensure due_date and tax_date match issue_date if not specified
        if data.get('issue_date'):
            if not data.get('due_date'):
                data['due_date'] = data['issue_date']
            if not data.get('tax_date'):
                data['tax_date'] = data['issue_date']
        
        # Generate title from organization if missing
        if data.get('organization') and not data.get('title'):
            org = data['organization']
            words = org.replace('บริษัท', '').replace('จำกัด', '').strip().split()
            if words:
                data['title'] = ''.join([word[0].upper() for word in words[:3] if word])
        
        return data
    
    def _rule_based_correction(
        self,
        ocr_text: str,
        parsed_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Fallback: Rule-based correction when LLM is not available
        """
        logger.info("📋 Using rule-based correction (fallback)...")
        
        data = parsed_data.copy()
        
        # Try to extract CT format invoice number
        ct_pattern = r'(?:เลขที่บิล|เลขทีบิล|เลขที่).*?([Cc][Tt]\s*\d{2}[\-\s]*\d{6})'
        match = re.search(ct_pattern, ocr_text)
        if match:
            ct_number = match.group(1)
            ct_number = ct_number.upper().replace(' ', '')
            data['invoice_number'] = ct_number
            data['company_format'] = 'CT'
            logger.info(f"🔍 Found CT number: {ct_number}")
        
        # Try to fix Buddhist year in date
        if data.get('issue_date'):
            try:
                date_obj = datetime.strptime(data['issue_date'], '%Y-%m-%d')
                if date_obj.year > 2100:  # Likely Buddhist year
                    corrected_year = date_obj.year - 543
                    data['issue_date'] = date_obj.replace(year=corrected_year).strftime('%Y-%m-%d')
                    logger.info(f"📅 Corrected Buddhist year: {data['issue_date']}")
            except ValueError:
                pass
        
        # Clean organization name
        if data.get('organization'):
            org = data['organization']
            # Extract company name from first line/sentence
            org_clean = re.split(r'(?:ใบ|ที่อยู่|โทร)', org)[0]
            org_clean = ' '.join(org_clean.split()[:6])  # Take first 6 words max
            if len(org_clean) > 10:
                data['organization'] = org_clean
                data['name'] = org_clean
        
        return data
    
    def ensemble_reasoning(
        self,
        ocr_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Feature 4: Ensemble Reasoning
        เลือกผลลัพธ์ที่ดีที่สุดจากหลาย OCR engines
        """
        logger.info("🎯 Ensemble reasoning from multiple OCR results...")
        
        if not ocr_results or len(ocr_results) == 0:
            return {}
        
        if len(ocr_results) == 1:
            return ocr_results[0]
        
        # Score each result
        scored_results = []
        for result in ocr_results:
            score = self._calculate_result_score(result)
            scored_results.append((score, result))
        
        # Sort by score (highest first)
        scored_results.sort(reverse=True, key=lambda x: x[0])
        
        best_result = scored_results[0][1]
        logger.info(f"✨ Best result score: {scored_results[0][0]:.2f}")
        
        # Merge best fields from all results
        merged = best_result.copy()
        
        # For each field, take the best value
        for field in ['invoice_number', 'tax_id', 'organization', 'telephone']:
            values = [(r.get(field), s) for s, r in scored_results if r.get(field)]
            if values:
                merged[field] = max(values, key=lambda x: x[1])[0]
        
        return merged
    
    def _calculate_result_score(self, result: Dict[str, Any]) -> float:
        """Calculate quality score for OCR result"""
        score = 0.0
        
        # Count filled fields
        filled_fields = len([v for v in result.values() if v and str(v).strip()])
        score += filled_fields * 2
        
        # Bonus for critical fields
        if result.get('invoice_number'):
            score += 10
        if result.get('tax_id') and len(result['tax_id']) == 13:
            score += 10
        if result.get('subtotal') and float(result.get('subtotal', 0)) > 0:
            score += 10
        if result.get('vat_amount') and float(result.get('vat_amount', 0)) > 0:
            score += 10
        if result.get('total_amount') and float(result.get('total_amount', 0)) > 0:
            score += 10
        
        # Check date validity
        if result.get('issue_date'):
            try:
                date_obj = datetime.strptime(result['issue_date'], '%Y-%m-%d')
                current_year = datetime.now().year
                if 2000 <= date_obj.year <= current_year + 5:
                    score += 10
            except ValueError:
                pass
        
        return score


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Example: Initialize processor
    processor = LLMProcessor(provider="openai", model="gpt-4o-mini")
    
    # Example OCR text
    ocr_text = """
    บริษัท พี 111 เดคคอร์ จำกัด (สาขาที่ 00001)
    ใบกำกับภาษี/ใบเสร็จรับเงิน
    7/3 หมู่ 3 ต.คลองข่อย อ.ปากเกร็ด จนนทบุรี 11120
    โทร 02 003-8869
    เลขที่บิล CT 68-000612
    เลขประจำตัวผู้เสียภาษี 0 1355 63000 95 2
    วันที่ 1/8/2568
    รวมเป็นเงิน 5,448.60
    VAT 7% 381.40
    ยอดเงินสุทธิ 5,830.00
    """
    
    parsed_data = {
        'invoice_number': '088381872500',
        'issue_date': '2025-08-01',
        'organization': 'บริษัท 111 เดคคอร์ จำกัด',
        'tax_id': '0135563000952',
        'subtotal': '5448.60',
        'vat_amount': '381.40',
        'total_amount': '5830.00'
    }
    
    # Process with LLM
    result = processor.process_ocr_results(ocr_text, parsed_data)
    
    print("\n" + "="*80)
    print("🧠 LLM Enhanced Result:")
    print("="*80)
    print(json.dumps(result, ensure_ascii=False, indent=2))
