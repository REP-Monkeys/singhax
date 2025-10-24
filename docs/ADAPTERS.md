# Insurer Adapters Documentation

## Overview

The ConvoTravelInsure platform uses a plugin-based adapter system to integrate with different insurance providers. This allows the platform to work with multiple insurers while maintaining a consistent interface.

## Adapter Interface

All insurer adapters must implement the `InsurerAdapter` interface:

```python
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
```

## Implementing a Real Insurer Adapter

### Example: Allianz Adapter

```python
from app.adapters.insurer.base import InsurerAdapter
from typing import Dict, Any, List
import requests

class AllianzAdapter(InsurerAdapter):
    """Adapter for Allianz Travel Insurance API."""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def get_products(self, ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get available Allianz products."""
        response = self.session.get(f'{self.base_url}/products')
        response.raise_for_status()
        
        products = []
        for product in response.json():
            products.append({
                'id': product['product_id'],
                'name': product['name'],
                'description': product['description'],
                'base_rate': product['base_rate'],
                'coverage_limits': product['coverage_limits']
            })
        
        return products
    
    def quote_range(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Get quote range from Allianz."""
        quote_request = {
            'product_type': input['product_type'],
            'travelers': input['travelers'],
            'activities': input['activities'],
            'trip_duration': input['trip_duration'],
            'destinations': input['destinations']
        }
        
        response = self.session.post(
            f'{self.base_url}/quotes/range',
            json=quote_request
        )
        response.raise_for_status()
        
        result = response.json()
        return {
            'price_min': result['min_price'],
            'price_max': result['max_price'],
            'breakdown': result['breakdown'],
            'currency': result['currency']
        }
    
    def price_firm(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Get firm price from Allianz."""
        firm_request = {
            'product_type': input['product_type'],
            'travelers': input['travelers'],
            'activities': input['activities'],
            'trip_duration': input['trip_duration'],
            'destinations': input['destinations'],
            'risk_factors': input['risk_factors']
        }
        
        response = self.session.post(
            f'{self.base_url}/quotes/firm',
            json=firm_request
        )
        response.raise_for_status()
        
        result = response.json()
        return {
            'price': result['price'],
            'breakdown': result['breakdown'],
            'currency': result['currency'],
            'eligibility': result['eligibility']
        }
    
    def bind_policy(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Bind policy with Allianz."""
        bind_request = {
            'quote_id': input['quote_id'],
            'payment_id': input['payment_id'],
            'travelers': input['travelers'],
            'effective_date': input['effective_date'],
            'expiry_date': input['expiry_date']
        }
        
        response = self.session.post(
            f'{self.base_url}/policies/bind',
            json=bind_request
        )
        response.raise_for_status()
        
        result = response.json()
        return {
            'policy_number': result['policy_number'],
            'coverage': result['coverage'],
            'named_insureds': result['named_insureds'],
            'insurer_ref': result['policy_id']
        }
    
    def claim_requirements(self, claim_type: str) -> Dict[str, Any]:
        """Get claim requirements from Allianz."""
        response = self.session.get(
            f'{self.base_url}/claims/requirements/{claim_type}'
        )
        response.raise_for_status()
        
        return response.json()
```

### Example: AIG Adapter

```python
from app.adapters.insurer.base import InsurerAdapter
from typing import Dict, Any, List
import aiohttp
import asyncio

class AIGAdapter(InsurerAdapter):
    """Adapter for AIG Travel Insurance API."""
    
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
    
    async def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None):
        """Make async HTTP request to AIG API."""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        async with aiohttp.ClientSession() as session:
            if method == 'GET':
                async with session.get(f'{self.base_url}{endpoint}', headers=headers) as response:
                    return await response.json()
            elif method == 'POST':
                async with session.post(f'{self.base_url}{endpoint}', json=data, headers=headers) as response:
                    return await response.json()
    
    def get_products(self, ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get available AIG products."""
        return asyncio.run(self._make_request('GET', '/products'))
    
    def quote_range(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Get quote range from AIG."""
        return asyncio.run(self._make_request('POST', '/quotes/range', input))
    
    def price_firm(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Get firm price from AIG."""
        return asyncio.run(self._make_request('POST', '/quotes/firm', input))
    
    def bind_policy(self, input: Dict[str, Any]) -> Dict[str, Any]:
        """Bind policy with AIG."""
        return asyncio.run(self._make_request('POST', '/policies/bind', input))
    
    def claim_requirements(self, claim_type: str) -> Dict[str, Any]:
        """Get claim requirements from AIG."""
        return asyncio.run(self._make_request('GET', f'/claims/requirements/{claim_type}'))
```

## Configuration

### Environment Variables

Each adapter requires specific configuration:

