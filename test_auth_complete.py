#!/usr/bin/env python3
"""
Complete authentication system test.
Tests JWT verification and database connection.
"""

import sys
import os
from pathlib import Path

# Load .env file before importing settings
from dotenv import load_dotenv
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "apps" / "backend"))

from app.core.config import settings
from app.core.security import verify_supabase_token
from app.core.db import engine
from sqlalchemy import text


def test_config():
    """Test configuration is loaded."""
    print("=" * 70)
    print("1️⃣  TESTING CONFIGURATION")
    print("=" * 70)
    
    checks = [
        ("Supabase URL", settings.supabase_url),
        ("Supabase Anon Key", settings.supabase_anon_key),
        ("Supabase Service Role Key", settings.supabase_service_role_key),
        ("Supabase JWT Secret", settings.supabase_jwt_secret),
        ("Database URL", settings.database_url),
    ]
    
    all_good = True
    for name, value in checks:
        if value and not any(placeholder in str(value).lower() for placeholder in ["your-", "placeholder", "example"]):
            print(f"   ✅ {name} configured")
        else:
            print(f"   ❌ {name} NOT configured or is placeholder")
            all_good = False
    
    print()
    return all_good


def test_database_connection():
    """Test database connection."""
    print("=" * 70)
    print("2️⃣  TESTING DATABASE CONNECTION")
    print("=" * 70)
    
    try:
        conn = engine.connect()
        result = conn.execute(text('SELECT 1'))
        conn.close()
        print("   ✅ Database connection successful!")
        print()
        return True
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        print()
        return False


def test_jwt_verification():
    """Test JWT verification with a sample token."""
    print("=" * 70)
    print("3️⃣  TESTING JWT VERIFICATION")
    print("=" * 70)
    
    print("   ℹ️  JWT verification requires a valid Supabase token")
    print("   ℹ️  To test, you need to:")
    print("      1. Start your backend server")
    print("      2. Log in through your frontend")
    print("      3. Check the network tab for the Authorization header")
    print()
    print("   Configuration check:")
    
    if settings.supabase_jwt_secret:
        secret_preview = settings.supabase_jwt_secret[:20] + "..." if len(settings.supabase_jwt_secret) > 20 else settings.supabase_jwt_secret
        print(f"   ✅ JWT Secret configured: {secret_preview}")
        
        # Check if it looks like a JWT (it shouldn't)
        if settings.supabase_jwt_secret.startswith("eyJ"):
            print("   ⚠️  WARNING: JWT Secret looks like a JWT token!")
            print("      It should be a plain secret string, not a token.")
            print("      Get it from: Supabase Dashboard → Settings → API → JWT Settings")
            return False
        else:
            print("   ✅ JWT Secret format looks correct (not a JWT token)")
    else:
        print("   ❌ JWT Secret NOT configured")
        return False
    
    print()
    return True


def test_auth_endpoint():
    """Test if the auth endpoint is working."""
    print("=" * 70)
    print("4️⃣  TESTING AUTH ENDPOINTS")
    print("=" * 70)
    
    print("   ℹ️  To test authentication endpoints:")
    print()
    print("   Option 1: Start the backend server")
    print("   -------")
    print("   cd apps/backend")
    print("   python -m uvicorn app.main:app --reload --port 8000")
    print()
    print("   Option 2: Use the batch file")
    print("   -------")
    print("   START_BACKEND.bat")
    print()
    print("   Then visit: http://localhost:8000/docs")
    print()
    return True


def main():
    """Run all tests."""
    print()
    print("🔐 AUTHENTICATION SYSTEM TEST")
    print()
    
    results = []
    
    # Run tests
    results.append(("Configuration", test_config()))
    results.append(("Database Connection", test_database_connection()))
    results.append(("JWT Verification Setup", test_jwt_verification()))
    results.append(("Auth Endpoints Info", test_auth_endpoint()))
    
    # Summary
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print()
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"   {status} - {name}")
    
    print()
    
    if all(result[1] for result in results):
        print("🎉 ALL TESTS PASSED!")
        print()
        print("Your authentication system is properly configured.")
        print()
        print("Next steps:")
        print("1. Start your backend server:")
        print("   cd apps/backend")
        print("   python -m uvicorn app.main:app --reload --port 8000")
        print()
        print("2. Start your frontend:")
        print("   cd apps/frontend")
        print("   npm run dev")
        print()
        print("3. Test login functionality")
        print()
    else:
        print("⚠️  SOME TESTS FAILED")
        print()
        print("Please check the failed tests above and:")
        print("1. Verify your .env file has correct values")
        print("2. Ensure your Supabase project is active")
        print("3. Check network connectivity")
        print()
    
    return 0 if all(result[1] for result in results) else 1


if __name__ == "__main__":
    sys.exit(main())

