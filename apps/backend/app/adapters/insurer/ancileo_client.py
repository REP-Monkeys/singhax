"""Ancileo MSIG API client for travel insurance quotation and purchase."""

import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime, date

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.core.config import settings

logger = logging.getLogger(__name__)


class AncileoAPIError(Exception):
    """Base exception for Ancileo API errors."""
    pass


class AncileoQuoteExpiredError(AncileoAPIError):
    """Exception raised when quote has expired."""
    pass


class AncileoClient:
    """HTTP client for Ancileo MSIG Travel Insurance API.
    
    Implements the two core endpoints:
    1. Quotation API - Get insurance quotes
    2. Purchase API - Complete policy purchase
    
    Reference: .cursorrules/ancileo_msig_api_guide.md
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30
    ):
        """Initialize Ancileo API client.
        
        Args:
            api_key: Ancileo API key (defaults to settings.ancileo_msig_api_key)
            base_url: API base URL (defaults to settings.ancileo_api_base_url)
            timeout: Request timeout in seconds (default: 30)
        """
        self.api_key = api_key or settings.ancileo_msig_api_key
        self.base_url = base_url or settings.ancileo_api_base_url
        self.timeout = timeout
        
        if not self.api_key:
            logger.warning("Ancileo API key not configured")
        
        # Create session with retry strategy
        self.session = self._create_session_with_retries()
    
    def _create_session_with_retries(self) -> requests.Session:
        """Create requests session with retry configuration.
        
        Retries on 500, 502, 503, 504 errors with exponential backoff.
        Max 3 retries.
        """
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=1,  # 1s, 2s, 4s delays
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["POST"]  # Updated from method_whitelist
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make HTTP request to Ancileo API.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            payload: Request payload
            
        Returns:
            Response JSON data
            
        Raises:
            AncileoAPIError: For API errors
        """
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key
        }
        
        logger.info(f"Ancileo API Request: {method} {url}")
        logger.debug(f"Request payload: {payload}")
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            
            # Log response
            logger.info(f"Ancileo API Response: {response.status_code}")
            logger.debug(f"Response body: {response.text[:500]}")  # Log first 500 chars
            
            # Handle errors
            if response.status_code == 401:
                logger.error("Invalid or missing API key")
                raise AncileoAPIError("Authentication failed - invalid API key")
            
            elif response.status_code == 404:
                logger.error(f"Resource not found (likely expired quote): {response.text}")
                raise AncileoQuoteExpiredError("Quote not found or expired")
            
            elif response.status_code == 400:
                error_msg = response.text
                logger.error(f"Bad request: {error_msg}")
                raise AncileoAPIError(f"Invalid request: {error_msg}")
            
            elif response.status_code >= 500:
                logger.error(f"Server error: {response.status_code} - {response.text}")
                raise AncileoAPIError(f"Server error: {response.status_code}")
            
            # Raise for other error status codes
            response.raise_for_status()
            
            # Parse JSON response
            return response.json()
            
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout after {self.timeout}s")
            raise AncileoAPIError(f"Request timeout after {self.timeout}s")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise AncileoAPIError(f"Request failed: {str(e)}")
    
    def get_quotation(
        self,
        trip_type: str,
        departure_date: date,
        return_date: Optional[date],
        departure_country: str,
        arrival_country: str,
        adults_count: int,
        children_count: int = 0
    ) -> Dict[str, Any]:
        """Get travel insurance quotation from Ancileo API.
        
        Args:
            trip_type: "RT" (round trip) or "ST" (single trip)
            departure_date: Trip departure date
            return_date: Trip return date (required for RT, omit for ST)
            departure_country: Departure country ISO code (e.g., "SG")
            arrival_country: Arrival country ISO code (e.g., "JP")
            adults_count: Number of adult travelers (must be >= 1)
            children_count: Number of child travelers (default: 0)
            
        Returns:
            Dictionary containing:
            {
                "quoteId": str,
                "offers": [{
                    "offerId": str,
                    "productCode": str,
                    "productType": str,
                    "unitPrice": float,
                    "currency": str,
                    "coverageDetails": {...}
                }]
            }
            
        Raises:
            AncileoAPIError: For API errors
            ValueError: For invalid input
        """
        # Validate inputs
        if trip_type not in ["RT", "ST"]:
            raise ValueError(f"Invalid trip_type: {trip_type}. Must be 'RT' or 'ST'")
        
        if trip_type == "RT" and not return_date:
            raise ValueError("return_date is required for round trip (RT)")
        
        if adults_count < 1:
            raise ValueError("adults_count must be at least 1")
        
        # Validate dates are in future
        today = date.today()
        if departure_date <= today:
            raise ValueError(f"Departure date must be in the future (got {departure_date})")
        
        if trip_type == "RT" and return_date:
            if return_date <= departure_date:
                raise ValueError(f"Return date must be after departure date")
        
        # Build request payload
        payload = {
            "market": "SG",  # Singapore market (fixed)
            "languageCode": "en",  # English (fixed)
            "channel": "white-label",  # Fixed
            "deviceType": "DESKTOP",  # Fixed
            "context": {
                "tripType": trip_type,
                "departureDate": departure_date.strftime("%Y-%m-%d"),
                "departureCountry": departure_country.upper(),
                "arrivalCountry": arrival_country.upper(),
                "adultsCount": adults_count,
                "childrenCount": children_count
            }
        }
        
        # Add returnDate only for round trip (critical - don't include for ST)
        if trip_type == "RT" and return_date:
            payload["context"]["returnDate"] = return_date.strftime("%Y-%m-%d")
        
        # Make API request
        response = self._make_request(
            method="POST",
            endpoint="/v1/travel/front/pricing",
            payload=payload
        )
        
        logger.info(f"Successfully retrieved quotation: {response.get('quoteId')}")
        return response
    
    def create_purchase(
        self,
        quote_id: str,
        offer_id: str,
        product_code: str,
        unit_price: float,
        insureds: list[Dict[str, Any]],
        main_contact: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Complete insurance purchase via Ancileo Purchase API.
        
        CRITICAL: Only call this AFTER payment has been confirmed via Stripe webhook.
        
        Args:
            quote_id: Quote ID from quotation response
            offer_id: Offer ID from quotation response
            product_code: Product code from quotation response
            unit_price: Exact unit price from quotation response
            insureds: List of insured travelers with details:
                [
                    {
                        "id": "1",
                        "title": "Mr",  # Mr, Ms, Mrs, Dr
                        "firstName": "John",
                        "lastName": "Doe",
                        "nationality": "SG",
                        "dateOfBirth": "2000-01-01",
                        "passport": "E1234567",
                        "email": "john@example.com",
                        "phoneType": "mobile",
                        "phoneNumber": "6581234567",
                        "relationship": "main"  # "main" for primary
                    }
                ]
            main_contact: Main contact information (includes address):
                {
                    "id": "1",
                    "title": "Mr",
                    "firstName": "John",
                    "lastName": "Doe",
                    "nationality": "SG",
                    "dateOfBirth": "2000-01-01",
                    "passport": "E1234567",
                    "email": "john@example.com",
                    "phoneType": "mobile",
                    "phoneNumber": "6581234567",
                    "address": "123 Orchard Road",
                    "city": "Singapore",
                    "zipCode": "238858",
                    "countryCode": "SG"
                }
            
        Returns:
            Dictionary containing policy details
            
        Raises:
            AncileoAPIError: For API errors
            AncileoQuoteExpiredError: If quote has expired
        """
        # Build request payload
        payload = {
            "market": "SG",
            "languageCode": "en",
            "channel": "white-label",
            "quoteId": quote_id,
            "purchaseOffers": [
                {
                    "productType": "travel-insurance",
                    "offerId": offer_id,
                    "productCode": product_code,
                    "unitPrice": unit_price,
                    "currency": "SGD",
                    "quantity": 1,
                    "totalPrice": unit_price,  # unit_price * quantity
                    "isSendEmail": True  # Auto-send policy email
                }
            ],
            "insureds": insureds,
            "mainContact": main_contact
        }
        
        logger.info(f"Creating purchase for quote: {quote_id}, offer: {offer_id}")
        
        # Make API request
        response = self._make_request(
            method="POST",
            endpoint="/v1/travel/front/purchase",
            payload=payload
        )
        
        logger.info(f"Successfully created purchase: {response}")
        return response

