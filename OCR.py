import os
import sys
from pathlib import Path
from typing import List, Optional
import logging
from pdf2image import convert_from_path

# OCR imports
try:
    import pytesseract
    from PIL import Image
except ImportError:
    pytesseract = None

# LLM imports (optional)
try:
    from llm_processor import LLMProcessor
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFToImageConverter:
    """
    PDF to Image converter system
    Focused on converting PDF files to high-quality images for further processing
    """
    
    def __init__(self, poppler_path: Optional[str] = None):
        """
        Initialize PDF to Image converter
        
        Args:
            poppler_path: Path to poppler binaries (if not in system PATH)
        """
        self.poppler_path = poppler_path
        if not self.poppler_path:
            # Try to find poppler in the project directory
            project_poppler = Path(__file__).parent / "Lib" / "poppler-25.07.0" / "Library" / "bin"
            if project_poppler.exists():
                self.poppler_path = str(project_poppler)
                logger.info(f"Found poppler at: {self.poppler_path}")
            else:
                logger.warning("Poppler path not specified and not found in project directory")
        
        # Create output directories
        self.base_path = Path(__file__).parent
        self.output_dir = self.base_path / "outputs"
        self.tmp_dir = self.base_path / "tmp"
        self.output_dir.mkdir(exist_ok=True)
        self.tmp_dir.mkdir(exist_ok=True)
    
    def convert_pdf_to_images(
        self, 
        pdf_path: str, 
        output_folder: Optional[str] = None,
        dpi: int = 300,
        output_format: str = 'PNG'
    ) -> List[str]:
        """
        Convert PDF pages to high-quality images
        
        Args:
            pdf_path: Path to the PDF file
            dpi: Resolution for conversion (higher = better quality)
            output_folder: Folder to save converted images (optional)
            
        Returns:
            List of paths to converted image files
        """
        try:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            logger.info(f"Converting PDF to images: {pdf_path.name}")
            
            # Set output folder
            if output_folder is None:
                output_folder = pdf_path.parent / "tmp" / pdf_path.stem
            output_folder = Path(output_folder)
            output_folder.mkdir(parents=True, exist_ok=True)
            
            # Convert PDF to images
            convert_kwargs = {
                'dpi': dpi,
                'output_format': 'PNG',
                'thread_count': 1  # Conservative for stability
            }
            
            if self.poppler_path:
                convert_kwargs['poppler_path'] = self.poppler_path
            
            pages = convert_from_path(str(pdf_path), **convert_kwargs)
            
            # Save images and collect paths
            image_paths = []
            for i, page in enumerate(pages, 1):
                image_path = output_folder / f"page_{i:03d}.png"
                page.save(str(image_path), 'PNG', optimize=True)
                image_paths.append(str(image_path))
                logger.info(f"Saved page {i} to: {image_path}")
            
            logger.info(f"Successfully converted {len(pages)} pages")
            return image_paths
            
        except Exception as e:
            logger.error(f"Error converting PDF to images: {str(e)}")
            raise
    
    def extract_text_with_pdfplumber(self, pdf_path: str) -> str:
        """
        Extract text directly from PDF using pdfplumber
        This is faster but may not work well with scanned documents
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text
        """
        try:
            text_content = []
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text()
                    if text:
                        text_content.append(f"--- Page {page_num} ---\n{text}\n")
                    else:
                        logger.warning(f"No text found on page {page_num}")
            
            return "\n".join(text_content)
            
        except Exception as e:
            logger.error(f"Error extracting text with pdfplumber: {str(e)}")
            return ""
    
    def is_scanned_pdf(self, pdf_path: str) -> bool:
        """
        Determine if PDF is scanned (image-based) or contains extractable text
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            True if PDF appears to be scanned, False if it contains extractable text
        """
        try:
            text = self.extract_text_with_pdfplumber(pdf_path)
            # If we get very little text, it's likely a scanned document
            return len(text.strip()) < 50
        except:
            return True  # Assume scanned if we can't extract text


