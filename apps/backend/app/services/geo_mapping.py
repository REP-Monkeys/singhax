"""Geographic destination mapping for insurance pricing."""

from enum import Enum
from typing import Dict, Any, Set


class DestinationArea(Enum):
    """Geographic areas for insurance pricing."""
    AREA_A = "area_a"  # ASEAN
    AREA_B = "area_b"  # Asia-Pacific
    AREA_C = "area_c"  # Worldwide


class GeoMapper:
    """Maps destinations to geographic areas and base rates."""
    
    # Area A: ASEAN countries (9 countries)
    AREA_A_COUNTRIES: Set[str] = {
        "brunei", "cambodia", "indonesia", "laos", "malaysia",
        "myanmar", "philippines", "thailand", "vietnam"
    }
    
    # Area B: Asia-Pacific countries (10 countries, excludes Area A)
    AREA_B_COUNTRIES: Set[str] = {
        "australia", "china", "hong kong", "india", "japan",
        "korea", "macau", "new zealand", "sri lanka", "taiwan"
    }
    
    # Base rates per geographic area
    BASE_RATES: Dict[DestinationArea, float] = {
        DestinationArea.AREA_A: 3.0,
        DestinationArea.AREA_B: 5.0,
        DestinationArea.AREA_C: 8.0,
    }
    
    # Country name to ISO 2-letter code mapping (for Ancileo API)
    COUNTRY_ISO_CODES: Dict[str, str] = {
        # Singapore (departure country for SG market)
        "singapore": "SG",
        
        # Area A - ASEAN countries
        "brunei": "BN",
        "cambodia": "KH",
        "indonesia": "ID",
        "laos": "LA",
        "malaysia": "MY",
        "myanmar": "MM",
        "philippines": "PH",
        "thailand": "TH",
        "vietnam": "VN",
        
        # Area B - Asia-Pacific countries
        "australia": "AU",
        "china": "CN",
        "hong kong": "HK",
        "india": "IN",
        "japan": "JP",
        "korea": "KR",
        "south korea": "KR",
        "macau": "MO",
        "new zealand": "NZ",
        "sri lanka": "LK",
        "taiwan": "TW",
        
        # Area C - Common worldwide destinations
        "united states": "US",
        "usa": "US",
        "united kingdom": "GB",
        "uk": "GB",
        "canada": "CA",
        "france": "FR",
        "germany": "DE",
        "italy": "IT",
        "spain": "ES",
        "switzerland": "CH",
        "netherlands": "NL",
        "belgium": "BE",
        "austria": "AT",
        "denmark": "DK",
        "norway": "NO",
        "sweden": "SE",
        "finland": "FI",
        "greece": "GR",
        "portugal": "PT",
        "ireland": "IE",
        "poland": "PL",
        "czech republic": "CZ",
        "hungary": "HU",
        "russia": "RU",
        "turkey": "TR",
        "united arab emirates": "AE",
        "uae": "AE",
        "dubai": "AE",
        "saudi arabia": "SA",
        "qatar": "QA",
        "egypt": "EG",
        "south africa": "ZA",
        "kenya": "KE",
        "morocco": "MA",
        "brazil": "BR",
        "argentina": "AR",
        "chile": "CL",
        "mexico": "MX",
        "peru": "PE",
        "colombia": "CO",
        "iceland": "IS",
        "croatia": "HR",
        "romania": "RO",
        "bulgaria": "BG",
        "israel": "IL",
        "jordan": "JO",
        "lebanon": "LB",
        "tunisia": "TN",
        "ethiopia": "ET",
        "tanzania": "TZ",
        "zimbabwe": "ZW",
        "botswana": "BW",
        "namibia": "NA",
        "jamaica": "JM",
        "bahamas": "BS",
        "barbados": "BB",
        "costa rica": "CR",
        "panama": "PA",
        "uruguay": "UY",
        "paraguay": "PY",
        "venezuela": "VE",
        "ecuador": "EC",
        "bolivia": "BO",
        "cuba": "CU",
        "nepal": "NP",
        "bangladesh": "BD",
        "pakistan": "PK",
        "maldives": "MV",
        "seychelles": "SC",
        "mauritius": "MU",
        "fiji": "FJ",
        "papua new guinea": "PG",
        "samoa": "WS",
        "tonga": "TO",
        "vanuatu": "VU",
    }
    
    @classmethod
    def get_area(cls, destination: str) -> DestinationArea:
        """Get geographic area for destination.
        
        Args:
            destination: Country name (case-insensitive)
            
        Returns:
            DestinationArea enum representing the geographic area
        """
        # Normalize to lowercase for case-insensitive matching
        dest_lower = destination.lower().strip()
        
        # Check Area A first, then Area B, else Area C
        if dest_lower in cls.AREA_A_COUNTRIES:
            return DestinationArea.AREA_A
        elif dest_lower in cls.AREA_B_COUNTRIES:
            return DestinationArea.AREA_B
        else:
            return DestinationArea.AREA_C
    
    @classmethod
    def get_base_rate(cls, destination: str) -> float:
        """Get base rate for destination.
        
        Args:
            destination: Country name (case-insensitive)
            
        Returns:
            Base rate per day for the destination's area
        """
        area = cls.get_area(destination)
        return cls.BASE_RATES[area]
    
    @classmethod
    def validate_destination(cls, destination: str) -> Dict[str, Any]:
        """Validate destination and return area info.
        
        Args:
            destination: Country name (case-insensitive)
            
        Returns:
            Dictionary with keys:
                - valid (bool): Always True for Step 1 (no exclusions yet)
                - area (DestinationArea): Geographic area enum
                - base_rate (float): Base rate per day for the area
        """
        area = cls.get_area(destination)
        base_rate = cls.BASE_RATES[area]
        
        return {
            "valid": True,
            "area": area,
            "base_rate": base_rate
        }
    
    @classmethod
    def get_country_iso_code(cls, country_name: str) -> str:
        """Convert country name to 2-letter ISO code.
        
        Used for Ancileo API which requires ISO country codes.
        
        Args:
            country_name: Country name (case-insensitive)
            
        Returns:
            2-letter ISO country code (uppercase)
            
        Raises:
            ValueError: If country not found in mapping
        """
        normalized = country_name.lower().strip()
        
        iso_code = cls.COUNTRY_ISO_CODES.get(normalized)
        
        if not iso_code:
            # Try partial matching for common variations
            for country, code in cls.COUNTRY_ISO_CODES.items():
                if normalized in country or country in normalized:
                    return code
            
            # If still not found, raise error
            raise ValueError(
                f"Country '{country_name}' not found in ISO code mapping. "
                f"Please add it to COUNTRY_ISO_CODES."
            )
        
        return iso_code


