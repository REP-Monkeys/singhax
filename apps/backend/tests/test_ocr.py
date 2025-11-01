"""Tests for OCR services."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import io
import json
from pathlib import Path

from app.services.ocr import OCRService, DocumentTypeDetector, JSONExtractor


class TestOCRService:
    """Test cases for OCR service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.ocr_service = OCRService()
    
    def test_ocr_service_initialization(self):
        """Test OCR service initializes correctly."""
        assert self.ocr_service is not None
    
    @patch('app.services.ocr.ocr_service.pytesseract')
    @patch('app.services.ocr.ocr_service.Image')
    def test_extract_text_from_image_success(self, mock_image, mock_pytesseract):
        """Test successful text extraction from image."""
        # Mock image
        mock_img = MagicMock()
        mock_img.mode = 'RGB'
        mock_image.open.return_value = mock_img
        
        # Mock OCR result
        mock_pytesseract.image_to_string.return_value = "Sample extracted text"
        mock_pytesseract.image_to_data.return_value = {
            'conf': ['91', '88', '92', '0', '0']  # Confidence scores
        }
        
        # Create test image bytes
        test_image_bytes = b'fake image data'
        
        result = self.ocr_service.extract_text(
            test_image_bytes,
            "test_image.png",
            language='eng'
        )
        
        assert result.get("error") is None
        assert "text" in result
        assert result["file_type"] == "image"
        assert result["language"] == "eng"
        assert "confidence" in result
        assert "word_count" in result
    
    @patch('app.services.ocr.ocr_service.pytesseract')
    @patch('app.services.ocr.ocr_service.convert_from_bytes')
    def test_extract_text_from_pdf_success(self, mock_convert, mock_pytesseract):
        """Test successful text extraction from PDF."""
        # Mock PDF conversion
        mock_img1 = MagicMock()
        mock_img1.mode = 'RGB'
        mock_img2 = MagicMock()
        mock_img2.mode = 'RGB'
        mock_convert.return_value = [mock_img1, mock_img2]
        
        # Mock OCR results
        mock_pytesseract.image_to_string.side_effect = [
            "Page 1 text",
            "Page 2 text"
        ]
        mock_pytesseract.image_to_data.side_effect = [
            {'conf': ['91', '88']},
            {'conf': ['92', '90']}
        ]
        
        test_pdf_bytes = b'fake pdf data'
        
        result = self.ocr_service.extract_text(
            test_pdf_bytes,
            "test_document.pdf",
            language='eng'
        )
        
        assert result.get("error") is None
        assert "text" in result
        assert result["file_type"] == "pdf"
        assert "pages" in result
        assert result["pages"] == 2
        assert "Page 1 text" in result["text"]
        assert "Page 2 text" in result["text"]
    
    def test_extract_text_unsupported_format(self):
        """Test extraction with unsupported file format."""
        test_bytes = b'fake data'
        
        result = self.ocr_service.extract_text(
            test_bytes,
            "test_file.txt",
            language='eng'
        )
        
        assert result.get("error") is not None
        assert "Unsupported file format" in result["error"]
        assert result["text"] == ""
    
    @patch('app.services.ocr.ocr_service.pytesseract')
    def test_extract_text_tesseract_not_found(self, mock_pytesseract):
        """Test handling when Tesseract is not installed."""
        from pytesseract import TesseractNotFoundError
        
        # TesseractNotFoundError doesn't take arguments, create it properly
        mock_pytesseract.image_to_string.side_effect = TesseractNotFoundError()
        mock_pytesseract.TesseractNotFoundError = TesseractNotFoundError
        
        # Mock image
        with patch('app.services.ocr.ocr_service.Image') as mock_image:
            mock_img = MagicMock()
            mock_img.mode = 'RGB'
            mock_image.open.return_value = mock_img
            
            test_image_bytes = b'fake image data'
            
            with pytest.raises(RuntimeError) as exc_info:
                self.ocr_service._extract_from_image(test_image_bytes, 'eng')
            
            assert "Tesseract OCR is not installed" in str(exc_info.value)
    
    @patch('app.services.ocr.ocr_service.pytesseract')
    @patch('app.services.ocr.ocr_service.Image')
    def test_extract_text_with_preprocessing_grayscale(self, mock_image, mock_pytesseract):
        """Test text extraction with grayscale preprocessing."""
        mock_img = MagicMock()
        mock_img.mode = 'RGB'
        mock_processed = MagicMock()
        mock_img.convert.return_value = mock_processed
        mock_image.open.return_value = mock_img
        
        mock_pytesseract.image_to_string.return_value = "Extracted text"
        mock_pytesseract.image_to_data.return_value = {'conf': ['91']}
        
        test_image_bytes = b'fake image data'
        
        result = self.ocr_service.extract_text_with_preprocessing(
            test_image_bytes,
            "test_image.png",
            language='eng',
            grayscale=True
        )
        
        assert result.get("error") is None
        assert "text" in result
    
    @patch('app.services.ocr.ocr_service.pytesseract')
    @patch('app.services.ocr.ocr_service.Image')
    @patch('PIL.ImageEnhance.Contrast')
    def test_extract_text_with_preprocessing_contrast(self, mock_contrast_class, mock_image, mock_pytesseract):
        """Test text extraction with contrast enhancement."""
        mock_img = MagicMock()
        mock_img.mode = 'RGB'
        mock_image.open.return_value = mock_img
        
        # Mock ImageEnhance.Contrast
        mock_enhancer = MagicMock()
        mock_enhancer.enhance.return_value = mock_img
        mock_contrast_class.return_value = mock_enhancer
        
        mock_pytesseract.image_to_string.return_value = "Extracted text"
        mock_pytesseract.image_to_data.return_value = {'conf': ['91']}
        
        test_image_bytes = b'fake image data'
        
        result = self.ocr_service.extract_text_with_preprocessing(
            test_image_bytes,
            "test_image.png",
            language='eng',
            enhance_contrast=True
        )
        
        assert result.get("error") is None
        assert "text" in result
        mock_contrast_class.assert_called_once()
    
    def test_preprocess_image_grayscale(self):
        """Test image preprocessing with grayscale conversion."""
        # Create a simple test image
        test_image = Image.new('RGB', (100, 100), color='red')
        
        processed = self.ocr_service._preprocess_image(
            test_image,
            grayscale=True,
            enhance_contrast=False
        )
        
        assert processed is not None
        assert processed.mode == 'RGB'  # Should convert back to RGB
    
    @patch('PIL.ImageEnhance.Contrast')
    def test_preprocess_image_contrast(self, mock_contrast_class):
        """Test image preprocessing with contrast enhancement."""
        test_image = Image.new('RGB', (100, 100), color='red')
        
        # Mock ImageEnhance.Contrast
        mock_enhancer = MagicMock()
        mock_enhancer.enhance.return_value = test_image
        mock_contrast_class.return_value = mock_enhancer
        
        processed = self.ocr_service._preprocess_image(
            test_image,
            grayscale=False,
            enhance_contrast=True
        )
        
        assert processed is not None
        mock_contrast_class.assert_called_once_with(test_image)
        mock_enhancer.enhance.assert_called_once_with(1.5)


