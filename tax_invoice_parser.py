import re
import json
from datetime import datetime, date
from typing import Dict, Any, Optional, List, Union
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class ThaiTaxInvoiceParser:
    """
    Parser สำหรับแยกข้อมูลจากใบภาษีไทยที่ได้จาก OCR
    แปลงข้อความจาก OCR เป็น structured data
    """
    
    def __init__(self):
        """Initialize the parser with Thai patterns"""
        self.thai_months = {
            'มกราคม': '01', 'กุมภาพันธ์': '02', 'มีนาคม': '03', 'เมษายน': '04',
            'พฤษภาคม': '05', 'มิถุนายน': '06', 'กรกฎาคม': '07', 'สิงหาคม': '08',
            'กันยายน': '09', 'ตุลาคม': '10', 'พฤศจิกายน': '11', 'ธันวาคม': '12',
            'ม.ค.': '01', 'ก.พ.': '02', 'มี.ค.': '03', 'เม.ย.': '04',
            'พ.ค.': '05', 'มิ.ย.': '06', 'ก.ค.': '07', 'ส.ค.': '08',
            'ก.ย.': '09', 'ต.ค.': '10', 'พ.ย.': '11', 'ธ.ค.': '12'
        }
        
        # Compiled regex patterns for better performance
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile all regex patterns"""
        # Date patterns (Thai Buddhist calendar)
        self.date_patterns = [
            # dd/mm/yyyy format (Thai year)
            re.compile(r'(\d{1,2})[/\-\.]\s*(\d{1,2})[/\-\.]\s*(\d{4})'),
            # dd/mm/yy format
            re.compile(r'(\d{1,2})[/\-\.]\s*(\d{1,2})[/\-\.]\s*(\d{2})'),
            # Thai text date format
            re.compile(r'(\d{1,2})\s*([ก-๙\w\.]{2,15})\s*(\d{4})')
        ]
        
        # Tax ID pattern (13 digits with possible spaces/dashes)
        self.tax_id_pattern = re.compile(r'(\d[\s\-]*){13}')
        
        # Phone patterns
        self.phone_patterns = [
            re.compile(r'0[2-9][\s\-]*\d{3}[\s\-]*\d{4}'),  # Thai landline
            re.compile(r'0[6-9][\s\-]*\d{4}[\s\-]*\d{4}'),  # Thai mobile
            re.compile(r'02[\s\-]*\d{3}[\s\-]*\d{4}')       # Bangkok area
        ]
        
        # Amount patterns
        self.amount_patterns = [
            re.compile(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)'),
            re.compile(r'(\d+(?:\.\d{2})?)')
        ]
        
        # Invoice number patterns - IMPROVED FOR CT FORMAT
        self.invoice_patterns = [
            re.compile(r'(?:เลขที่บิล|เลขที่|หมายเลข|เลขบิล|No\.?\s*)[:：]?\s*([A-Z]{1,3}\s*\d{2}[\-\s]*\d{6,})', re.IGNORECASE),  # CT 68-000612
            re.compile(r'([A-Z]{1,3}\s*\d{2}[\-\s]*\d{6,})'),  # CT68-000612 or CT 68-000612
            re.compile(r'(?:เลขที่|No\.?\s*)[:：]?\s*([A-Z0-9\-/]+)', re.IGNORECASE),
            re.compile(r'([A-Z]{2,4}[\-/]?\d{6,})'),
            re.compile(r'(\d{12,13})')  # Long numbers like barcodes
        ]
        
        # Company name indicators
        self.company_indicators = [
            'บริษัท', 'ห้างหุ้นส่วน', 'ร้าน', 'องค์การ', 'มหาวิทยาลัย',
            'โรงงาน', 'สำนักงาน', 'ศูนย์', 'สถาบัน'
        ]
    
    def parse_invoice_text(self, ocr_text: str) -> Dict[str, Any]:
        """
        Parse OCR text และแยกข้อมูลออกเป็น structured format
        
        Args:
            ocr_text: ข้อความที่ได้จาก OCR
            
        Returns:
            Dictionary ของข้อมูลที่แยกได้
        """
        logger.info("เริ่มแยกข้อมูลจากใบภาษี")
        
        # Initialize result structure
        result = self._initialize_result_structure()
        
        # Clean and prepare text
        cleaned_text = self._clean_text(ocr_text)
        lines = cleaned_text.split('\n')
        
        # Parse different sections
        result['issue_date'] = self._extract_issue_date(cleaned_text, lines)
        result['tax_date'] = result['issue_date']  # Usually same as issue date
        result['due_date'] = self._extract_due_date(cleaned_text, lines)
        
        result['invoice_number'] = self._extract_invoice_number(cleaned_text, lines)
        result['reference'] = self._extract_reference(cleaned_text, lines)
        
        # Company information
        company_info = self._extract_company_info(cleaned_text, lines)
        result.update(company_info)
        
        # Tax information
        tax_info = self._extract_tax_information(cleaned_text, lines)
        result.update(tax_info)
        
        # Items and amounts
        amounts = self._extract_amounts(cleaned_text, lines)
        result.update(amounts)
        
        # Set defaults for required fields
        result = self._set_defaults(result)
        
        logger.info(f"แยกข้อมูลเสร็จสิ้น: พบข้อมูล {len([v for v in result.values() if v])} ฟิลด์")
        
        return result
    
    def _initialize_result_structure(self) -> Dict[str, Any]:
        """Initialize empty result structure"""
        return {
            'issue_date': '',
            'company_format': 'AP',  # Default document series
            'invoice_number': '',
            'reference': '',
            'tax_option': 'in',  # Default to tax inclusive
            'contact_id': '',
            'title': '',
            'name': '',
            'organization': '',
            'branch': '',
            'address': '',
            'email': '',
            'telephone': '',
            'tax_id': '',
            'staff': '',
            'department': '',
            'project': '',
            'warehouse': '',
            'due_date': '',
            'type': '',
            'wht': '0.00',
            'tax_report': 'yes',  # Default to show in tax report
            'tax_date': '',
            # Additional fields for amounts
            'subtotal': '0.00',
            'vat_amount': '0.00',
            'total_amount': '0.00',
            'vat_rate': '7'  # Default VAT rate in Thailand
        }
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize OCR text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common OCR errors in Thai
        replacements = {
            'ๆ': 'ๆ',  # Normalize Thai repeat character
            '０': '0', '１': '1', '２': '2', '３': '3', '４': '4',
            '５': '5', '６': '6', '７': '7', '８': '8', '９': '9',
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text.strip()
    
    def _extract_issue_date(self, text: str, lines: List[str]) -> str:
        """Extract issue date from text"""
        # Look for date patterns
        for pattern in self.date_patterns:
            matches = pattern.findall(text)
            for match in matches:
                if len(match) == 3:
                    day, month, year = match
                    
                    # Convert Thai Buddhist year to Christian year if needed
                    year = int(year)
                    if year > 2400:  # Buddhist year
                        year -= 543
                    elif year < 100:  # Two digit year
                        year += 2000 if year < 50 else 1900
                    
                    # Handle month (could be Thai month name)
                    if month.isdigit():
                        month = int(month)
                    else:
                        month = int(self.thai_months.get(month, '1'))
                    
                    try:
                        # Validate date
                        date_obj = date(year, month, int(day))
                        return date_obj.strftime('%Y-%m-%d')
                    except ValueError:
                        continue
        
        # If no valid date found, return current date
        return datetime.now().strftime('%Y-%m-%d')
    
    def _extract_due_date(self, text: str, lines: List[str]) -> str:
        """Extract due date (usually same as issue date for tax invoices)"""
        # For tax invoices, due date is often the same as issue date
        issue_date = self._extract_issue_date(text, lines)
        
        # Look for specific due date mentions
        due_patterns = [
            r'(?:กำหนด|ครบกำหนด|Due).*?(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})',
            r'(?:ชำระ|จ่าย).*?(\d{1,2}[/\-\.]\d{1,2}[/\-\.]\d{2,4})'
        ]
        
        for pattern in due_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                # Parse this date similar to issue_date
                # For now, return issue_date
                break
        
        return issue_date
    
    def _extract_invoice_number(self, text: str, lines: List[str]) -> str:
        """Extract invoice number - IMPROVED"""
        # Try different patterns in order of priority
        for pattern in self.invoice_patterns:
            matches = pattern.findall(text)
            if matches:
                # Return the first reasonable looking invoice number
                for match in matches:
                    clean_match = match.strip().replace(' ', '')  # Remove spaces
                    if len(clean_match) >= 5:  # Minimum length for invoice number
                        # Prefer format like CT68-000612
                        if re.match(r'[A-Z]{1,3}\d{2}[\-\s]*\d{6,}', clean_match):
                            return clean_match
                        # Also accept other formats
                        if not clean_match.isdigit() or len(clean_match) >= 10:
                            return clean_match
        
        # If no invoice number found, generate one based on date
        today = datetime.now()
        return f"AP{today.strftime('%Y%m%d')}001"
    
    def _extract_reference(self, text: str, lines: List[str]) -> str:
        """Extract reference document"""
        ref_patterns = [
            r'(?:อ้างอิง|Reference|Ref)[:：]?\s*([A-Z0-9\-/]+)',
            r'(?:เอกสารอ้างอิง)[:：]?\s*([A-Z0-9\-/]+)'
        ]
        
        for pattern in ref_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ''
    
    def _extract_company_info(self, text: str, lines: List[str]) -> Dict[str, str]:
        """Extract company/contact information"""
        info = {
            'name': '',
            'organization': '',
            'address': '',
            'telephone': '',
            'tax_id': '',
            'title': ''
        }
        
        # Extract company name (usually near the top)
        for i, line in enumerate(lines[:10]):  # Check first 10 lines
            for indicator in self.company_indicators:
                if indicator in line:
                    # Clean up the company name
                    company_name = line.strip()
                    company_name = re.sub(r'\(.*?\)', '', company_name)  # Remove parentheses
                    info['organization'] = company_name.strip()
                    info['name'] = company_name.strip()
                    break
            if info['organization']:
                break
        
        # Extract tax ID
        tax_match = self.tax_id_pattern.search(text)
        if tax_match:
            tax_id = re.sub(r'[\s\-]', '', tax_match.group())
            if len(tax_id) == 13:
                info['tax_id'] = tax_id
        
        # Extract phone number
        for pattern in self.phone_patterns:
            phone_match = pattern.search(text)
            if phone_match:
                phone = re.sub(r'[\s\-]', '', phone_match.group())
                info['telephone'] = phone
                break
        
        # Extract address (lines containing address indicators)
        address_lines = []
        address_indicators = ['ที่อยู่', 'จังหวัด', 'แขวง', 'เขต', 'ตำบล', 'อำเภอ', 'ถนน']
        
        for line in lines:
            if any(indicator in line for indicator in address_indicators):
                # Clean address line
                cleaned_line = re.sub(r'(?:ที่อยู่|Address)[:：]?', '', line).strip()
                if cleaned_line:
                    address_lines.append(cleaned_line)
        
        if address_lines:
            info['address'] = ' '.join(address_lines[:3])  # Limit to first 3 address lines
        
        # Generate title/code from company name
        if info['organization']:
            # Simple title generation (first letters of words)
            words = info['organization'].replace('บริษัท', '').replace('จำกัด', '').strip().split()
            if words:
                info['title'] = ''.join([word[0].upper() for word in words[:3] if word])
        
        return info
    
    def _extract_tax_information(self, text: str, lines: List[str]) -> Dict[str, str]:
        """Extract tax-related information"""
        info = {
            'tax_option': 'in',  # Default to inclusive
            'tax_report': 'yes',
            'vat_rate': '7'
        }
        
        # Check for tax exclusive indicators
        exclusive_indicators = [
            'ไม่รวมภาษี', 'ก่อนภาษี', 'excluded', 'exclusive', 'before tax'
        ]
        
        for indicator in exclusive_indicators:
            if indicator.lower() in text.lower():
                info['tax_option'] = 'ex'
                break
        
        # Extract VAT rate if mentioned
        vat_patterns = [
            r'VAT\s*(\d+)%',
            r'ภาษี\s*(\d+)\s*%',
            r'อัตรา\s*(\d+)\s*%'
        ]
        
        for pattern in vat_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                info['vat_rate'] = match.group(1)
                break
        
        return info
    
    def _extract_amounts(self, text: str, lines: List[str]) -> Dict[str, str]:
        """Extract monetary amounts"""
        amounts = {
            'subtotal': '0.00',
            'vat_amount': '0.00',
            'total_amount': '0.00'
        }
        
        # Enhanced patterns for Thai invoice amounts
        # Pattern 1: รวมเป็นเงิน, รวมทั้งสิ้น, รวมราคา
        subtotal_patterns = [
            re.compile(r'(?:รวมเป็นเงิน|รวมทั้งสิ้น|รวมราคา|subtotal|sub-total)[\s:：]*([0-9,]+\.?\d{0,2})', re.IGNORECASE),
            re.compile(r'(?:รวม)[\s:：]+([0-9,]+\.?\d{0,2})(?!\s*%)', re.IGNORECASE),  # รวม ตามด้วยตัวเลข แต่ไม่ตามด้วย %
        ]
        
        # Pattern 2: VAT, ภาษีมูลค่าเพิ่ม, vat 7%
        vat_patterns = [
            re.compile(r'(?:vat|ภาษี(?:มูลค่าเพิ่ม)?)\s*(?:\d+\s*%)?\s*([0-9,]+\.?\d{0,2})', re.IGNORECASE),
            re.compile(r'(?:ภาษี|vat)\s*([0-9,]+\.?\d{0,2})', re.IGNORECASE),
        ]
        
        # Pattern 3: ยอดเงินสุทธิ, ยอดรวมสุทธิ, จำนวนเงินทั้งสิ้น, Grand Total
        total_patterns = [
            re.compile(r'(?:ยอดเงินสุทธิ|ยอดรวมสุทธิ|จำนวนเงินทั้งสิ้น|grand\s*total|net\s*total|total)[\s:：]*([0-9,]+\.?\d{0,2})', re.IGNORECASE),
            re.compile(r'(?:ยอด|total)[\s]+(?:สุทธิ|รวม)[\s:：]*([0-9,]+\.?\d{0,2})', re.IGNORECASE),
        ]
        
        # Try to extract subtotal
        for pattern in subtotal_patterns:
            match = pattern.search(text)
            if match:
                amount_str = match.group(1).replace(',', '').strip()
                try:
                    amount = float(amount_str)
                    if 0 < amount < 10000000:  # Sanity check
                        amounts['subtotal'] = f"{amount:.2f}"
                        logger.info(f"พบยอดรวมก่อนภาษี: {amounts['subtotal']}")
                        break
                except ValueError:
                    continue
        
        # Try to extract VAT
        for pattern in vat_patterns:
            match = pattern.search(text)
            if match:
                amount_str = match.group(1).replace(',', '').strip()
                try:
                    amount = float(amount_str)
                    if 0 < amount < 1000000:  # VAT shouldn't be too large
                        amounts['vat_amount'] = f"{amount:.2f}"
                        logger.info(f"พบภาษี VAT: {amounts['vat_amount']}")
                        break
                except ValueError:
                    continue
        
        # Try to extract total
        for pattern in total_patterns:
            match = pattern.search(text)
            if match:
                amount_str = match.group(1).replace(',', '').strip()
                try:
                    amount = float(amount_str)
                    if 0 < amount < 10000000:  # Sanity check
                        amounts['total_amount'] = f"{amount:.2f}"
                        logger.info(f"พบยอดรวมสุทธิ: {amounts['total_amount']}")
                        break
                except ValueError:
                    continue
        
        # Validate and calculate missing amounts
        try:
            subtotal = float(amounts['subtotal'])
            vat = float(amounts['vat_amount'])
            total = float(amounts['total_amount'])
            
            # If we have 2 out of 3, calculate the missing one
            if subtotal > 0 and vat > 0 and total == 0:
                amounts['total_amount'] = f"{(subtotal + vat):.2f}"
                logger.info(f"คำนวณยอดรวมสุทธิ: {amounts['total_amount']}")
            elif subtotal > 0 and total > 0 and vat == 0:
                amounts['vat_amount'] = f"{(total - subtotal):.2f}"
                logger.info(f"คำนวณภาษี VAT: {amounts['vat_amount']}")
            elif vat > 0 and total > 0 and subtotal == 0:
                amounts['subtotal'] = f"{(total - vat):.2f}"
                logger.info(f"คำนวณยอดรวมก่อนภาษี: {amounts['subtotal']}")
                
        except ValueError:
            pass
        
        return amounts
    
    def _set_defaults(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Set default values for missing required fields"""
        # Generate invoice number if missing
        if not result['invoice_number']:
            today = datetime.now()
            result['invoice_number'] = f"AP{today.strftime('%Y%m%d')}001"
        
        # Set default dates if missing
        today_str = datetime.now().strftime('%Y-%m-%d')
        if not result['issue_date']:
            result['issue_date'] = today_str
        if not result['due_date']:
            result['due_date'] = result['issue_date']
        if not result['tax_date']:
            result['tax_date'] = result['issue_date']
        
        # Ensure amounts are formatted properly
        for field in ['subtotal', 'vat_amount', 'total_amount', 'wht']:
            try:
                value = float(result[field])
                result[field] = f"{value:.2f}"
            except (ValueError, TypeError):
                result[field] = '0.00'
        
        return result
    
    def export_to_json(self, parsed_data: Dict[str, Any], output_path: str = None) -> str:
        """
        Export parsed data to JSON file
        
        Args:
            parsed_data: ข้อมูลที่แยกได้
            output_path: path สำหรับบันทึกไฟล์
            
        Returns:
            path ของไฟล์ที่บันทึก
        """
        if output_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = f"outputs/parsed_invoice_{timestamp}.json"
        
        # Ensure directory exists
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Add metadata
        export_data = {
            'metadata': {
                'parsed_at': datetime.now().isoformat(),
                'parser_version': '1.0',
                'total_fields': len(parsed_data),
                'filled_fields': len([v for v in parsed_data.values() if v])
            },
            'invoice_data': parsed_data
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Exported parsed data to: {output_path}")
        return output_path
    
    def validate_parsed_data(self, data: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validate parsed data and return validation errors
        
        Args:
            data: ข้อมูลที่แยกได้
            
        Returns:
            Dictionary ของ validation errors
        """
        errors = {
            'missing_required': [],
            'invalid_format': [],
            'warnings': []
        }
        
        # Required fields
        required_fields = ['issue_date', 'invoice_number', 'tax_id']
        for field in required_fields:
            if not data.get(field):
                errors['missing_required'].append(f"Missing required field: {field}")
        
        # Date format validation
        date_fields = ['issue_date', 'due_date', 'tax_date']
        for field in date_fields:
            if data.get(field):
                try:
                    datetime.strptime(data[field], '%Y-%m-%d')
                except ValueError:
                    errors['invalid_format'].append(f"Invalid date format in {field}: {data[field]}")
        
        # Tax ID validation
        if data.get('tax_id'):
            tax_id = data['tax_id']
            if not tax_id.isdigit() or len(tax_id) != 13:
                errors['invalid_format'].append(f"Invalid tax ID format: {tax_id}")
        
        # Amount validation
        amount_fields = ['subtotal', 'vat_amount', 'total_amount', 'wht']
        for field in amount_fields:
            if data.get(field):
                try:
                    float(data[field])
                except ValueError:
                    errors['invalid_format'].append(f"Invalid amount format in {field}: {data[field]}")
        
        # Business logic warnings
        if data.get('total_amount') and data.get('subtotal'):
            try:
                total = float(data['total_amount'])
                subtotal = float(data['subtotal'])
                if total < subtotal:
                    errors['warnings'].append("Total amount is less than subtotal")
            except ValueError:
                pass
        
        return errors


def main():
    """Test the parser with sample data"""
    # Sample OCR text for testing
    sample_text = """
    บริษัท ซี 111 เดคคอร์ จำกัด (สาขาที่ 00001)
    ใบกำกับภาษี/ใบเสร็จรับเงิน
    เลขประจำตัวผู้เสียภาษี 0 1355 63000 95 2
    วันที่ 1/8/2568
    
    รายการสินค้า:
    1. ดอกสว่านโรตารี่ DF333QWYE/MAKITA - 4,380.00 บาท
    2. ดอกสว่าน 6.5 mm M6501B /MAKITA - 1,450.00 บาท
    
    รวมเป็นเงิน 5,449.60 บาท
    VAT 7% 381.40 บาท
    ยอดเงินสุทธิ 5,830.00 บาท
    """
    
    parser = ThaiTaxInvoiceParser()
    result = parser.parse_invoice_text(sample_text)
    
    print("=== Parsed Invoice Data ===")
    for key, value in result.items():
        print(f"{key}: {value}")
    
    # Export to JSON
    output_file = parser.export_to_json(result)
    print(f"\nExported to: {output_file}")
    
    # Validate
    errors = parser.validate_parsed_data(result)
    if any(errors.values()):
        print("\n=== Validation Errors ===")
        for error_type, error_list in errors.items():
            if error_list:
                print(f"{error_type}:")
                for error in error_list:
                    print(f"  - {error}")


if __name__ == "__main__":
    main()