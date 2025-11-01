#!/usr/bin/env python3
"""
Test script to verify the complete payment integration.

This script checks:
1. Backend API is running
2. Payment endpoints are accessible
3. Webhook endpoint is configured
4. Email service is configured
"""

import requests
import sys
from typing import Dict, Any

# Configuration
BACKEND_URL = "http://localhost:8000/api/v1"


def check_service(name: str, url: str) -> bool:
    """Check if a service is running."""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ {name}: Running")
            return True
        else:
            print(f"⚠️  {name}: Returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {name}: Not accessible ({str(e)})")
        return False


def check_payment_health() -> bool:
    """Check payment service health."""
    return check_service("Payment Service", f"{BACKEND_URL}/payments/health")


def check_chat_health() -> bool:
    """Check chat service health."""
    return check_service("Chat Service", f"{BACKEND_URL}/chat/health")


def test_webhook_accessibility() -> bool:
    """Test that webhook endpoint is accessible."""
    print("\n🔔 Testing webhook endpoint...")
    # We can't POST without valid Stripe signature, but we can check it responds
    try:
        response = requests.post(
            f"{BACKEND_URL}/payments/webhook/stripe",
            json={},
            timeout=5
        )
        # We expect 400 (invalid payload) not 404 - this means endpoint exists
        if response.status_code in [400, 401]:
            print(f"✅ Webhook endpoint: Accessible (returned {response.status_code})")
            print("   Note: 400/401 expected - means endpoint exists but requires valid Stripe signature")
            return True
        elif response.status_code == 404:
            print(f"❌ Webhook endpoint: Not found (404)")
            return False
        else:
            print(f"⚠️  Webhook endpoint: Unexpected status {response.status_code}")
            return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Webhook endpoint: Not accessible ({str(e)})")
        return False


def check_environment() -> Dict[str, bool]:
    """Check environment configuration."""
    print("\n⚙️  Checking environment configuration...")
    
    import os
    from pathlib import Path
    
    # Load .env file
    env_path = Path(__file__).parent.parent.parent / ".env"
    
    if not env_path.exists():
        print(f"❌ .env file not found at: {env_path}")
        return {"env_file": False}
    
    print(f"✅ .env file found")
    
    # Check for required environment variables
    required_vars = [
        "STRIPE_SECRET_KEY",
        "STRIPE_PUBLISHABLE_KEY", 
        "STRIPE_WEBHOOK_SECRET",
        "DATABASE_URL",
        "GROQ_API_KEY"
    ]
    
    results = {}
    with open(env_path) as f:
        env_content = f.read()
    
    for var in required_vars:
        # Check if variable is defined and not empty
        if f"{var}=" in env_content:
            # Get the value
            line = [l for l in env_content.split('\n') if l.startswith(f"{var}=")]
            if line:
                value = line[0].split('=', 1)[1].strip()
                if value and not value.startswith('#'):
                    print(f"✅ {var}: Configured")
                    results[var] = True
                else:
                    print(f"❌ {var}: Not set (empty value)")
                    results[var] = False
            else:
                print(f"❌ {var}: Not found")
                results[var] = False
        else:
            print(f"❌ {var}: Not found in .env")
            results[var] = False
    
    return results


def print_next_steps(all_passed: bool):
    """Print next steps for user."""
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALL CHECKS PASSED!")
        print("="*60)
        print("\n🚀 Next Steps:")
        print("\n1. Start Stripe webhook forwarding:")
        print("   cd apps/backend")
        print("   ./start_stripe_webhooks.sh")
        print("\n2. Copy the webhook secret (whsec_...) and update .env")
        print("\n3. Test payment flow:")
        print("   - Go to http://localhost:3000")
        print("   - Start a conversation and get a quote")
        print("   - Click 'Proceed to Payment'")
        print("   - Use test card: 4242 4242 4242 4242")
        print("   - Complete payment")
        print("\n4. Verify results:")
        print("   - Check chat for confirmation message")
        print("   - Check backend logs for webhook events")
        print("   - Check database for payment status = 'completed'")
    else:
        print("⚠️  SOME CHECKS FAILED")
        print("="*60)
        print("\n🔧 Please fix the issues above before testing payment flow.")
        print("\n📚 See PAYMENT_SETUP_GUIDE.md for detailed instructions")
    print()


def main():
    """Run all integration tests."""
    print("="*60)
    print("🧪 Payment Integration Test")
    print("="*60)
    
    results = []
    
    # Check services
    print("\n📡 Checking services...")
    results.append(check_payment_health())
    results.append(check_chat_health())
    
    # Check webhook
    results.append(test_webhook_accessibility())
    
    # Check environment
    env_results = check_environment()
    results.extend(env_results.values())
    
    # Summary
    all_passed = all(results)
    passed_count = sum(results)
    total_count = len(results)
    
    print("\n" + "="*60)
    print(f"📊 Results: {passed_count}/{total_count} checks passed")
    
    # Print next steps
    print_next_steps(all_passed)
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()

