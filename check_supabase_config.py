#!/usr/bin/env python3
"""
Helper script to check Supabase configuration without exposing secrets.
Run this to verify your .env file is configured correctly.
"""

import os
from pathlib import Path


def check_env_variable(var_name: str, should_be_jwt: bool = False) -> dict:
    """Check if an environment variable is set and return status."""
    value = os.getenv(var_name)
    
    status = {
        "name": var_name,
        "is_set": value is not None and value != "",
        "is_placeholder": False,
        "value_preview": None
    }
    
    if status["is_set"]:
        # Check if it's a placeholder
        placeholder_keywords = ["your-", "placeholder", "example", "change-this"]
        status["is_placeholder"] = any(kw in value.lower() for kw in placeholder_keywords)
        
        # Show first and last 10 chars for verification (don't expose full secret)
        if len(value) > 20:
            status["value_preview"] = f"{value[:10]}...{value[-10:]}"
        else:
            status["value_preview"] = f"{value[:5]}...{value[-5:]}"
            
        # Check if JWT secret looks like a JWT token (it shouldn't)
        if should_be_jwt and value.startswith("eyJ"):
            status["warning"] = "⚠️  JWT_SECRET looks like a JWT token (starts with 'eyJ'). It should be a plain secret string!"
    
    return status


def main():
    print("=" * 70)
    print("🔍 SUPABASE CONFIGURATION CHECKER")
    print("=" * 70)
    print()
    
    # Load .env file if it exists
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        print(f"✅ Found .env file at: {env_path}")
        # Load environment variables from .env
        try:
            from dotenv import load_dotenv
            load_dotenv(env_path)
            print("✅ Loaded environment variables from .env")
        except ImportError:
            print("⚠️  python-dotenv not installed. Reading system environment only.")
    else:
        print(f"❌ No .env file found at: {env_path}")
        print("   You need to create a .env file from infra/env.example")
        return
    
    print()
    print("-" * 70)
    print("CHECKING SUPABASE CONFIGURATION:")
    print("-" * 70)
    print()
    
    # Check each required variable
    variables = [
        ("SUPABASE_URL", False),
        ("SUPABASE_ANON_KEY", False),
        ("SUPABASE_SERVICE_ROLE_KEY", False),
        ("SUPABASE_JWT_SECRET", True),  # This is the one that's usually missing!
        ("DATABASE_URL", False),
    ]
    
    issues = []
    
    for var_name, is_jwt in variables:
        status = check_env_variable(var_name, is_jwt)
        
        # Print status
        if status["is_set"] and not status["is_placeholder"]:
            print(f"✅ {var_name}")
            print(f"   Preview: {status['value_preview']}")
            if "warning" in status:
                print(f"   {status['warning']}")
                issues.append(f"{var_name}: {status['warning']}")
        elif status["is_set"] and status["is_placeholder"]:
            print(f"⚠️  {var_name} - PLACEHOLDER VALUE DETECTED")
            print(f"   Current: {status['value_preview']}")
            issues.append(f"{var_name}: Contains placeholder value")
        else:
            print(f"❌ {var_name} - NOT SET")
            issues.append(f"{var_name}: Not set")
        
        print()
    
    print("-" * 70)
    print("SUMMARY:")
    print("-" * 70)
    print()
    
    if not issues:
        print("🎉 All Supabase configuration looks good!")
        print()
        print("Next steps:")
        print("1. Start/restart your backend server")
        print("2. Check the startup logs for configuration confirmation")
        print("3. Test authentication")
    else:
        print(f"❌ Found {len(issues)} issue(s):")
        print()
        for i, issue in enumerate(issues, 1):
            print(f"{i}. {issue}")
        print()
        print("=" * 70)
        print("HOW TO FIX:")
        print("=" * 70)
        print()
        print("1. Go to: https://supabase.com/dashboard")
        print("2. Select your project")
        print("3. Navigate to: Settings → API")
        print()
        print("4. Copy these values:")
        print("   - Project URL → SUPABASE_URL")
        print("   - anon/public key → SUPABASE_ANON_KEY")
        print("   - service_role key → SUPABASE_SERVICE_ROLE_KEY")
        print()
        print("5. Scroll down to 'JWT Settings' section:")
        print("   - JWT Secret → SUPABASE_JWT_SECRET")
        print("     (This is NOT a JWT token, it's a secret string!)")
        print()
        print("6. Update your .env file with these values")
        print("7. Restart your backend server")
        print()
        print("📖 For detailed instructions, see: HOW_TO_FIX_AUTH.md")
    
    print()


if __name__ == "__main__":
    main()

