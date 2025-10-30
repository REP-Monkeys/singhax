# Supabase Auth Migration Guide

This guide documents the migration from custom JWT authentication to Supabase Auth with Row Level Security (RLS).

## Overview

We've migrated from a custom authentication system to Supabase Auth, which enables:
- **Built-in authentication** with email/password, social OAuth, and more
- **Row Level Security (RLS)** policies that automatically enforce data isolation
- **Automatic session management** with JWT tokens
- **Better security** with Supabase's battle-tested auth system

## What Changed

### Backend Changes

1. **Security Module** (`app/core/security.py`)
   - Added Supabase JWT token validation
   - Updated `get_current_user` to accept Supabase tokens
   - Maintains backward compatibility with legacy tokens during migration

2. **Auth Router** (`app/routers/auth.py`)
   - `POST /auth/register` now creates users in Supabase Auth
   - `POST /auth/login` authenticates via Supabase and returns Supabase JWT tokens
   - User IDs in our database now match Supabase `auth.users.id`

3. **Database Connection**
   - Backend uses service role key for operations that bypass RLS
   - User-facing operations will use authenticated connections with RLS

### Frontend Changes

1. **Supabase Client** (`src/lib/supabase.ts`)
   - New Supabase client initialized with project URL and anon key

2. **Auth Context** (`src/contexts/AuthContext.tsx`)
   - Updated to use Supabase client for authentication
   - Listens to Supabase auth state changes
   - Stores Supabase access tokens

### Database Changes

1. **Row Level Security Policies** (`apps/backend/scripts/enable_rls_policies.sql`)
   - All tables now have RLS enabled
   - Policies restrict users to their own data using `auth.uid()`
   - Service role policies allow backend to bypass RLS when needed

## Migration Steps

### 1. Install Dependencies

**Backend:**
```bash
cd apps/backend
pip install supabase==2.3.0
```

**Frontend:**
```bash
cd apps/frontend
npm install @supabase/supabase-js@^2.39.0
```

### 2. Environment Variables

Ensure these are set in your `.env` file:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Frontend (.env.local or .env)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

### 3. Enable RLS Policies

Run the SQL script in your Supabase SQL Editor:

```bash
# Copy and paste the contents of:
apps/backend/scripts/enable_rls_policies.sql
```

Or execute via psql:
```bash
psql $DATABASE_URL < apps/backend/scripts/enable_rls_policies.sql
```

### 4. Migrate Existing Users

**Option A: Manual Migration (Recommended for few users)**
1. Create each user in Supabase Auth dashboard
2. Update the `users.id` in your database to match the Supabase `auth.users.id`
3. Users will need to reset their passwords via Supabase

**Option B: Programmatic Migration**
1. Use the migration script as a guide: `apps/backend/scripts/migrate_to_supabase_auth.py`
2. Note: Supabase doesn't allow importing password hashes for security reasons
3. Users will need to use "Forgot Password" after migration

### 5. Update Database Connection (Optional)

For user-facing queries to respect RLS, you have two options:

**Option A: Continue using service role (Current)**
- Backend continues using service role key
- RLS is enforced at application level (via `get_current_user`)
- Simpler but less secure if service key is compromised

**Option B: Use connection pooling with JWT (Advanced)**
- Set up Supabase connection pooler with JWT tokens
- Each request uses authenticated connection
- RLS enforced at database level
- More secure but requires connection management

Currently, Option A is implemented. Option B requires additional infrastructure.

## Testing

### Test Authentication Flow

1. **Registration:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"testpass123","name":"Test User"}'
   ```

2. **Login:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"testpass123"}'
   ```

3. **Get User Info:**
   ```bash
   curl http://localhost:8000/api/v1/auth/me \
     -H "Authorization: Bearer <token-from-login>"
   ```

### Test RLS Policies

1. **Create two test users**
2. **Login as User 1 and create a trip**
3. **Login as User 2 and try to access User 1's trip**
4. **Verify User 2 cannot see User 1's data**

## RLS Policy Details

### Tables with RLS

- `users` - Users can view/update only their own record
- `trips` - Users can CRUD only their own trips
- `quotes` - Users can CRUD only their own quotes
- `policies` - Users can CRUD only their own policies
- `claims` - Users can CRUD only claims for their own policies
- `travelers` - Users can CRUD only their own travelers
- `chat_history` - Users can CRUD only their own chat history
- `audit_log` - Users can view their own logs; service role can insert/view all
- `rag_documents` - All authenticated users can read; service role can modify

### Service Role Policies

All tables have service role policies that allow the backend (using service role key) to bypass RLS. This is necessary for:
- Admin operations
- System operations
- Background jobs

## Troubleshooting

### "Supabase authentication not configured"
- Check that `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are set
- Restart the backend server after setting environment variables

### "Could not validate credentials"
- Token might be expired - user needs to login again
- Check that token is a valid Supabase JWT
- Verify Supabase client is properly initialized

### RLS blocking legitimate queries
- Check that user ID in database matches `auth.uid()`
- Verify RLS policies are correctly applied
- Check that backend is using service role for admin operations

### User can't see their own data
- Verify user ID matches: `SELECT id FROM users WHERE email = 'user@example.com'` vs `SELECT id FROM auth.users WHERE email = 'user@example.com'`
- Check RLS policies are enabled: `SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname = 'public'`

## Next Steps

1. **Email Verification**: Configure Supabase to require email verification
2. **Password Reset**: Set up password reset flow via Supabase
3. **Social OAuth**: Add Google/GitHub/etc. login options
4. **Connection Pooling**: Migrate to JWT-based connection pooling for better security
5. **Audit Logging**: Review audit logs to ensure proper access patterns

## Rollback Plan

If you need to rollback:

1. Disable RLS on all tables:
   ```sql
   ALTER TABLE users DISABLE ROW LEVEL SECURITY;
   -- Repeat for all tables
   ```

2. Revert backend changes to use custom JWT validation
3. Revert frontend to use custom auth flow
4. Users will need to use old passwords (if still in database)

## Support

For issues or questions:
- Check Supabase docs: https://supabase.com/docs/guides/auth
- Review RLS documentation: https://supabase.com/docs/guides/database/postgres/row-level-security