class ImagePreprocessor:
    """
    Handles image preprocessing to improve OCR accuracy
    Optimized for Thai tax documents and invoices
    """
    
    @staticmethod
    def enhance_image(image_path: str, output_path: Optional[str] = None) -> str:
        """
        Enhance image quality for better OCR results
        
        Args:
            image_path: Path to input image
            output_path: Path to save enhanced image (optional)
            
        Returns:
            Path to enhanced image
        """
        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Apply denoising
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Apply adaptive thresholding for better contrast
            adaptive_thresh = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Apply morphological operations to clean up
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_CLOSE, kernel)
            
            # Save enhanced image
            if output_path is None:
                path_obj = Path(image_path)
                output_path = path_obj.parent / f"{path_obj.stem}_enhanced{path_obj.suffix}"
            
            cv2.imwrite(str(output_path), cleaned)
            logger.info(f"Enhanced image saved to: {output_path}")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error enhancing image: {str(e)}")
            return image_path  # Return original if enhancement fails
    
    @staticmethod
    def resize_image(image_path: str, scale_factor: float = 2.0) -> str:
        """
        Resize image to improve OCR accuracy
        
        Args:
            image_path: Path to input image
            scale_factor: Factor to scale image by
            
        Returns:
            Path to resized image
        """
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            # Calculate new dimensions
            height, width = image.shape[:2]
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            
            # Resize with high-quality interpolation
            resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
            # Save resized image
            path_obj = Path(image_path)
            output_path = path_obj.parent / f"{path_obj.stem}_resized{path_obj.suffix}"
            cv2.imwrite(str(output_path), resized)
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error resizing image: {str(e)}")
            return image_path


class OCREngine:
    """
    Wrapper for multiple OCR engines with Thai language support
    """
    
    def __init__(self):
        """Initialize OCR engines"""
        self.available_engines = []
        
        # Check Tesseract
        try:
            import pytesseract
            from PIL import Image
            
            # Try to find Tesseract in project directory first
            project_tesseract = Path(__file__).parent / "Lib" / "Tesseract-OCR" / "tesseract.exe"
            
            tesseract_paths = [
                str(project_tesseract),  # Local project installation
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Users\Administrator\AppData\Local\Programs\Tesseract-OCR\tesseract.exe',
                r'C:\tesseract\tesseract.exe'
            ]
            
            tesseract_found = False
            for path in tesseract_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    tesseract_found = True
                    logger.info(f"Found Tesseract at: {path}")
                    break
            
            if tesseract_found:
                # Test Tesseract
                version = pytesseract.get_tesseract_version()
                self.available_engines.append('tesseract')
                logger.info(f"Tesseract OCR is available (version: {version})")
            else:
                logger.warning("Tesseract executable not found in any paths")
                
        except Exception as e:
            logger.warning(f"Tesseract OCR not available: {e}")
        
        # Check PaddleOCR
        try:
            import paddleocr
            self.paddle_ocr = paddleocr.PaddleOCR(use_angle_cls=True, lang='th')
            self.available_engines.append('paddleocr')
            logger.info("PaddleOCR is available")
        except Exception as e:
            logger.warning(f"PaddleOCR not available: {e}")
            self.paddle_ocr = None
        
        # Check EasyOCR
        try:
            import easyocr
            self.easy_ocr = easyocr.Reader(['th', 'en'])
            self.available_engines.append('easyocr')
            logger.info("EasyOCR is available")
        except Exception as e:
            logger.warning(f"EasyOCR not available: {e}")
            self.easy_ocr = None
        
        if not self.available_engines:
            raise RuntimeError("No OCR engines available!")
        
        logger.info(f"Available OCR engines: {', '.join(self.available_engines)}")
    
    def extract_text_tesseract(self, image_path: str) -> str:
        """Extract text using Tesseract OCR"""
        try:
            # Configure for Thai + English
            config = '--oem 3 --psm 6 -l tha+eng'
            text = pytesseract.image_to_string(Image.open(image_path), config=config)
            return text.strip()
        except Exception as e:
            logger.error(f"Tesseract OCR error: {e}")
            return ""
    
    def extract_text_paddleocr(self, image_path: str) -> str:
        """Extract text using PaddleOCR"""
        try:
            if self.paddle_ocr is None:
                return ""
            
            result = self.paddle_ocr.ocr(image_path, cls=True)
            text_lines = []
            
            if result and result[0]:
                for line in result[0]:
                    if line and len(line) > 1:
                        text_lines.append(line[1][0])
            
            return '\n'.join(text_lines)
            
        except Exception as e:
            logger.error(f"PaddleOCR error: {e}")
            return ""
    
    def extract_text_easyocr(self, image_path: str) -> str:
        """Extract text using EasyOCR"""
        try:
            if self.easy_ocr is None:
                return ""
            
            result = self.easy_ocr.readtext(image_path)
            text_lines = [item[1] for item in result if len(item) > 1]
            return '\n'.join(text_lines)
            
        except Exception as e:
            logger.error(f"EasyOCR error: {e}")
            return ""
    
    def extract_text(self, image_path: str, engine: str = 'auto') -> str:
        """
        Extract text using specified OCR engine
        
        Args:
            image_path: Path to image file
            engine: OCR engine to use ('tesseract', 'paddleocr', 'easyocr', 'auto')
            
        Returns:
            Extracted text
        """
        if engine == 'auto':
            engine = self.available_engines[0]  # Use first available engine
        
        if engine == 'tesseract' and 'tesseract' in self.available_engines:
            return self.extract_text_tesseract(image_path)
        elif engine == 'paddleocr' and 'paddleocr' in self.available_engines:
            return self.extract_text_paddleocr(image_path)
        elif engine == 'easyocr' and 'easyocr' in self.available_engines:
            return self.extract_text_easyocr(image_path)
        else:
            logger.error(f"OCR engine '{engine}' not available")
            return ""


