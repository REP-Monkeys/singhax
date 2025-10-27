#!/usr/bin/env python3
"""Test different Supabase connection options."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))

from app.core.config import settings
import psycopg2

print("Testing Supabase connection options...\n")

# Test 1: Direct connection
print("1. Testing direct connection:")
print(f"   Connection string: {settings.database_url[:60]}...")
try:
    conn = psycopg2.connect(settings.database_url, connect_timeout=5)
    print("   ✅ Direct connection works!")
    conn.close()
except Exception as e:
    print(f"   ❌ Direct connection failed: {e}")

# Test 2: Try without sslmode
print("\n2. Testing without sslmode:")
base_url = settings.database_url.replace("?sslmode=require", "")
try:
    conn = psycopg2.connect(base_url, connect_timeout=5)
    print("   ✅ Connection without ssl works!")
    conn.close()
except Exception as e:
    print(f"   ❌ Connection without ssl failed: {e}")

print("\nNote: If both fail, check your Supabase dashboard for:")
print("   - Project status (should be Active, not Paused)")
print("   - IP restrictions (should allow all IPs)")
print("   - Network issues (try different network)")
print("   - Correct connection string in Dashboard")

