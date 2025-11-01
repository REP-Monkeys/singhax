# Authentication Debugging - Changes Summary

## Problem Identified
Supabase JWT verification is failing with "Signature verification failed" because the `SUPABASE_JWT_SECRET` environment variable is not configured.

## Root Cause
From the debug output in the terminal logs:
```
[DEBUG] supabase_jwt_secret is set: False
[DEBUG] supabase_service_role_key is set: True
[DEBUG] Will use: SERVICE_ROLE_KEY
[DEBUG] Using JWT secret: your-service-role-ke... (length: 21)
```

The code is falling back to using `SUPABASE_SERVICE_ROLE_KEY` as the JWT secret, which is incorrect. The JWT secret is a different cryptographic key used specifically for signing/verifying JWT tokens.

## Files Modified for Debugging

### 1. `apps/backend/app/core/security.py`
**Purpose:** Add comprehensive JWT token debugging

**Key Changes:**
- Lines 82-85: Print which secret is configured and which one will be used
- Lines 96-101: Decode token without verification to show payload structure (with verify_aud and verify_exp disabled)
- Lines 103-112: Manually decode JWT header to show algorithm and key ID (kid)

**What it shows:**
- Configuration status of JWT secrets
- Token header (algorithm, kid)
- Token payload (without verification)
- Which secret is being used for verification

### 2. `apps/backend/app/main.py`
**Purpose:** Show Supabase configuration on startup

**Key Changes:**
- Lines 77-86: Print status of all Supabase environment variables
- Show first 30 characters of configured secrets (without exposing full secrets)

**What it shows:**
- Which Supabase variables are loaded from .env
- Hints about configuration issues

### 3. `infra/env.example`
**Purpose:** Document the missing environment variable

**Key Changes:**
- Line 40: Added `SUPABASE_JWT_SECRET` with helpful comment

## Debug Output Example

### On Server Startup:
```
[CONFIG] Supabase URL configured: True
[CONFIG] Supabase anon key configured: True
[CONFIG] Supabase service role key configured: True
[CONFIG] Supabase JWT secret configured: False  ← Problem identified!
[CONFIG] Service role key starts with: eyJhbGciOiJIUzI1NiIsInR5cCI6Ikp...
```

### During Authentication:
```
[DEBUG] supabase_jwt_secret is set: False
[DEBUG] supabase_service_role_key is set: True
[DEBUG] Will use: SERVICE_ROLE_KEY
[DEBUG] Using JWT secret: your-service-role-ke... (length: 21)
[DEBUG] Token first 50 chars: eyJhbGciOiJIUzI1NiIsImtpZCI6IjY5cWowcUNwME9tdzN5M2...
[DEBUG] Token header: {
  "alg": "HS256",
  "kid": "69qj0qCp0Omw3y3i",
  "typ": "JWT"
}
[DEBUG] Token payload (unverified): {
  "iss": "https://zwyib...",
  "sub": "47ded42d-94fc-4e17-b37b-81fd74353997",
  ...
}
Supabase JWT verification failed: Signature verification failed.
```

## Solution

The user needs to add `SUPABASE_JWT_SECRET` to their `.env` file:

1. Get the JWT Secret from Supabase:
   - Go to: https://supabase.com/dashboard/project/YOUR_PROJECT_ID/settings/api
   - Navigate to "JWT Settings" section
   - Copy the "JWT Secret" value

2. Add to `.env` file:
   ```
   SUPABASE_JWT_SECRET=<paste-jwt-secret-here>
   ```

3. Restart the backend server

## Important Notes

- **No authentication logic was changed** - only debugging output was added
- The debug output will help identify the exact issue
- Once `SUPABASE_JWT_SECRET` is configured, authentication should work
- The JWT secret is different from both the service role key and anon key
- All debug output is prefixed with `[DEBUG]` or `[CONFIG]` for easy filtering

## Testing After Fix

After adding the JWT secret, the debug output should show:
```
[CONFIG] Supabase JWT secret configured: True
[DEBUG] Will use: JWT_SECRET
[DEBUG] JWT verification successful! User ID: 47ded42d-94fc-4e17-b37b-81fd74353997
```

## Files NOT Modified
- `apps/backend/app/core/config.py` - already had uncommitted changes from before
- `apps/backend/requirements.txt` - already had uncommitted changes from before

These files are shown as modified in git status but were not changed by this debugging session.