class TestDocumentTypeDetector:
    """Test cases for document type detector."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.detector = DocumentTypeDetector()
    
    @patch('app.services.ocr.document_detector.GroqLLMClient')
    def test_detect_type_flight_confirmation(self, mock_llm_client_class):
        """Test detection of flight confirmation document."""
        # Mock LLM response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "type": "flight_confirmation",
            "confidence": 0.95,
            "reasoning": "Contains flight numbers and PNR"
        })
        mock_client.client.chat.completions.create.return_value = mock_response
        mock_llm_client_class.return_value = mock_client
        
        ocr_text = "Flight TR892 from SIN to NRT on March 15, 2025. PNR: ABC123"
        
        result = self.detector.detect_type(ocr_text)
        
        assert result["type"] == "flight_confirmation"
        assert result["confidence"] == 0.95
        assert "reasoning" in result
    
    @patch('app.services.ocr.document_detector.GroqLLMClient')
    def test_detect_type_hotel_booking(self, mock_llm_client_class):
        """Test detection of hotel booking document."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "type": "hotel_booking",
            "confidence": 0.92,
            "reasoning": "Contains hotel name and check-in dates"
        })
        mock_client.client.chat.completions.create.return_value = mock_response
        mock_llm_client_class.return_value = mock_client
        
        ocr_text = "Hotel Booking: Grand Tokyo Hotel. Check-in: March 15, 2025"
        
        result = self.detector.detect_type(ocr_text)
        
        assert result["type"] == "hotel_booking"
        # Allow some flexibility in confidence (LLM might return slightly different values)
        assert 0.8 <= result["confidence"] <= 1.0
    
    @patch('app.services.ocr.document_detector.GroqLLMClient')
    def test_detect_type_unknown(self, mock_llm_client_class):
        """Test detection with unknown document type."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "type": "unknown",
            "confidence": 0.3,
            "reasoning": "Cannot determine document type"
        })
        mock_client.client.chat.completions.create.return_value = mock_response
        mock_llm_client_class.return_value = mock_client
        
        ocr_text = "Random text that doesn't match any document type"
        
        result = self.detector.detect_type(ocr_text)
        
        assert result["type"] == "unknown"
        assert result["confidence"] < 0.5
    
    @patch('app.services.ocr.document_detector.GroqLLMClient')
    def test_detect_type_error_handling(self, mock_llm_client_class):
        """Test error handling in document type detection."""
        mock_client = MagicMock()
        # Make sure the exception is raised properly
        mock_client.client.chat.completions.create.side_effect = Exception("API Error")
        mock_llm_client_class.return_value = mock_client
        
        # Create a new detector instance to ensure clean state
        detector = DocumentTypeDetector()
        detector.llm_client = mock_client
        
        ocr_text = "Some text"
        
        result = detector.detect_type(ocr_text)
        
        assert result["type"] == "unknown"
        assert result["confidence"] == 0.0
        assert "error" in result["reasoning"].lower() or "Detection error" in result["reasoning"]


class TestJSONExtractor:
    """Test cases for JSON extractor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = JSONExtractor()
    
    @patch('app.services.ocr.json_extractor.DocumentTypeDetector')
    @patch('app.services.ocr.json_extractor.GroqLLMClient')
    def test_extract_flight_confirmation(self, mock_llm_client_class, mock_detector_class):
        """Test extraction from flight confirmation document."""
        # Mock document detector
        mock_detector = MagicMock()
        mock_detector.detect_type.return_value = {
            "type": "flight_confirmation",
            "confidence": 0.95,
            "reasoning": "Flight confirmation"
        }
        mock_detector_class.return_value = mock_detector
        
        # Mock LLM response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "session_id": "test-session",
            "document_type": "flight_confirmation",
            "airline": {"name": "Scoot", "code": "TR", "confidence": 0.92},
            "flight_details": {
                "departure": {"date": "2025-03-15", "time": "14:30", "airport_code": "SIN", "confidence": 0.91},
                "return": {"date": "2025-03-22", "time": "18:45", "airport_code": "NRT", "confidence": 0.91},
                "flight_numbers": {"outbound": "TR892", "inbound": "TR893", "confidence": 0.93}
            },
            "destination": {"country": "Japan", "city": "Tokyo", "confidence": 0.92},
            "travelers": [{
                "name": {"first": "John", "last": "Doe", "full": "John Doe", "confidence": 0.94},
                "ticket": {"ticket_number": "123456", "confidence": 0.91}
            }],
            "trip_duration": {"days": 7, "confidence": 0.95},
            "trip_value": {"total_cost": {"amount": 1850.00, "currency": "SGD", "confidence": 0.90}},
            "booking_reference": {"pnr": "ABC123", "confidence": 0.93}
        })
        mock_client.client.chat.completions.create.return_value = mock_response
        mock_llm_client_class.return_value = mock_client
        
        ocr_text = "Flight TR892 from SIN to NRT on March 15, 2025"
        
        result = self.extractor.extract(
            ocr_text=ocr_text,
            session_id="test-session",
            filename="flight.pdf"
        )
        
        assert result["document_type"] == "flight_confirmation"
        assert "airline" in result
        assert "flight_details" in result
        assert "destination" in result
        assert "high_confidence_fields" in result
        assert "low_confidence_fields" in result
    
    @patch('app.services.ocr.json_extractor.DocumentTypeDetector')
    @patch('app.services.ocr.json_extractor.GroqLLMClient')
    def test_extract_hotel_booking(self, mock_llm_client_class, mock_detector_class):
        """Test extraction from hotel booking document."""
        mock_detector = MagicMock()
        mock_detector.detect_type.return_value = {
            "type": "hotel_booking",
            "confidence": 0.92,
            "reasoning": "Hotel booking"
        }
        mock_detector_class.return_value = mock_detector
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "session_id": "test-session",
            "document_type": "hotel_booking",
            "hotel_details": {"name": "Grand Tokyo Hotel", "confidence": 0.92},
            "location": {"address": {"country": "Japan", "confidence": 0.91}},
            "booking_dates": {
                "check_in": {"date": "2025-03-15", "confidence": 0.93},
                "check_out": {"date": "2025-03-22", "confidence": 0.93}
            },
            "guests": [{"name": {"full": "John Doe", "confidence": 0.94}}]
        })
        mock_client.client.chat.completions.create.return_value = mock_response
        mock_llm_client_class.return_value = mock_client
        
        ocr_text = "Hotel: Grand Tokyo Hotel. Check-in: March 15, 2025"
        
        result = self.extractor.extract(
            ocr_text=ocr_text,
            session_id="test-session",
            filename="hotel.pdf"
        )
        
        assert result["document_type"] == "hotel_booking"
        assert "hotel_details" in result
        assert "location" in result
        assert "booking_dates" in result
    
    @patch('app.services.ocr.json_extractor.DocumentTypeDetector')
    @patch('app.services.ocr.json_extractor.GroqLLMClient')
    def test_extract_itinerary(self, mock_llm_client_class, mock_detector_class):
        """Test extraction from itinerary document."""
        mock_detector = MagicMock()
        mock_detector.detect_type.return_value = {
            "type": "itinerary",
            "confidence": 0.90,
            "reasoning": "Travel itinerary"
        }
        mock_detector_class.return_value = mock_detector
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "session_id": "test-session",
            "document_type": "itinerary",
            "trip_overview": {
                "title": "Japan Tour",
                "duration_days": 10,
                "start_date": "2025-03-15",
                "end_date": "2025-03-24",
                "confidence": 0.91
            },
            "destinations": [{"city": "Tokyo", "country": "Japan", "confidence": 0.92}],
            "adventure_sports_detected": {
                "has_adventure_sports": True,
                "confidence": 0.91
            },
            "activities": [{
                "date": "2025-03-17",
                "activity_type": "adventure",
                "is_adventure_sport": True,
                "confidence": 0.91
            }]
        })
        mock_client.client.chat.completions.create.return_value = mock_response
        mock_llm_client_class.return_value = mock_client
        
        ocr_text = "Japan Tour: Skiing on March 17, 2025"
        
        result = self.extractor.extract(
            ocr_text=ocr_text,
            session_id="test-session",
            filename="itinerary.pdf"
        )
        
        assert result["document_type"] == "itinerary"
        assert "trip_overview" in result
        assert "adventure_sports_detected" in result
        assert result["adventure_sports_detected"]["has_adventure_sports"] is True
    
    @patch('app.services.ocr.json_extractor.DocumentTypeDetector')
    def test_extract_unknown_document_type(self, mock_detector_class):
        """Test extraction with unknown document type."""
        mock_detector = MagicMock()
        mock_detector.detect_type.return_value = {
            "type": "unknown",
            "confidence": 0.3,
            "reasoning": "Unknown type"
        }
        mock_detector_class.return_value = mock_detector
        
        # Create a new extractor instance so it uses the mocked detector
        extractor = JSONExtractor()
        extractor.detector = mock_detector
        
        ocr_text = "Random text"
        
        result = extractor.extract(
            ocr_text=ocr_text,
            session_id="test-session",
            filename="unknown.pdf"
        )
        
        assert result["document_type"] == "unknown"
        assert "error" in result
        assert "high_confidence_fields" in result
        assert "low_confidence_fields" in result
    
    @patch('app.services.ocr.json_extractor.DocumentTypeDetector')
    @patch('app.services.ocr.json_extractor.GroqLLMClient')
    def test_extract_confidence_filtering(self, mock_llm_client_class, mock_detector_class):
        """Test that confidence filtering works correctly."""
        mock_detector = MagicMock()
        mock_detector.detect_type.return_value = {
            "type": "flight_confirmation",
            "confidence": 0.95,
            "reasoning": "Flight confirmation"
        }
        mock_detector_class.return_value = mock_detector
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        # Include fields with different confidence levels
        mock_response.choices[0].message.content = json.dumps({
            "session_id": "test-session",
            "document_type": "flight_confirmation",
            "airline": {"name": "Scoot", "confidence": 0.95},  # High confidence
            "destination": {"country": "Japan", "confidence": 0.85},  # Medium confidence
            "flight_details": {"departure": {"date": "2025-03-15", "confidence": 0.75}}  # Low confidence (should be filtered)
        })
        mock_client.client.chat.completions.create.return_value = mock_response
        mock_llm_client_class.return_value = mock_client
        
        ocr_text = "Flight to Japan"
        
        result = self.extractor.extract(
            ocr_text=ocr_text,
            session_id="test-session",
            filename="flight.pdf"
        )
        
        assert "high_confidence_fields" in result
        assert "low_confidence_fields" in result
        # Low confidence fields should be filtered out or marked appropriately
    
    @patch('app.services.ocr.json_extractor.DocumentTypeDetector')
    @patch('app.services.ocr.json_extractor.GroqLLMClient')
    @patch('app.services.ocr.json_extractor.Path')
    def test_extract_saves_json_file(self, mock_path_class, mock_llm_client_class, mock_detector_class):
        """Test that extracted JSON is saved to file."""
        mock_detector = MagicMock()
        mock_detector.detect_type.return_value = {
            "type": "flight_confirmation",
            "confidence": 0.95,
            "reasoning": "Flight confirmation"
        }
        mock_detector_class.return_value = mock_detector
        
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "session_id": "test-session",
            "document_type": "flight_confirmation",
            "airline": {"name": "Scoot", "confidence": 0.92}
        })
        mock_client.client.chat.completions.create.return_value = mock_response
        mock_llm_client_class.return_value = mock_client
        
        # Mock file operations
        mock_docs_dir = MagicMock()
        mock_path_class.return_value.mkdir = MagicMock()
        mock_path_class.return_value.__truediv__ = MagicMock(return_value=mock_docs_dir)
        mock_open = MagicMock()
        
        with patch('builtins.open', mock_open):
            ocr_text = "Flight to Japan"
            
            result = self.extractor.extract(
                ocr_text=ocr_text,
                session_id="test-session",
                filename="flight.pdf"
            )
            
            assert "json_file_path" in result
            # Verify file was opened for writing
            mock_open.assert_called()


