"""
Test JWT decoding with different secrets to diagnose the issue.
"""
from jose import jwt, JWTError
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv("../../.env")

# Get secrets from environment
jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
anon_key = os.getenv("SUPABASE_ANON_KEY")

print("=" * 80)
print("JWT DECODE DIAGNOSTIC TOOL")
print("=" * 80)
print()

# Ask for token
print("Please paste a Supabase JWT token from your browser's network tab:")
print("(Look for the Authorization header in a request to /api/v1/auth/me)")
token = input().strip()

if token.startswith("Bearer "):
    token = token[7:]

print()
print(f"Token first 50 chars: {token[:50]}...")
print()

# Try with JWT secret
print("-" * 80)
print("Attempt 1: Using SUPABASE_JWT_SECRET")
print("-" * 80)
if jwt_secret:
    print(f"Secret: {jwt_secret[:20]}... (length: {len(jwt_secret)})")
    try:
        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"], options={"verify_aud": False})
        print("✅ SUCCESS! JWT decoded successfully")
        print(f"User ID: {payload.get('sub')}")
        print(f"Email: {payload.get('email')}")
        print(f"Role: {payload.get('role')}")
    except JWTError as e:
        print(f"❌ FAILED: {e}")
else:
    print("❌ SUPABASE_JWT_SECRET not found in environment")

print()

# Try with service role key (unlikely to work but worth trying)
print("-" * 80)
print("Attempt 2: Using SUPABASE_SERVICE_ROLE_KEY as secret")
print("-" * 80)
if service_role_key:
    print(f"Key: {service_role_key[:50]}... (length: {len(service_role_key)})")
    try:
        payload = jwt.decode(token, service_role_key, algorithms=["HS256"], options={"verify_aud": False})
        print("✅ SUCCESS! JWT decoded successfully")
        print(f"User ID: {payload.get('sub')}")
        print(f"Email: {payload.get('email')}")
        print(f"Role: {payload.get('role')}")
    except JWTError as e:
        print(f"❌ FAILED: {e}")
else:
    print("❌ SUPABASE_SERVICE_ROLE_KEY not found in environment")

print()
print("=" * 80)
print("NEXT STEPS:")
print("=" * 80)
print()
print("If both attempts failed, you need to get the correct JWT secret from Supabase:")
print()
print("1. Go to https://supabase.com/dashboard/project/YOUR_PROJECT_ID/settings/api")
print("2. Find the section 'JWT Settings'")
print("3. Copy the 'JWT Secret' value")
print("4. Update SUPABASE_JWT_SECRET in your .env file with this value")
print()
print("The JWT secret is different from both the service role key and anon key!")
print()
