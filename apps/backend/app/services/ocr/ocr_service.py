"""OCR service for extracting text from images and PDFs."""

from typing import Dict, Any, Optional, TYPE_CHECKING
from PIL import Image
import pytesseract
from pdf2image import convert_from_bytes
import io
import os
from pathlib import Path

if TYPE_CHECKING:
    from PIL.Image import Image as PILImage


class OCRService:
    """Service for extracting text from images and PDF documents using Tesseract OCR."""
    
    def __init__(self):
        """Initialize OCR service with optional tesseract path configuration."""
        # Try to detect tesseract path if not in PATH
        # This handles macOS Homebrew installations
        if os.name == 'posix':  # macOS/Linux
            possible_paths = [
                '/opt/homebrew/bin/tesseract',  # macOS Apple Silicon
                '/usr/local/bin/tesseract',  # macOS Intel / Linux
                '/usr/bin/tesseract',  # Linux standard
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break
    
    def extract_text(
        self,
        file_bytes: bytes,
        filename: str,
        language: str = 'eng'
    ) -> Dict[str, Any]:
        """
        Extract text from image or PDF file.
        
        Args:
            file_bytes: File content as bytes
            filename: Original filename (used to determine file type)
            language: Tesseract language code (default: 'eng')
            
        Returns:
            Dictionary with:
            - text: Extracted text
            - confidence: Average confidence score (0-100)
            - language: Language used for OCR
            - word_count: Number of words extracted
            - file_type: Detected file type
            - error: Error message if processing failed
            
        Raises:
            ValueError: If file format is not supported
            RuntimeError: If Tesseract is not installed or OCR fails
        """
        try:
            # Determine file type from extension
            file_ext = Path(filename).suffix.lower()
            
            if file_ext == '.pdf':
                return self._extract_from_pdf(file_bytes, language)
            elif file_ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif']:
                return self._extract_from_image(file_bytes, language)
            else:
                return {
                    "text": "",
                    "confidence": 0.0,
                    "language": language,
                    "word_count": 0,
                    "file_type": file_ext,
                    "error": f"Unsupported file format: {file_ext}"
                }
        except Exception as e:
            return {
                "text": "",
                "confidence": 0.0,
                "language": language,
                "word_count": 0,
                "file_type": file_ext if 'file_ext' in locals() else "unknown",
                "error": f"OCR processing failed: {str(e)}"
            }
    
    def _extract_from_image(
        self,
        image_bytes: bytes,
        language: str = 'eng'
    ) -> Dict[str, Any]:
        """Extract text from image bytes."""
        try:
            # Open image from bytes
            image = Image.open(io.BytesIO(image_bytes))
            
            # Convert to RGB if needed (required for some formats)
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extract text using Tesseract
            text = pytesseract.image_to_string(image, lang=language)
            
            # Get confidence data
            data = pytesseract.image_to_data(image, lang=language, output_type=pytesseract.Output.DICT)
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Count words
            word_count = len(text.split())
            
            return {
                "text": text.strip(),
                "confidence": round(avg_confidence, 2),
                "language": language,
                "word_count": word_count,
                "file_type": "image",
                "error": None
            }
        except pytesseract.TesseractNotFoundError:
            raise RuntimeError(
                "Tesseract OCR is not installed. "
                "Please install it following instructions in docs/TESSERACT_SETUP.md"
            )
        except Exception as e:
            raise RuntimeError(f"Image OCR processing failed: {str(e)}")
    
    def _extract_from_pdf(
        self,
        pdf_bytes: bytes,
        language: str = 'eng'
    ) -> Dict[str, Any]:
        """Extract text from PDF by converting pages to images."""
        try:
            # Convert PDF pages to images
            images = convert_from_bytes(pdf_bytes)
            
            if not images:
                return {
                    "text": "",
                    "confidence": 0.0,
                    "language": language,
                    "word_count": 0,
                    "file_type": "pdf",
                    "error": "PDF conversion produced no images"
                }
            
            # Extract text from each page
            all_text = []
            all_confidences = []
            
            for image in images:
                # Convert to RGB if needed
                if image.mode != 'RGB':
                    image = image.convert('RGB')
                
                # Extract text
                page_text = pytesseract.image_to_string(image, lang=language)
                all_text.append(page_text)
                
                # Get confidence
                data = pytesseract.image_to_data(image, lang=language, output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                if confidences:
                    all_confidences.extend(confidences)
            
            # Combine all text
            combined_text = "\n\n".join(all_text)
            
            # Calculate average confidence
            avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
            
            # Count words
            word_count = len(combined_text.split())
            
            return {
                "text": combined_text.strip(),
                "confidence": round(avg_confidence, 2),
                "language": language,
                "word_count": word_count,
                "file_type": "pdf",
                "pages": len(images),
                "error": None
            }
        except Exception as e:
            # Check if it's a missing dependency error
            if "poppler" in str(e).lower() or "pdftoppm" in str(e).lower():
                raise RuntimeError(
                    "Poppler is not installed. "
                    "Please install it following instructions in docs/TESSERACT_SETUP.md"
                )
            raise RuntimeError(f"PDF OCR processing failed: {str(e)}")
    
    def extract_text_with_preprocessing(
        self,
        file_bytes: bytes,
        filename: str,
        language: str = 'eng',
        enhance_contrast: bool = False,
        grayscale: bool = False
    ) -> Dict[str, Any]:
        """
        Extract text with optional image preprocessing for better accuracy.
        
        Args:
            file_bytes: File content as bytes
            filename: Original filename
            language: Tesseract language code
            enhance_contrast: Apply contrast enhancement
            grayscale: Convert to grayscale before OCR
            
        Returns:
            Same format as extract_text()
        """
        try:
            file_ext = Path(filename).suffix.lower()
            
            if file_ext == '.pdf':
                # For PDFs, convert to images first, then preprocess
                images = convert_from_bytes(file_bytes)
                if not images:
                    return {
                        "text": "",
                        "confidence": 0.0,
                        "language": language,
                        "word_count": 0,
                        "file_type": "pdf",
                        "error": "PDF conversion produced no images"
                    }
                
                # Process each page with preprocessing
                all_text = []
                all_confidences = []
                
                for image in images:
                    processed_image = self._preprocess_image(image, enhance_contrast, grayscale)
                    page_text = pytesseract.image_to_string(processed_image, lang=language)
                    all_text.append(page_text)
                    
                    data = pytesseract.image_to_data(processed_image, lang=language, output_type=pytesseract.Output.DICT)
                    confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                    if confidences:
                        all_confidences.extend(confidences)
                
                combined_text = "\n\n".join(all_text)
                avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0
                
                return {
                    "text": combined_text.strip(),
                    "confidence": round(avg_confidence, 2),
                    "language": language,
                    "word_count": len(combined_text.split()),
                    "file_type": "pdf",
                    "pages": len(images),
                    "error": None
                }
            
            elif file_ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif']:
                # For images, preprocess then extract
                image = Image.open(io.BytesIO(file_bytes))
                processed_image = self._preprocess_image(image, enhance_contrast, grayscale)
                
                text = pytesseract.image_to_string(processed_image, lang=language)
                data = pytesseract.image_to_data(processed_image, lang=language, output_type=pytesseract.Output.DICT)
                confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
                avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
                
                return {
                    "text": text.strip(),
                    "confidence": round(avg_confidence, 2),
                    "language": language,
                    "word_count": len(text.split()),
                    "file_type": "image",
                    "error": None
                }
            else:
                return {
                    "text": "",
                    "confidence": 0.0,
                    "language": language,
                    "word_count": 0,
                    "file_type": file_ext,
                    "error": f"Unsupported file format: {file_ext}"
                }
        except Exception as e:
            return {
                "text": "",
                "confidence": 0.0,
                "language": language,
                "word_count": 0,
                "file_type": file_ext if 'file_ext' in locals() else "unknown",
                "error": f"OCR processing with preprocessing failed: {str(e)}"
            }
    
    def _preprocess_image(
        self,
        image: "Image.Image",
        enhance_contrast: bool = False,
        grayscale: bool = False
    ) -> "Image.Image":
        """
        Preprocess image for better OCR accuracy.
        
        Args:
            image: PIL Image object
            enhance_contrast: Apply contrast enhancement
            grayscale: Convert to grayscale
            
        Returns:
            Preprocessed PIL Image
        """
        # Convert to RGB if needed
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Convert to grayscale if requested (often improves OCR)
        if grayscale:
            image = image.convert('L')
            # Convert back to RGB for consistency (Tesseract works better with RGB)
            image = image.convert('RGB')
        
        # Enhance contrast if requested
        if enhance_contrast:
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)  # Increase contrast by 50%
        
        return image

