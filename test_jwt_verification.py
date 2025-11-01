#!/usr/bin/env python3
"""
Test JWT verification with actual token
"""

import sys
from pathlib import Path

# Load .env first
from dotenv import load_dotenv
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "apps" / "backend"))

from app.core.config import settings
from app.core.security import verify_supabase_token


def main():
    print("=" * 70)
    print("🔐 JWT VERIFICATION TEST")
    print("=" * 70)
    print()
    
    # Check configuration
    print("Configuration Status:")
    print(f"  JWT Secret Set: {settings.supabase_jwt_secret is not None}")
    if settings.supabase_jwt_secret:
        print(f"  JWT Secret Preview: {settings.supabase_jwt_secret[:20]}...")
        print(f"  JWT Secret Length: {len(settings.supabase_jwt_secret)}")
        
        # Check if it looks like a JWT token (it shouldn't)
        if settings.supabase_jwt_secret.startswith("eyJ"):
            print("  ⚠️  WARNING: JWT Secret looks like a JWT token!")
        else:
            print("  ✅ JWT Secret format looks correct")
    
    print()
    print("-" * 70)
    print()
    
    # Ask for a token to test
    print("To test JWT verification, you need a valid Supabase access token.")
    print()
    print("How to get a token:")
    print("1. Open your frontend in a browser")
    print("2. Log in with your Supabase credentials")
    print("3. Open DevTools → Network tab")
    print("4. Look for any API request")
    print("5. Copy the 'Authorization: Bearer <token>' header value")
    print()
    
    token = input("Paste your JWT token here (or press Enter to skip): ").strip()
    
    if not token:
        print()
        print("No token provided. Skipping verification test.")
        print()
        print("When you have a token, you can test it by calling:")
        print("  verify_supabase_token(your_token)")
        return
    
    # Remove "Bearer " prefix if present
    if token.startswith("Bearer "):
        token = token[7:]
    
    print()
    print("Testing JWT verification...")
    print(f"Token preview: {token[:50]}...")
    print()
    
    # Try to verify
    result = verify_supabase_token(token)
    
    print()
    print("-" * 70)
    print()
    
    if result:
        print("✅ JWT VERIFICATION SUCCESSFUL!")
        print()
        print("Token payload:")
        print(f"  User ID: {result.get('sub')}")
        print(f"  Email: {result.get('email')}")
        print(f"  Role: {result.get('role')}")
        print()
    else:
        print("❌ JWT VERIFICATION FAILED")
        print()
        print("This usually means:")
        print("1. The token is expired")
        print("2. The JWT secret is incorrect")
        print("3. The token was not issued by your Supabase project")
        print()
        print("Check the debug output above for more details.")
        print()


if __name__ == "__main__":
    main()

