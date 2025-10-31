"""Document type detection using LLM."""

from typing import Dict, Any
from app.agents.llm_client import GroqLLMClient


class DocumentTypeDetector:
    """Detect document type from OCR text using LLM."""
    
    def __init__(self):
        self.llm_client = GroqLLMClient()
    
    def detect_type(self, ocr_text: str) -> Dict[str, Any]:
        """
        Detect document type from OCR text.
        
        Args:
            ocr_text: Extracted text from OCR
            
        Returns:
            Dictionary with:
            - type: detected document type
            - confidence: confidence score
            - reasoning: explanation
        """
        # Use first 2000 characters for detection (enough context)
        text_sample = ocr_text[:2000] if len(ocr_text) > 2000 else ocr_text
        
        prompt = f"""Analyze this document text and determine its type.

Document text:
{text_sample}

Classify as ONE of these types:
1. flight_confirmation - Flight tickets, booking confirmations, PNR references, airline confirmations
2. hotel_booking - Hotel reservations, accommodation confirmations, check-in/check-out dates
3. itinerary - Travel schedules, day-by-day plans, activity lists, travel plans
4. visa_application - Visa forms, entry permits, consulate documents, visa approvals

Respond with ONLY a valid JSON object:
{{
    "type": "flight_confirmation",
    "confidence": 0.95,
    "reasoning": "Contains flight numbers, departure/arrival times, and PNR reference"
}}"""
        
        try:
            # Groq may not support response_format, so we'll parse JSON from text response
            response = self.llm_client.client.chat.completions.create(
                model=self.llm_client.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=150
            )
            
            result_text = response.choices[0].message.content.strip()
            import json
            import re
            
            # Try to extract JSON from response (in case LLM adds extra text)
            json_match = re.search(r'\{[^{}]*\}', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(0)
            
            detected = json.loads(result_text)
            
            # Validate type
            valid_types = ["flight_confirmation", "hotel_booking", "itinerary", "visa_application"]
            if detected.get("type") not in valid_types:
                detected["type"] = "unknown"
                detected["confidence"] = 0.0
                detected["reasoning"] = "Could not determine document type"
            
            return detected
            
        except Exception as e:
            print(f"⚠️  Document type detection failed: {e}")
            return {
                "type": "unknown",
                "confidence": 0.0,
                "reasoning": f"Detection error: {str(e)}"
            }

