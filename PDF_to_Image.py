import os
import sys
from pathlib import Path
from typing import List, Optional
import logging
import shutil
from pdf2image import convert_from_path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFToImageConverter:
    """
    PDF to Image converter system
    Focused on converting PDF files to high-quality images for further processing
    """
    
    def __init__(self, poppler_path: Optional[str] = None, clean_previous: bool = True):
        """
        Initialize PDF to Image converter
        
        Args:
            poppler_path: Path to poppler binaries (if not in system PATH)
            clean_previous: If True, clean previous outputs before starting
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
        
        if clean_previous:
            self.clean_previous_outputs()
        
        self.output_dir.mkdir(exist_ok=True)
        self.tmp_dir.mkdir(exist_ok=True)
    
    def clean_previous_outputs(self):
        """Clean previous output folders to start fresh (only processed_images)"""
        try:
            # Only clean processed_images, not the PDF conversion outputs
            dirs_to_clean = [
                self.base_path / "processed_images"
            ]
            
            for dir_path in dirs_to_clean:
                if dir_path.exists():
                    logger.info(f"Cleaning previous outputs from: {dir_path}")
                    shutil.rmtree(dir_path)
                    logger.info(f"Cleaned: {dir_path}")
            
            logger.info("Previous processed images cleaned successfully")
            
        except Exception as e:
            logger.warning(f"Error cleaning previous outputs: {e}")
    
    def clean_specific_output(self, output_name: str):
        """
        Clean a specific output folder
        
        Args:
            output_name: Name of the output folder to clean
        """
        try:
            output_path = self.output_dir / output_name
            if output_path.exists():
                logger.info(f"Cleaning specific output: {output_path}")
                shutil.rmtree(output_path)
                logger.info(f"Cleaned: {output_path}")
                
        except Exception as e:
            logger.error(f"Error cleaning output {output_name}: {e}")
    
    def convert_pdf_to_images(
        self, 
        pdf_path: str, 
        output_folder: Optional[str] = None,
        dpi: int = 200,
        output_format: str = 'PNG'
    ) -> List[str]:
        """
        Convert PDF pages to high-quality images
        
        Args:
            pdf_path: Path to the PDF file
            output_folder: Folder to save converted images (optional)
            dpi: Resolution for conversion (higher = better quality)
            output_format: Image format ('PNG', 'JPEG')
            
        Returns:
            List of paths to converted image files
        """
        try:
            pdf_file = Path(pdf_path)
            if not pdf_file.exists():
                raise FileNotFoundError(f"PDF file not found: {pdf_file}")
            
            logger.info(f"Starting PDF conversion: {pdf_file.name}")
            logger.info(f"Settings - DPI: {dpi}, Format: {output_format}")
            
            # Set output folder
            if output_folder is None:
                output_folder_path = self.output_dir / f"{pdf_file.stem}_images"
            else:
                output_folder_path = Path(output_folder)
            output_folder_path.mkdir(parents=True, exist_ok=True)
            
            # Convert PDF to images
            convert_kwargs = {
                'dpi': dpi,
                'fmt': output_format.lower(),  # Use 'fmt' instead of 'output_format'
                'thread_count': 1  # Conservative for stability
            }
            
            if self.poppler_path:
                convert_kwargs['poppler_path'] = self.poppler_path
            
            logger.info("Converting PDF pages to images...")
            pages = convert_from_path(str(pdf_file), **convert_kwargs)
            
            # Save images and collect paths
            image_paths = []
            file_extension = output_format.lower()
            
            for i, page in enumerate(pages, 1):
                image_filename = f"page_{i:03d}.{file_extension}"
                image_path = output_folder_path / image_filename
                
                # Save with appropriate quality settings
                if output_format.upper() == 'JPEG':
                    page.save(str(image_path), 'JPEG', quality=95, optimize=True)
                else:  # PNG
                    page.save(str(image_path), 'PNG', optimize=True)
                
                image_paths.append(str(image_path))
                logger.info(f"Saved page {i}: {image_filename} ({page.size[0]}x{page.size[1]} pixels)")
            
            logger.info(f"Successfully converted {len(pages)} pages to {output_folder_path}")
            logger.info(f"Total images created: {len(image_paths)}")
            
            return image_paths
            
        except Exception as e:
            logger.error(f"Error converting PDF to images: {str(e)}")
            raise
    
    def get_pdf_info(self, pdf_path: str) -> dict:
        """
        Get basic information about the PDF file
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary with PDF information
        """
        try:
            pdf_file = Path(pdf_path)
            if not pdf_file.exists():
                raise FileNotFoundError(f"PDF file not found: {pdf_file}")
            
            # Get file size
            file_size = pdf_file.stat().st_size
            
            # Try to get page count using pdf2image
            try:
                # Quick conversion to count pages
                convert_kwargs = {'dpi': 72}  # Low DPI for quick count
                if self.poppler_path:
                    convert_kwargs['poppler_path'] = self.poppler_path
                
                pages = convert_from_path(str(pdf_file), **convert_kwargs)
                page_count = len(pages)
                
                # Get dimensions from first page
                if pages:
                    first_page = pages[0]
                    width, height = first_page.size
                else:
                    width, height = 0, 0
                
            except Exception as e:
                logger.warning(f"Could not get page info: {e}")
                page_count = 0
                width, height = 0, 0
            
            info = {
                'filename': pdf_file.name,
                'file_path': str(pdf_file),
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'page_count': page_count,
                'first_page_dimensions': (width, height)
            }
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting PDF info: {str(e)}")
            return {}
    
    def convert_multiple_pdfs(
        self, 
        pdf_folder: str, 
        dpi: int = 300,
        output_format: str = 'PNG'
    ) -> dict:
        """
        Convert multiple PDF files in a folder
        
        Args:
            pdf_folder: Folder containing PDF files
            dpi: Resolution for conversion
            output_format: Image format
            
        Returns:
            Dictionary with results for each PDF
        """
        results = {}
        pdf_folder_path = Path(pdf_folder)
        
        if not pdf_folder_path.exists():
            raise FileNotFoundError(f"PDF folder not found: {pdf_folder_path}")
        
        # Find all PDF files
        pdf_files = list(pdf_folder_path.glob("*.pdf")) + list(pdf_folder_path.glob("*.PDF"))
        
        if not pdf_files:
            logger.warning(f"No PDF files found in: {pdf_folder_path}")
            return results
        
        logger.info(f"Found {len(pdf_files)} PDF files to convert")
        
        for pdf_file in pdf_files:
            try:
                logger.info(f"\n{'='*50}")
                logger.info(f"Processing: {pdf_file.name}")
                logger.info(f"{'='*50}")
                
                # Convert PDF
                image_paths = self.convert_pdf_to_images(
                    str(pdf_file), 
                    dpi=dpi,
                    output_format=output_format
                )
                
                results[pdf_file.name] = {
                    'success': True,
                    'image_paths': image_paths,
                    'image_count': len(image_paths),
                    'error': None
                }
                
            except Exception as e:
                logger.error(f"Failed to convert {pdf_file.name}: {e}")
                results[pdf_file.name] = {
                    'success': False,
                    'image_paths': [],
                    'image_count': 0,
                    'error': str(e)
                }
        
        return results
    
    def print_conversion_summary(self, results: dict):
        """
        Print a summary of conversion results
        
        Args:
            results: Results dictionary from convert_multiple_pdfs
        """
        successful = sum(1 for r in results.values() if r['success'])
        failed = len(results) - successful
        total_images = sum(r['image_count'] for r in results.values())
        
        print(f"\n{'='*60}")
        print(f"CONVERSION SUMMARY")
        print(f"{'='*60}")
        print(f"Total PDFs processed: {len(results)}")
        print(f"Successful conversions: {successful}")
        print(f"Failed conversions: {failed}")
        print(f"Total images created: {total_images}")
        
        if failed > 0:
            print(f"\nFailed conversions:")
            for filename, result in results.items():
                if not result['success']:
                    print(f"  - {filename}: {result['error']}")
        
        if successful > 0:
            print(f"\nSuccessful conversions:")
            for filename, result in results.items():
                if result['success']:
                    print(f"  - {filename}: {result['image_count']} images")


def main():
    """Example usage of the PDF to Image converter"""
    
    # Initialize converter
    converter = PDFToImageConverter()
    
    # Check input directory
    input_dir = Path(__file__).parent / "input"
    
    if not input_dir.exists():
        print("No input directory found. Please create an 'input' folder and add PDF files.")
        return
    
    # Process all PDFs in input directory
    try:
        print("PDF to Image Converter")
        print("=" * 40)
        
        # Convert all PDFs
        results = converter.convert_multiple_pdfs(
            str(input_dir),
            dpi=300,  # High quality
            output_format='PNG'  # PNG for best quality
        )
        
        # Print summary
        converter.print_conversion_summary(results)
        
        # Show individual file info
        pdf_files = list(input_dir.glob("*.pdf")) + list(input_dir.glob("*.PDF"))
        if pdf_files:
            print(f"\nPDF File Information:")
            print("-" * 40)
            for pdf_file in pdf_files:
                info = converter.get_pdf_info(str(pdf_file))
                if info:
                    print(f"File: {info['filename']}")
                    print(f"  Size: {info['file_size_mb']} MB")
                    print(f"  Pages: {info['page_count']}")
                    if info['first_page_dimensions'][0] > 0:
                        print(f"  Dimensions: {info['first_page_dimensions'][0]}x{info['first_page_dimensions'][1]} pixels")
                    print()
    
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()