```bash
# Allianz
ALLIANZ_API_KEY=your-allianz-api-key
ALLIANZ_BASE_URL=https://api.allianz.com/v1

# AIG
AIG_API_KEY=your-aig-api-key
AIG_BASE_URL=https://api.aig.com/v1

# Default adapter
DEFAULT_INSURER_ADAPTER=allianz
```

### Adapter Factory

```python
from app.adapters.insurer.allianz import AllianzAdapter
from app.adapters.insurer.aig import AIGAdapter
from app.adapters.insurer.mock import MockInsurerAdapter
from app.core.config import settings

def create_insurer_adapter(adapter_name: str = None) -> InsurerAdapter:
    """Factory function to create insurer adapters."""
    
    if adapter_name is None:
        adapter_name = settings.default_insurer_adapter
    
    if adapter_name == 'allianz':
        return AllianzAdapter(
            api_key=settings.allianz_api_key,
            base_url=settings.allianz_base_url
        )
    elif adapter_name == 'aig':
        return AIGAdapter(
            api_key=settings.aig_api_key,
            base_url=settings.aig_base_url
        )
    elif adapter_name == 'mock':
        return MockInsurerAdapter()
    else:
        raise ValueError(f"Unknown adapter: {adapter_name}")
```

## Testing Adapters

### Unit Tests

```python
import pytest
from app.adapters.insurer.allianz import AllianzAdapter

class TestAllianzAdapter:
    def test_get_products(self):
        adapter = AllianzAdapter('test-key', 'https://api.test.com')
        products = adapter.get_products({})
        
        assert len(products) > 0
        assert 'id' in products[0]
        assert 'name' in products[0]
    
    def test_quote_range(self):
        adapter = AllianzAdapter('test-key', 'https://api.test.com')
        
        input_data = {
            'product_type': 'basic_travel',
            'travelers': [{'name': 'John Doe', 'age': 35}],
            'activities': [{'type': 'sightseeing'}],
            'trip_duration': 7,
            'destinations': ['France']
        }
        
        result = adapter.quote_range(input_data)
        
        assert 'price_min' in result
        assert 'price_max' in result
        assert result['price_min'] < result['price_max']
```

### Integration Tests

```python
import pytest
from app.adapters.insurer.allianz import AllianzAdapter

@pytest.mark.integration
class TestAllianzIntegration:
    def test_real_api_call(self):
        adapter = AllianzAdapter(
            api_key=os.getenv('ALLIANZ_TEST_API_KEY'),
            base_url=os.getenv('ALLIANZ_TEST_BASE_URL')
        )
        
        products = adapter.get_products({})
        assert len(products) > 0
```

## Error Handling

### Adapter Exceptions

```python
class InsurerAdapterError(Exception):
    """Base exception for insurer adapter errors."""
    pass

class QuoteError(InsurerAdapterError):
    """Error during quote generation."""
    pass

class PolicyError(InsurerAdapterError):
    """Error during policy binding."""
    pass

class ClaimError(InsurerAdapterError):
    """Error during claim processing."""
    pass
```

### Error Handling in Adapters

```python
def quote_range(self, input: Dict[str, Any]) -> Dict[str, Any]:
    """Get quote range with error handling."""
    try:
        response = self.session.post(
            f'{self.base_url}/quotes/range',
            json=input,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.Timeout:
        raise QuoteError("Quote request timed out")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            raise QuoteError("Invalid quote request")
        elif e.response.status_code == 500:
            raise QuoteError("Insurer service error")
        else:
            raise QuoteError(f"HTTP error: {e.response.status_code}")
    except requests.exceptions.RequestException as e:
        raise QuoteError(f"Request failed: {str(e)}")
```

## Monitoring and Logging

### Adapter Metrics

```python
import logging
import time
from functools import wraps

logger = logging.getLogger(__name__)

def log_adapter_call(func):
    """Decorator to log adapter method calls."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.info(f"{func.__name__} completed in {duration:.2f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"{func.__name__} failed after {duration:.2f}s: {str(e)}")
            raise
    return wrapper

class AllianzAdapter(InsurerAdapter):
    @log_adapter_call
    def quote_range(self, input: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation...
        pass
```

## Best Practices

1. **Error Handling**: Always implement proper error handling and logging
2. **Timeouts**: Set appropriate timeouts for API calls
3. **Retries**: Implement retry logic for transient failures
4. **Caching**: Cache product information and other static data
5. **Validation**: Validate input data before making API calls
6. **Testing**: Write comprehensive unit and integration tests
7. **Documentation**: Document all adapter-specific configuration and requirements

## Adding New Adapters

1. Create a new adapter class implementing `InsurerAdapter`
2. Add configuration variables to settings
3. Update the adapter factory
4. Write tests
5. Update documentation
6. Add to the adapter registry

## Adapter Registry

```python
ADAPTER_REGISTRY = {
    'allianz': AllianzAdapter,
    'aig': AIGAdapter,
    'mock': MockInsurerAdapter,
    # Add new adapters here
}
```
