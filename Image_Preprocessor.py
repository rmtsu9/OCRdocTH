import os
import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional
import logging
from PIL import Image, ImageEnhance
import matplotlib.pyplot as plt
import shutil

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ImagePreprocessor:
    """
    Image preprocessing system for Thai tax documents
    Optimized to enhance image quality before OCR processing
    """
    
    def __init__(self):
        """Initialize the image preprocessor"""
        self.base_path = Path(__file__).parent
        self.processed_dir = self.base_path / "outputs" / "processed_images"
        self.processed_dir.mkdir(exist_ok=True)
    
    def clean_previous_outputs(self):
        """Clean previous output folders to start fresh"""
        try:
            # List of directories to clean
            dirs_to_clean = [
                self.base_path / "processed_images",
                self.base_path / "outputs",
                self.base_path / "tmp"
            ]
            
            for dir_path in dirs_to_clean:
                if dir_path.exists():
                    logger.info(f"Cleaning previous outputs from: {dir_path}")
                    shutil.rmtree(dir_path)
                    logger.info(f"Cleaned: {dir_path}")
            
            logger.info("Previous outputs cleaned successfully")
            
        except Exception as e:
            logger.warning(f"Error cleaning previous outputs: {e}")
    
    def clean_specific_folder(self, folder_path: str):
        """
        Clean a specific folder
        
        Args:
            folder_path: Path to folder to clean
        """
        try:
            folder = Path(folder_path)
            if folder.exists():
                logger.info(f"Cleaning folder: {folder}")
                shutil.rmtree(folder)
                folder.mkdir(parents=True, exist_ok=True)
                logger.info(f"Folder cleaned and recreated: {folder}")
            else:
                logger.info(f"Folder doesn't exist, creating: {folder}")
                folder.mkdir(parents=True, exist_ok=True)
                
        except Exception as e:
            logger.error(f"Error cleaning folder {folder_path}: {e}")
    
    def enhance_image_quality(self, image_path: str, output_path: Optional[str] = None, gentle_mode: bool = True) -> str:
        """
        Enhance overall image quality with gentle processing for documents
        
        Args:
            image_path: Path to input image
            output_path: Path to save enhanced image
            gentle_mode: If True, use gentle enhancement suitable for documents
            
        Returns:
            Path to enhanced image
        """
        try:
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            logger.info(f"Enhancing image quality: {Path(image_path).name} (gentle_mode: {gentle_mode})")
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            if gentle_mode:
                # Gentle enhancement for document images - OPTIMIZED FOR CLEAR TEXT
                
                # 1. Minimal denoising to preserve text sharpness
                denoised = cv2.medianBlur(gray, 3)
                
                # 2. Very mild contrast enhancement
                clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
                enhanced = clahe.apply(denoised)
                
                # 3. Unsharp mask for better text definition
                gaussian = cv2.GaussianBlur(enhanced, (0, 0), 2.0)
                result = cv2.addWeighted(enhanced, 1.5, gaussian, -0.5, 0)
                
                # 4. Slight brightness adjustment if needed
                result = cv2.convertScaleAbs(result, alpha=1.1, beta=5)
                
            else:
                # Original stronger enhancement
                denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                enhanced = clahe.apply(denoised)
                blurred = cv2.GaussianBlur(enhanced, (1, 1), 0)
                kernel_sharpening = np.array([[-1, -1, -1],
                                            [-1, 9, -1],
                                            [-1, -1, -1]])
                result = cv2.filter2D(blurred, -1, kernel_sharpening)
            
            # Save enhanced image
            if output_path is None:
                input_path = Path(image_path)
                mode_suffix = "_gentle" if gentle_mode else "_enhanced"
                output_path = self.processed_dir / f"{input_path.stem}{mode_suffix}{input_path.suffix}"
            
            cv2.imwrite(str(output_path), result)
            logger.info(f"Enhanced image saved: {output_path}")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error enhancing image quality: {str(e)}")
            return image_path
    
    def detect_rotation_angle(self, image: np.ndarray) -> float:
        """
        Detect rotation angle using multiple methods for robustness
        
        Args:
            image: Grayscale image
            
        Returns:
            Rotation angle in degrees
        """
        # Method 1: Line detection using Hough Transform
        edges = cv2.Canny(image, 50, 150, apertureSize=3)
        lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=100)
        
        angles_hough = []
        if lines is not None:
            for rho, theta in lines[:50]:  # Use first 50 lines
                angle = np.degrees(theta) - 90
                if abs(angle) < 45:  # Filter reasonable angles
                    angles_hough.append(angle)
        
        # Method 2: Text line detection using morphology
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 1))
        morph = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
        
        contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        angles_morph = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 500:  # Filter by area
                rect = cv2.minAreaRect(contour)
                angle = rect[2]
                
                # Normalize angle to [-45, 45]
                if angle < -45:
                    angle += 90
                elif angle > 45:
                    angle -= 90
                
                if abs(angle) < 45:
                    angles_morph.append(angle)
        
        # Combine angles from both methods
        all_angles = angles_hough + angles_morph
        
        if not all_angles:
            return 0.0
        
        # Use histogram to find dominant angle
        hist, bins = np.histogram(all_angles, bins=90, range=(-45, 45))
        dominant_bin = np.argmax(hist)
        dominant_angle = (bins[dominant_bin] + bins[dominant_bin + 1]) / 2
        
        return dominant_angle
    
    def correct_orientation(self, image_path: str, output_path: Optional[str] = None, manual_angle: Optional[float] = None) -> str:
        """
        Detect and correct image orientation/rotation with improved algorithm
        
        Args:
            image_path: Path to input image
            output_path: Path to save corrected image
            manual_angle: Manual rotation angle (if None, auto-detect)
            
        Returns:
            Path to orientation-corrected image
        """
        try:
            # Read image
            image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            logger.info(f"Correcting orientation: {Path(image_path).name}")
            
            if manual_angle is not None:
                rotation_angle = manual_angle
                logger.info(f"Using manual rotation angle: {rotation_angle:.2f} degrees")
            else:
                # Auto-detect rotation angle
                rotation_angle = self.detect_rotation_angle(image)
                logger.info(f"Detected rotation angle: {rotation_angle:.2f} degrees")
            
            # Apply rotation if significant
            if abs(rotation_angle) > 0.1:
                h, w = image.shape
                center = (w // 2, h // 2)
                
                # Create rotation matrix
                rotation_matrix = cv2.getRotationMatrix2D(center, rotation_angle, 1.0)
                
                # Calculate new image size to prevent cropping
                cos_angle = abs(rotation_matrix[0, 0])
                sin_angle = abs(rotation_matrix[0, 1])
                new_w = int((h * sin_angle) + (w * cos_angle))
                new_h = int((h * cos_angle) + (w * sin_angle))
                
                # Adjust translation to center the rotated image
                rotation_matrix[0, 2] += (new_w / 2) - center[0]
                rotation_matrix[1, 2] += (new_h / 2) - center[1]
                
                # Apply rotation
                rotated = cv2.warpAffine(image, rotation_matrix, (new_w, new_h), 
                                       flags=cv2.INTER_CUBIC, 
                                       borderMode=cv2.BORDER_CONSTANT,
                                       borderValue=255)  # White background
                
                logger.info(f"Image rotated by {rotation_angle:.2f} degrees")
            else:
                rotated = image
                logger.info("No significant rotation detected")
            
            # Save corrected image
            if output_path is None:
                input_path = Path(image_path)
                output_path = self.processed_dir / f"{input_path.stem}_oriented{input_path.suffix}"
            
            cv2.imwrite(str(output_path), rotated)
            logger.info(f"Orientation corrected image saved: {output_path}")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error correcting orientation: {str(e)}")
            return image_path
    
    def binarize_image(self, image_path: str, output_path: Optional[str] = None, gentle_mode: bool = True) -> str:
        """
        Convert image to binary (black and white) for better OCR with gentle processing
        
        Args:
            image_path: Path to input image
            output_path: Path to save binarized image
            gentle_mode: If True, use gentle binarization to preserve details
            
        Returns:
            Path to binarized image
        """
        try:
            # Read image
            image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            logger.info(f"Binarizing image: {Path(image_path).name} (gentle_mode: {gentle_mode})")
            
            if gentle_mode:
                # Gentle binarization for document preservation
                
                # Use larger block size for smoother threshold
                adaptive_thresh = cv2.adaptiveThreshold(
                    image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                    cv2.THRESH_BINARY, 25, 8  # Larger block, smaller C value
                )
                
                # Apply minimal morphology to preserve details
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 1))
                result = cv2.morphologyEx(adaptive_thresh, cv2.MORPH_CLOSE, kernel)
                
                # Very light noise removal
                result = cv2.medianBlur(result, 1)
                
            else:
                # Original stronger binarization
                adaptive_thresh = cv2.adaptiveThreshold(
                    image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                    cv2.THRESH_BINARY, 15, 10
                )
                
                _, otsu_thresh = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                diff = cv2.absdiff(adaptive_thresh, otsu_thresh)
                combined = np.where(diff > 30, adaptive_thresh, otsu_thresh)
                
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
                cleaned = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel)
                result = cv2.medianBlur(cleaned, 3)
            
            # Save binarized image
            if output_path is None:
                input_path = Path(image_path)
                mode_suffix = "_gentle_binary" if gentle_mode else "_binary"
                output_path = self.processed_dir / f"{input_path.stem}{mode_suffix}{input_path.suffix}"
            
            cv2.imwrite(str(output_path), result)
            logger.info(f"Binarized image saved: {output_path}")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error binarizing image: {str(e)}")
            return image_path
    
    def detect_text_regions(self, image_path: str) -> List[Tuple[int, int, int, int]]:
        """
        Detect text regions in the image (for layout analysis)
        
        Args:
            image_path: Path to input image
            
        Returns:
            List of bounding boxes (x, y, width, height) for text regions
        """
        try:
            # Read image
            image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if image is None:
                raise ValueError(f"Could not load image: {image_path}")
            
            logger.info(f"Detecting text regions: {Path(image_path).name}")
            
            # Apply binary threshold
            _, binary = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            
            # Create kernels for morphological operations
            # Horizontal kernel to detect horizontal text lines
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
            horizontal_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horizontal_kernel)
            
            # Vertical kernel to detect vertical elements
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
            vertical_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vertical_kernel)
            
            # Combine horizontal and vertical elements
            combined = cv2.addWeighted(horizontal_lines, 0.5, vertical_lines, 0.5, 0.0)
            
            # Find contours for text regions
            contours, _ = cv2.findContours(combined, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter and sort text regions
            text_regions = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 500:  # Filter small regions
                    x, y, w, h = cv2.boundingRect(contour)
                    # Filter by aspect ratio (typical text regions)
                    aspect_ratio = w / h
                    if 0.1 < aspect_ratio < 20:
                        text_regions.append((x, y, w, h))
            
            # Sort regions by vertical position (top to bottom)
            text_regions.sort(key=lambda region: region[1])
            
            logger.info(f"Detected {len(text_regions)} text regions")
            return text_regions
            
        except Exception as e:
            logger.error(f"Error detecting text regions: {str(e)}")
            return []
    
    def preprocess_for_ocr(self, image_path: str, output_path: Optional[str] = None, gentle_mode: bool = True) -> str:
        """
        Complete preprocessing pipeline for OCR with gentle processing option
        
        Args:
            image_path: Path to input image
            output_path: Path to save final processed image
            gentle_mode: If True, use gentle processing to preserve document details
            
        Returns:
            Path to final processed image ready for OCR
        """
        try:
            logger.info(f"Starting OCR preprocessing pipeline: {Path(image_path).name} (gentle_mode: {gentle_mode})")
            
            if gentle_mode:
                # Gentle processing for documents
                # Step 1: Light enhancement only
                enhanced_path = self.enhance_image_quality(image_path, gentle_mode=True)
                
                # Step 2: Skip orientation correction for now (causes problems)
                oriented_path = enhanced_path
                
                # Step 3: Gentle binarization
                binary_path = self.binarize_image(oriented_path, gentle_mode=True)
                
            else:
                # Original stronger processing
                enhanced_path = self.enhance_image_quality(image_path, gentle_mode=False)
                oriented_path = self.correct_orientation(enhanced_path)
                binary_path = self.binarize_image(oriented_path, gentle_mode=False)
            
            # Final output path
            if output_path is None:
                input_path = Path(image_path)
                mode_suffix = "_gentle_final" if gentle_mode else "_final"
                output_path = self.processed_dir / f"{input_path.stem}{mode_suffix}{input_path.suffix}"
            
            # Copy final result
            final_image = cv2.imread(binary_path)
            cv2.imwrite(str(output_path), final_image)
            
            logger.info(f"OCR preprocessing completed: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error in OCR preprocessing pipeline: {str(e)}")
            return image_path
    
    def process_pdf_images(self, images_folder: str) -> List[str]:
        """
        Process all images from PDF conversion
        
        Args:
            images_folder: Folder containing images converted from PDF
            
        Returns:
            List of processed image paths ready for OCR
        """
        try:
            images_folder_path = Path(images_folder)
            if not images_folder_path.exists():
                raise FileNotFoundError(f"Images folder not found: {images_folder_path}")
            
            # Find all image files
            image_extensions = ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']
            image_files = []
            for ext in image_extensions:
                image_files.extend(images_folder_path.glob(f"*{ext}"))
                image_files.extend(images_folder_path.glob(f"*{ext.upper()}"))
            
            if not image_files:
                logger.warning(f"No image files found in: {images_folder_path}")
                return []
            
            logger.info(f"Processing {len(image_files)} images for OCR")
            
            processed_images = []
            for i, image_file in enumerate(sorted(image_files), 1):
                logger.info(f"Processing image {i}/{len(image_files)}: {image_file.name}")
                
                # Process each image with gentle mode (default for documents)
                processed_path = self.preprocess_for_ocr(str(image_file), gentle_mode=True)
                processed_images.append(processed_path)
            
            logger.info(f"Completed processing {len(processed_images)} images")
            return processed_images
            
        except Exception as e:
            logger.error(f"Error processing PDF images: {str(e)}")
            return []
    
    def create_processing_summary(self, original_path: str, processed_path: str):
        """
        Create a visual summary showing before and after processing
        
        Args:
            original_path: Path to original image
            processed_path: Path to processed image
        """
        try:
            # Read images
            original = cv2.imread(original_path, cv2.IMREAD_GRAYSCALE)
            processed = cv2.imread(processed_path, cv2.IMREAD_GRAYSCALE)
            
            # Create comparison figure
            fig, axes = plt.subplots(1, 2, figsize=(15, 8))
            
            # Original image
            axes[0].imshow(original, cmap='gray')
            axes[0].set_title('Original Image')
            axes[0].axis('off')
            
            # Processed image
            axes[1].imshow(processed, cmap='gray')
            axes[1].set_title('Processed Image (Ready for OCR)')
            axes[1].axis('off')
            
            plt.tight_layout()
            
            # Save comparison
            comparison_path = self.processed_dir / f"comparison_{Path(original_path).stem}.png"
            plt.savefig(comparison_path, dpi=150, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Processing comparison saved: {comparison_path}")
            
        except Exception as e:
            logger.error(f"Error creating processing summary: {str(e)}")


def main():
    """Process PDF images with gentle preprocessing for OCR"""
    
    print("🔧 Image Preprocessor - Gentle Mode for Thai Tax Documents")
    print("=" * 60)
    
    # Initialize preprocessor
    preprocessor = ImagePreprocessor()
    
    # Check for PDF images to process
    outputs_dir = Path(__file__).parent / "outputs"
    
    if outputs_dir.exists():
        # Find image folders from PDF conversion
        image_folders = [f for f in outputs_dir.iterdir() if f.is_dir() and "images" in f.name]
        
        if image_folders:
            for folder in image_folders:
                print(f"\n📁 Processing images from: {folder.name}")
                print("-" * 40)
                
                # Process all images in folder with gentle mode
                processed_images = preprocessor.process_pdf_images(str(folder))
                
                if processed_images:
                    print(f"✅ Successfully processed {len(processed_images)} images")
                    print(f"📂 Results saved to: {preprocessor.processed_dir}")
                    
                    # Create comparison for first image
                    original_images = list(folder.glob("*.png"))
                    if original_images and processed_images:
                        print("📊 Creating before/after comparison...")
                        preprocessor.create_processing_summary(
                            str(original_images[0]), 
                            processed_images[0]
                        )
                        print("📈 Comparison chart saved")
                else:
                    print("❌ No images were processed")
        else:
            print("❌ No PDF image folders found in outputs directory")
            print("💡 Please run PDF_to_Image.py first to convert PDF files")
    else:
        print("❌ No outputs directory found")
        print("💡 Please run PDF_to_Image.py first to convert PDF files")





if __name__ == "__main__":
    main()