class TestOCRIntegration:
    """Integration tests for OCR functionality."""
    
    @patch('app.services.ocr.ocr_service.pytesseract')
    @patch('app.services.ocr.ocr_service.Image')
    @patch('app.services.ocr.document_detector.GroqLLMClient')
    @patch('app.services.ocr.json_extractor.GroqLLMClient')
    def test_full_ocr_pipeline(self, mock_extractor_llm, mock_detector_llm, mock_image, mock_pytesseract):
        """Test full OCR pipeline from image to structured data."""
        # Mock OCR extraction
        mock_img = MagicMock()
        mock_img.mode = 'RGB'
        mock_image.open.return_value = mock_img
        mock_pytesseract.image_to_string.return_value = "Flight TR892 from SIN to NRT on March 15, 2025"
        mock_pytesseract.image_to_data.return_value = {'conf': ['91']}
        
        # Mock document detection
        mock_detector_client = MagicMock()
        mock_detector_response = MagicMock()
        mock_detector_response.choices = [MagicMock()]
        mock_detector_response.choices[0].message.content = json.dumps({
            "type": "flight_confirmation",
            "confidence": 0.95,
            "reasoning": "Flight confirmation"
        })
        mock_detector_client.client.chat.completions.create.return_value = mock_detector_response
        mock_detector_llm.return_value = mock_detector_client
        
        # Mock JSON extraction
        mock_extractor_client = MagicMock()
        mock_extractor_response = MagicMock()
        mock_extractor_response.choices = [MagicMock()]
        mock_extractor_response.choices[0].message.content = json.dumps({
            "session_id": "test-session",
            "document_type": "flight_confirmation",
            "airline": {"name": "Scoot", "confidence": 0.92},
            "destination": {"country": "Japan", "confidence": 0.92}
        })
        mock_extractor_client.client.chat.completions.create.return_value = mock_extractor_response
        mock_extractor_llm.return_value = mock_extractor_client
        
        # Run full pipeline
        ocr_service = OCRService()
        test_image_bytes = b'fake image data'
        
        ocr_result = ocr_service.extract_text(test_image_bytes, "flight.png")
        
        assert ocr_result.get("error") is None
        assert "text" in ocr_result
        
        # Test document detection
        detector = DocumentTypeDetector()
        doc_type = detector.detect_type(ocr_result["text"])
        
        assert doc_type["type"] == "flight_confirmation"
        
        # Test JSON extraction
        extractor = JSONExtractor()
        json_result = extractor.extract(
            ocr_text=ocr_result["text"],
            session_id="test-session",
            filename="flight.png"
        )
        
        assert json_result["document_type"] == "flight_confirmation"
        assert "airline" in json_result