class DocumentOCR:
    """
    Main OCR class that handles document processing workflow
    Specialized for Thai tax documents and invoices
    """
    
    def __init__(self, poppler_path: Optional[str] = None, use_llm: bool = False, llm_provider: str = "openai", llm_model: str = "gpt-4o-mini"):
        """
        Initialize Document OCR system
        
        Args:
            poppler_path: Path to poppler binaries
            use_llm: Whether to use LLM for post-processing (default: False)
            llm_provider: LLM provider ("openai", "anthropic", or "local")
            llm_model: LLM model name
        """
        # Import the actual ImagePreprocessor
        from Image_Preprocessor import ImagePreprocessor
        from PDF_to_Image import PDFToImageConverter
        from tax_invoice_parser import ThaiTaxInvoiceParser
        
        self.pdf_converter = PDFToImageConverter(poppler_path)
        self.preprocessor = ImagePreprocessor()
        self.ocr_engine = OCREngine()
        self.parser = ThaiTaxInvoiceParser()
        
        # Initialize LLM processor if requested
        self.use_llm = use_llm and LLM_AVAILABLE
        self.llm_processor = None
        
        if self.use_llm:
            try:
                self.llm_processor = LLMProcessor(provider=llm_provider, model=llm_model)
                logger.info(f"🧠 LLM Processor initialized: {llm_provider}/{llm_model}")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM processor: {e}")
                self.use_llm = False
        
        if not self.use_llm:
            logger.info("📋 Running without LLM (rule-based only)")
        
        # Create output directories
        self.base_path = Path(__file__).parent
        self.tmp_dir = self.base_path / "tmp"
        self.output_dir = self.base_path / "outputs"
        self.tmp_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
    
    def process_pdf(self, pdf_path: str, engine: str = 'auto', enhance_images: bool = True) -> str:
        """
        Process PDF document and extract text using OCR
        
        Args:
            pdf_path: Path to PDF file
            engine: OCR engine to use
            enhance_images: Whether to enhance images before OCR
            
        Returns:
            Extracted text content
        """
        logger.info(f"Processing PDF: {Path(pdf_path).name}")
        
        # Convert PDF to images for OCR processing
        logger.info("Converting PDF to images for OCR processing")
        image_paths = self.pdf_converter.convert_pdf_to_images(pdf_path)
        
        # Process each page
        all_text = []
        for i, image_path in enumerate(image_paths, 1):
            logger.info(f"Processing page {i}/{len(image_paths)}")
            
            # Enhance image if requested
            if enhance_images:
                image_path = self.preprocessor.preprocess_for_ocr(image_path, gentle_mode=True)
            
            # Extract text
            text = self.ocr_engine.extract_text(image_path, engine)
            if text:
                all_text.append(f"--- Page {i} ---\n{text}\n")
        
        return "\n".join(all_text)
    
    def process_image(self, image_path: str, engine: str = 'auto', enhance_image: bool = True) -> str:
        """
        Process single image file and extract text using OCR
        
        Args:
            image_path: Path to image file
            engine: OCR engine to use
            enhance_image: Whether to enhance image before OCR
            
        Returns:
            Extracted text content
        """
        logger.info(f"Processing image: {Path(image_path).name}")
        
        # Enhance image if requested
        if enhance_image:
            image_path = self.preprocessor.preprocess_for_ocr(image_path, gentle_mode=True)
        
        # Extract text
        return self.ocr_engine.extract_text(image_path, engine)
    
    def process_file(self, file_path: str, engine: str = 'auto', enhance_images: bool = True) -> str:
        """
        Process any supported file (PDF or image) and extract text
        
        Args:
            file_path: Path to file
            engine: OCR engine to use
            enhance_images: Whether to enhance images before OCR
            
        Returns:
            Extracted text content
        """
        file_pathobj = Path(file_path)
        
        if not file_pathobj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine file type and process accordingly
        if file_pathobj.suffix.lower() == '.pdf':
            return self.process_pdf(file_path, engine, enhance_images)
        elif file_pathobj.suffix.lower() in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            return self.process_image(file_path, engine, enhance_images)
        else:
            raise ValueError(f"Unsupported file type: {file_pathobj.suffix}")
    
    def process_and_parse_invoice(self, file_path: str, engine: str = 'auto', 
                                 enhance_images: bool = True, trcloud_format: dict = None) -> dict:
        """
        Process file และแยกข้อมูลใบภาษีเป็น structured data
        
        Args:
            file_path: Path to file (PDF or image)
            engine: OCR engine to use ('auto', 'tesseract', 'easyocr' or combination)
            enhance_images: Whether to enhance images before OCR
            trcloud_format: TRCloud invoice number format settings
            
        Returns:
            Dictionary ของข้อมูลที่แยกได้พร้อม metadata
        """
        logger.info(f"Processing and parsing invoice: {Path(file_path).name}")
        
        # Extract text using OCR
        ocr_text = self.process_file(file_path, engine, enhance_images)
        
        # Parse the text to structured data
        parsed_data = self.parser.parse_invoice_text(ocr_text)
        
        # 🧠 LLM POST-PROCESSING (ถ้าเปิดใช้งาน)
        if self.use_llm and self.llm_processor:
            logger.info("🧠 Applying LLM post-processing...")
            try:
                parsed_data = self.llm_processor.process_ocr_results(
                    ocr_text=ocr_text,
                    parsed_data=parsed_data,
                    document_type="tax_invoice"
                )
                logger.info("✨ LLM enhanced data successfully")
            except Exception as e:
                logger.warning(f"LLM processing failed: {e}, using original data")
        
        # Apply TRCloud formatting if provided
        if trcloud_format:
            parsed_data = self.apply_trcloud_format(parsed_data, trcloud_format)
        
        # Add metadata
        from datetime import datetime
        result = {
            'success': True,
            'metadata': {
                'source_file': str(file_path),
                'ocr_engine': engine,
                'enhancement_used': enhance_images,
                'llm_used': self.use_llm,
                'ocr_text_length': len(ocr_text),
                'trcloud_format': trcloud_format or {},
                'processed_at': datetime.now().isoformat()
            },
            'raw_ocr_text': ocr_text,
            'parsed_data': parsed_data,
            'validation': self.parser.validate_parsed_data(parsed_data)
        }
        
        # สร้างไฟล์ผลลัพธ์ (JSON, TXT และ Excel)
        try:
            text_path, json_path, excel_path = self.save_parsed_results(result, export_to_excel=True)
            result['text_file_path'] = text_path
            result['json_file_path'] = json_path
            result['excel_file_path'] = excel_path
            logger.info(f"All result files created successfully")
        except Exception as e:
            logger.error(f"Error creating result files: {e}")
            result['success'] = False
            result['error'] = str(e)
        
        return result
    
    def apply_trcloud_format(self, parsed_data: dict, trcloud_format: dict) -> dict:
        """
        Apply TRCloud number formatting to parsed invoice data
        
        Args:
            parsed_data: Parsed invoice data dictionary
            trcloud_format: TRCloud format configuration
            
        Returns:
            Updated parsed_data with formatted numbers
        """
        try:
            if not trcloud_format or not parsed_data:
                return parsed_data
            
            from datetime import datetime
            
            format_type = trcloud_format.get('format_type', 'YYMMx')
            digits = trcloud_format.get('digits', 4)
            
            # Current date for formatting
            current_date = datetime.now()
            
            # Generate expected prefix based on format type
            if format_type == "YYx":
                expected_prefix = current_date.strftime("%y")
            elif format_type == "YYMMx":
                expected_prefix = current_date.strftime("%y%m")
            elif format_type == "YYMMDDx":
                expected_prefix = current_date.strftime("%y%m%d")
            else:  # "x" - no prefix
                expected_prefix = ""
            
            # Try to validate and format invoice_number
            invoice_num = parsed_data.get('invoice_number', '')
            if invoice_num and str(invoice_num).isdigit():
                invoice_str = str(invoice_num)
                
                # Check if it matches expected pattern
                if expected_prefix:
                    if invoice_str.startswith(expected_prefix):
                        # Extract running number part
                        running_part = invoice_str[len(expected_prefix):]
                        if running_part.isdigit():
                            # Reformat with correct digits
                            formatted_running = running_part.zfill(digits)
                            formatted_number = f"{expected_prefix}{formatted_running}"
                            parsed_data['invoice_number'] = formatted_number
                            logger.info(f"TRCloud format applied: {invoice_num} -> {formatted_number}")
                else:
                    # No prefix, just format digits
                    if invoice_str.isdigit():
                        formatted_number = invoice_str.zfill(digits)
                        parsed_data['invoice_number'] = formatted_number
                        logger.info(f"TRCloud format applied: {invoice_num} -> {formatted_number}")
            
            # Add TRCloud metadata to parsed data
            parsed_data['trcloud_format_applied'] = True
            parsed_data['trcloud_expected_prefix'] = expected_prefix
            parsed_data['trcloud_digits'] = digits
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error applying TRCloud format: {e}")
            return parsed_data
    
    def save_parsed_results(self, parsed_result: dict, output_filename: str = None, 
                           export_to_excel: bool = True) -> tuple:
        """
        บันทึกผลลัพธ์ที่แยกแล้วเป็นไฟล์และส่งออกไปยัง Excel
        
        Args:
            parsed_result: ผลลัพธ์จาก process_and_parse_invoice
            output_filename: ชื่อไฟล์ที่ต้องการ (optional)
            export_to_excel: ส่งออกไปยัง Excel หรือไม่
            
        Returns:
            Tuple ของ (text_file_path, json_file_path, excel_file_path)
        """
        from datetime import datetime
        import json
        
        # Generate filename if not provided
        if output_filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            source_name = Path(parsed_result['metadata']['source_file']).stem
            output_filename = f"{source_name}_parsed_{timestamp}"
        
        # Save raw OCR text
        text_path = self.output_dir / f"{output_filename}.txt"
        with open(text_path, 'w', encoding='utf-8') as f:
            f.write(parsed_result['raw_ocr_text'])
        
        # Save structured data as JSON
        json_path = self.output_dir / f"{output_filename}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(parsed_result, f, ensure_ascii=False, indent=2, default=str)
        
        excel_path = ""
        if export_to_excel:
            try:
                from excel_exporter import ExcelExporter
                exporter = ExcelExporter()
                excel_path = exporter.append_to_excel(parsed_result)
                logger.info(f"Data exported to Excel: {excel_path}")
            except Exception as e:
                logger.warning(f"Failed to export to Excel: {e}")
                excel_path = ""
        
        logger.info(f"Results saved to: {text_path}, {json_path}" + 
                   (f", and {excel_path}" if excel_path else ""))
        return str(text_path), str(json_path), excel_path
    
    def save_results(self, text: str, output_filename: str) -> str:
        """
        Save extracted text to file
        
        Args:
            text: Extracted text content
            output_filename: Output filename
            
        Returns:
            Path to saved file
        """
        output_path = self.output_dir / output_filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(text)
        
        logger.info(f"Results saved to: {output_path}")
        return str(output_path)


def main():
    """Example usage of the DocumentOCR system"""
    
    # Initialize OCR system
    ocr = DocumentOCR()
    
    # Test with files in input directory
    input_dir = Path(__file__).parent / "input"
    
    if input_dir.exists():
        for file_path in input_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in ['.pdf', '.png', '.jpg', '.jpeg']:
                try:
                    print(f"\n{'='*50}")
                    print(f"Processing: {file_path.name}")
                    print(f"{'='*50}")
                    
                    # Process file
                    text = ocr.process_file(str(file_path))
                    
                    # Save results
                    output_filename = f"{file_path.stem}_ocr_result.txt"
                    ocr.save_results(text, output_filename)
                    
                    # Print preview
                    print("Extracted text preview:")
                    print("-" * 30)
                    print(text[:500] + "..." if len(text) > 500 else text)
                    
                except Exception as e:
                    print(f"Error processing {file_path.name}: {e}")
    else:
        print("No input directory found. Please create an 'input' folder and add PDF/image files.")


if __name__ == "__main__":
    main()
