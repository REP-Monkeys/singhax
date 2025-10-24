"""Base insurer adapter interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class InsurerAdapter(ABC):
    """Abstract base class for insurer adapters."""
    
    @abstractmethod
    def get_products(self, ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get available insurance products."""
        pass
    
    @abstractmethod
    def quote_range(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Get quote price range."""
        pass
    
    @abstractmethod
    def price_firm(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Get firm price for a quote."""
        pass
    
    @abstractmethod
    def bind_policy(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Bind a policy from a quote."""
        pass
    
    @abstractmethod
    def claim_requirements(self, claim_type: str) -> Dict[str, Any]:
        """Get claim requirements for a claim type."""
        pass
