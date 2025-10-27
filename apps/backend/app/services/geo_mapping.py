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


