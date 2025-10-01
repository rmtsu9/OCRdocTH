import pandas as pd
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, Any, List, Optional
import os

logger = logging.getLogger(__name__)

class ExcelExporter:
    """
    ระบบส่งออกข้อมูล structured data จากใบภาษีไปยัง Excel
    รองรับการเพิ่มข้อมูลใหม่ลงในไฟล์ Excel ที่มีอยู่
    """
    
    def __init__(self):
        """Initialize Excel Exporter"""
        self.base_path = Path(__file__).parent
        self.export_dir = self.base_path / "Export"
        self.ref_dir = self.export_dir / "ref"
        self.template_file = self.ref_dir / "Book.xlsx"
        
        # Ensure directories exist
        self.export_dir.mkdir(exist_ok=True)
        self.ref_dir.mkdir(exist_ok=True)
        
        # Field mapping (OCR field -> Excel column name)
        self.field_mapping = {
            'issue_date': 'AP Date',
            'company_format': 'Document Series',
            'invoice_number': 'Autorun Number', 
            'reference': 'Reference Document',
            'tax_option': 'Tax Option',
            'contact_id': 'Contact ID',
            'title': 'Contact Code',
            'name': 'Name/Shop',
            'organization': 'Organization/Company',
            'branch': 'Branch',
            'address': 'Address',
            'email': 'Email',
            'telephone': 'Telephone',
            'tax_id': 'Tax ID',
            'staff': 'Staff',
            'department': 'Department',
            'project': 'Project',
            'warehouse': 'Warehouse',
            'due_date': 'Due Date',
            'type': 'Accounting Formula',
            'wht': 'Withholding Tax',
            'tax_report': 'Tax Report',
            'tax_date': 'Tax Date',
            # Additional calculated fields
            'subtotal': 'Subtotal',
            'vat_amount': 'VAT Amount',
            'total_amount': 'Total Amount',
            'vat_rate': 'VAT Rate'
        }
        
        # Required column order for Excel
        self.excel_columns = [
            'AP Date', 'Document Series', 'Autorun Number', 'Reference Document',
            'Tax Option', 'Contact ID', 'Contact Code', 'Name/Shop', 
            'Organization/Company', 'Branch', 'Address', 'Email', 'Telephone',
            'Tax ID', 'Staff', 'Department', 'Project', 'Warehouse',
            'Due Date', 'Accounting Formula', 'Withholding Tax', 'Tax Report',
            'Tax Date', 'Subtotal', 'VAT Amount', 'Total Amount', 'VAT Rate',
            'Source File', 'OCR Engine', 'Processed Date', 'Confidence Score'
        ]
    
    def load_existing_data(self) -> pd.DataFrame:
        """
        โหลดข้อมูลที่มีอยู่จาก Excel template
        
        Returns:
            DataFrame ของข้อมูลที่มีอยู่ หรือ DataFrame ว่างถ้าไม่มีไฟล์
        """
        try:
            if self.template_file.exists():
                logger.info(f"Loading existing data from: {self.template_file}")
                # Try to read existing Excel file
                df = pd.read_excel(self.template_file)
                
                # Ensure all required columns exist
                for col in self.excel_columns:
                    if col not in df.columns:
                        df[col] = ''
                
                # Reorder columns
                df = df[self.excel_columns]
                return df
            else:
                logger.info("No existing template file found, creating new DataFrame")
                # Create new DataFrame with required columns
                return pd.DataFrame(columns=self.excel_columns)
                
        except Exception as e:
            logger.warning(f"Error loading existing Excel file: {e}")
            logger.info("Creating new DataFrame")
            return pd.DataFrame(columns=self.excel_columns)
    
    def prepare_row_data(self, parsed_data: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        เตรียมข้อมูลแถวเดียวสำหรับ Excel
        
        Args:
            parsed_data: ข้อมูลที่แยกจากใบภาษี
            metadata: metadata จากการประมวลผล
            
        Returns:
            Dictionary ของข้อมูลแถวเดียว
        """
        row_data = {}
        
        # Map parsed data to Excel columns
        for ocr_field, excel_col in self.field_mapping.items():
            value = parsed_data.get(ocr_field, '')
            
            # Format specific fields
            if excel_col in ['AP Date', 'Due Date', 'Tax Date']:
                # Ensure date format is YYYY-MM-DD
                if value and value != '':
                    try:
                        # If already in correct format, keep it
                        datetime.strptime(value, '%Y-%m-%d')
                        row_data[excel_col] = value
                    except ValueError:
                        # Try to parse and reformat
                        try:
                            parsed_date = pd.to_datetime(value)
                            row_data[excel_col] = parsed_date.strftime('%Y-%m-%d')
                        except:
                            row_data[excel_col] = value  # Keep original if can't parse
                else:
                    row_data[excel_col] = ''
            
            elif excel_col == 'Tax Option':
                # Ensure lowercase for case sensitivity
                if value and str(value).lower() in ['in', 'ex']:
                    row_data[excel_col] = str(value).lower()
                else:
                    row_data[excel_col] = 'in'  # Default to inclusive
            
            elif excel_col == 'Tax Report':
                # Ensure lowercase for case sensitivity
                if value and str(value).lower() in ['yes', 'no']:
                    row_data[excel_col] = str(value).lower()
                else:
                    row_data[excel_col] = 'yes'  # Default to show in report
            
            elif excel_col in ['Subtotal', 'VAT Amount', 'Total Amount', 'Withholding Tax']:
                # Format amounts to 2 decimal places
                try:
                    if value and value != '':
                        formatted_value = f"{float(value):.2f}"
                        row_data[excel_col] = formatted_value
                    else:
                        row_data[excel_col] = '0.00'
                except ValueError:
                    row_data[excel_col] = '0.00'
            
            elif excel_col == 'Tax ID':
                # Remove spaces/dashes from Tax ID
                if value:
                    clean_tax_id = str(value).replace(' ', '').replace('-', '')
                    row_data[excel_col] = clean_tax_id
                else:
                    row_data[excel_col] = ''
            
            elif excel_col == 'Telephone':
                # Format phone number
                if value:
                    clean_phone = str(value).replace(' ', '').replace('-', '')
                    row_data[excel_col] = clean_phone
                else:
                    row_data[excel_col] = ''
            
            else:
                # Default: use value as-is
                row_data[excel_col] = str(value) if value else ''
        
        # Add metadata columns
        row_data['Source File'] = Path(metadata.get('source_file', '')).name
        row_data['OCR Engine'] = metadata.get('ocr_engine', '')
        row_data['Processed Date'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Calculate confidence score based on filled fields
        total_fields = len([v for v in parsed_data.values()])
        filled_fields = len([v for v in parsed_data.values() if v and str(v).strip()])
        confidence = (filled_fields / total_fields * 100) if total_fields > 0 else 0
        row_data['Confidence Score'] = f"{confidence:.1f}%"
        
        return row_data
    
    def create_new_excel_file(self, parsed_result: Dict[str, Any], output_filename: Optional[str] = None) -> str:
        """
        สร้างไฟล์ Excel ใหม่สำหรับข้อมูลที่แยกได้
        
        Args:
            parsed_result: ผลลัพธ์จาก process_and_parse_invoice
            output_filename: ชื่อไฟล์ที่ต้องการ (optional)
            
        Returns:
            Path ของไฟล์ Excel ที่สร้างขึ้นใหม่
        """
        try:
            # Prepare new row data
            parsed_data = parsed_result.get('parsed_data', {})
            metadata = parsed_result.get('metadata', {})
            new_row = self.prepare_row_data(parsed_data, metadata)
            
            # Create new DataFrame with single row
            df = pd.DataFrame([new_row])
            
            # Generate output filename if not provided
            if output_filename is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                source_name = Path(metadata.get('source_file', 'invoice')).stem
                output_filename = f"{source_name}_tax_invoice_{timestamp}.xlsx"
            
            # Ensure it has .xlsx extension
            if not output_filename.endswith('.xlsx'):
                output_filename += '.xlsx'
            
            # Save to Export directory (not in ref subfolder)
            output_file = self.export_dir / output_filename
            
            # Create Excel file with multiple sheets
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # Main data sheet
                df.to_excel(writer, sheet_name='Tax Invoice Data', index=False)
                
                # Summary sheet
                summary_data = {
                    'Field': ['Source File', 'Processing Date', 'OCR Engine', 'Enhancement Used', 
                             'Confidence Score', 'Total Fields', 'Filled Fields'],
                    'Value': [
                        Path(metadata.get('source_file', '')).name,
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        metadata.get('ocr_engine', ''),
                        'Yes' if metadata.get('enhancement_used', False) else 'No',
                        new_row.get('Confidence Score', '0%'),
                        len(parsed_data),
                        len([v for v in parsed_data.values() if v and str(v).strip()])
                    ]
                }
                summary_df = pd.DataFrame(summary_data)
                summary_df.to_excel(writer, sheet_name='Processing Summary', index=False)
                
                # Raw OCR text sheet
                raw_text_data = {
                    'Raw OCR Text': [parsed_result.get('raw_ocr_text', '')]
                }
                raw_df = pd.DataFrame(raw_text_data)
                raw_df.to_excel(writer, sheet_name='Raw OCR Text', index=False)
            
            logger.info(f"New Excel file created: {output_file}")
            logger.info(f"File contains structured data for: {Path(metadata.get('source_file', '')).name}")
            
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Error creating new Excel file: {e}")
            raise
    
    def append_to_excel(self, parsed_result: Dict[str, Any]) -> str:
        """
        สร้างไฟล์ Excel ใหม่ (backward compatibility method)
        ตอนนี้จะเรียก create_new_excel_file แทน
        
        Args:
            parsed_result: ผลลัพธ์จาก process_and_parse_invoice
            
        Returns:
            Path ของไฟล์ Excel ที่สร้าง
        """
        return self.create_new_excel_file(parsed_result)
    
    def export_batch(self, parsed_results: List[Dict[str, Any]]) -> str:
        """
        ส่งออกข้อมูลหลายรายการไปยัง Excel
        
        Args:
            parsed_results: รายการผลลัพธ์จาก process_and_parse_invoice
            
        Returns:
            Path ของไฟล์ Excel ที่บันทึก
        """
        try:
            # Load existing data
            df = self.load_existing_data()
            
            # Prepare all new rows
            new_rows = []
            for result in parsed_results:
                parsed_data = result.get('parsed_data', {})
                metadata = result.get('metadata', {})
                new_row = self.prepare_row_data(parsed_data, metadata)
                new_rows.append(new_row)
            
            # Add all new rows to DataFrame
            if new_rows:
                new_df = pd.DataFrame(new_rows)
                df = pd.concat([df, new_df], ignore_index=True)
            
            # Save to Excel
            output_file = self.template_file
            df.to_excel(output_file, index=False, sheet_name='Tax Invoices')
            
            logger.info(f"Batch data exported to Excel file: {output_file}")
            logger.info(f"Added {len(new_rows)} records, total: {len(df)}")
            
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Error exporting batch to Excel: {e}")
            raise
    
    def create_summary_report(self, output_file: str = None) -> str:
        """
        สร้างรายงานสรุปจากข้อมูลใน Excel
        
        Args:
            output_file: ชื่อไฟล์สำหรับรายงาน (optional)
            
        Returns:
            Path ของไฟล์รายงาน
        """
        try:
            # Load data
            df = self.load_existing_data()
            
            if df.empty:
                logger.warning("No data available for summary report")
                return ""
            
            # Generate summary statistics
            summary_stats = {
                'Total Records': len(df),
                'Unique Organizations': df['Organization/Company'].nunique(),
                'Date Range': f"{df['AP Date'].min()} to {df['AP Date'].max()}",
                'Total Amount': f"{df['Total Amount'].astype(str).str.replace(',', '').astype(float).sum():.2f}",
                'Average Amount': f"{df['Total Amount'].astype(str).str.replace(',', '').astype(float).mean():.2f}",
                'OCR Engines Used': df['OCR Engine'].value_counts().to_dict(),
                'Average Confidence': f"{df['Confidence Score'].str.rstrip('%').astype(float).mean():.1f}%"
            }
            
            # Create summary report
            if output_file is None:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = self.export_dir / f"summary_report_{timestamp}.txt"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("=== TAX INVOICE OCR SUMMARY REPORT ===\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")
                
                for key, value in summary_stats.items():
                    if isinstance(value, dict):
                        f.write(f"{key}:\n")
                        for k, v in value.items():
                            f.write(f"  {k}: {v}\n")
                    else:
                        f.write(f"{key}: {value}\n")
                
                f.write("\n" + "=" * 50 + "\n")
                f.write("Detailed Records:\n\n")
                
                # Add detailed records summary
                for _, row in df.iterrows():
                    f.write(f"Invoice: {row['Autorun Number']}\n")
                    f.write(f"  Organization: {row['Organization/Company']}\n")
                    f.write(f"  Date: {row['AP Date']}\n")
                    f.write(f"  Amount: {row['Total Amount']}\n")
                    f.write(f"  Source: {row['Source File']}\n")
                    f.write(f"  Confidence: {row['Confidence Score']}\n\n")
            
            logger.info(f"Summary report created: {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"Error creating summary report: {e}")
            raise
    
    def validate_excel_data(self) -> Dict[str, List[str]]:
        """
        ตรวจสอบความถูกต้องของข้อมูลใน Excel
        
        Returns:
            Dictionary ของข้อผิดพลาดที่พบ
        """
        errors = {
            'missing_required': [],
            'invalid_format': [],
            'warnings': []
        }
        
        try:
            df = self.load_existing_data()
            
            if df.empty:
                errors['warnings'].append("No data to validate")
                return errors
            
            # Check required fields
            required_fields = ['AP Date', 'Autorun Number', 'Tax ID']
            for field in required_fields:
                missing_count = df[field].isna().sum() + (df[field] == '').sum()
                if missing_count > 0:
                    errors['missing_required'].append(f"{field}: {missing_count} missing values")
            
            # Check date formats
            date_fields = ['AP Date', 'Due Date', 'Tax Date']
            for field in date_fields:
                invalid_dates = []
                for idx, value in df[field].items():
                    if value and value != '':
                        try:
                            datetime.strptime(str(value), '%Y-%m-%d')
                        except ValueError:
                            invalid_dates.append(f"Row {idx+1}: {value}")
                
                if invalid_dates:
                    errors['invalid_format'].extend([f"{field} - {error}" for error in invalid_dates])
            
            # Check Tax ID format
            for idx, tax_id in df['Tax ID'].items():
                if tax_id and tax_id != '':
                    clean_id = str(tax_id).replace(' ', '').replace('-', '')
                    if not clean_id.isdigit() or len(clean_id) != 13:
                        errors['invalid_format'].append(f"Tax ID Row {idx+1}: Invalid format - {tax_id}")
            
            # Check amount formats
            amount_fields = ['Subtotal', 'VAT Amount', 'Total Amount']
            for field in amount_fields:
                for idx, value in df[field].items():
                    if value and value != '':
                        try:
                            float(str(value).replace(',', ''))
                        except ValueError:
                            errors['invalid_format'].append(f"{field} Row {idx+1}: Invalid amount - {value}")
            
            logger.info(f"Validation completed. Found {len(errors['missing_required']) + len(errors['invalid_format'])} errors")
            
        except Exception as e:
            errors['warnings'].append(f"Validation error: {e}")
        
        return errors


def main():
    """Test the Excel exporter"""
    # Sample test data
    sample_parsed_result = {
        'metadata': {
            'source_file': 'test_invoice.jpg',
            'ocr_engine': 'tesseract',
            'enhancement_used': True,
            'processed_at': datetime.now().isoformat()
        },
        'parsed_data': {
            'issue_date': '2025-01-15',
            'company_format': 'AP',
            'invoice_number': 'AP202501150001',
            'tax_option': 'in',
            'organization': 'บริษัท ทดสอบ จำกัด',
            'tax_id': '1234567890123',
            'telephone': '0212345678',
            'total_amount': '5830.00',
            'vat_amount': '381.40',
            'subtotal': '5448.60'
        }
    }
    
    # Test export
    exporter = ExcelExporter()
    excel_file = exporter.append_to_excel(sample_parsed_result)
    print(f"Exported to: {excel_file}")
    
    # Test validation
    errors = exporter.validate_excel_data()
    print("Validation results:")
    for error_type, error_list in errors.items():
        if error_list:
            print(f"{error_type}:")
            for error in error_list:
                print(f"  - {error}")
    
    # Create summary report
    report_file = exporter.create_summary_report()
    print(f"Summary report: {report_file}")


if __name__ == "__main__":
    main()