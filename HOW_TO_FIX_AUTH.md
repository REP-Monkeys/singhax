# How to Fix the Authentication Issue

## Problem
Your `.env` file has placeholder values. You need to update it with real Supabase credentials.

## Step-by-Step Fix

### 1. Get Your Supabase Credentials

Go to: **https://supabase.com/dashboard**

1. Select your project (or create a new one)
2. Go to **Settings** → **API**
3. Copy these values:

#### From "Project API keys":
- **URL**: `https://your-project-ref.supabase.co`
- **anon public** key
- **service_role** key

#### From "JWT Settings" (scroll down):
- **JWT Secret**

**IMPORTANT:** The JWT Secret is different from the service_role key!

### 2. Update Your `.env` File

Edit the `.env` file in the project root:

```bash
# Navigate to project root
cd /Users/yuexin/Desktop/yuexin/singhax

# Edit the .env file
# (use your preferred editor: vim, nano, VS Code, etc.)
```

Replace these lines with your actual values:

```env
# Supabase Configuration
SUPABASE_URL=https://your-actual-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_JWT_SECRET=super-secret-jwt-token-string-here
```

### 3. Restart Backend Server

After updating `.env`, restart your backend:

```bash
# Stop the current server (Ctrl+C in the terminal running it)

# Start it again
cd apps/backend
python -m uvicorn app.main:app --reload
```

### 4. Verify It Works

Check the startup logs. You should see:

```
[CONFIG] Supabase URL configured: True
[CONFIG] Supabase anon key configured: True
[CONFIG] Supabase service role key configured: True
[CONFIG] Supabase JWT secret configured: True  ← Should be True now!
```

When you try to authenticate, you should see:

```
[DEBUG] Will use: JWT_SECRET
[DEBUG] JWT verification successful! User ID: 8d6c2356-4a7b-458f-96b6-01051fe71f24
```

### Example .env Values

Your values will look something like this (these are NOT real, just examples):

```env
SUPABASE_URL=https://abcdefghijklmnop.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFiY2RlZmdoaWprbG1ub3AiLCJyb2xlIjoiYW5vbiIsImlhdCI6MTYxNjIyOTIyMCwiZXhwIjoxOTMxODA1MjIwfQ.dcWIy-1234567890abcdef
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFiY2RlZmdoaWprbG1ub3AiLCJyb2xlIjoic2VydmljZV9yb2xlIiwiaWF0IjoxNjE2MjI5MjIwLCJleHAiOjE5MzE4MDUyMjB9.9876543210fedcba-Wiydc
SUPABASE_JWT_SECRET=super-secret-jwt-token-that-is-very-long-random-string-used-for-signing-tokens
```

## Troubleshooting

### "JWT verification failed: Signature verification failed"
- Make sure you copied the **JWT Secret** (not the service_role key)
- Double-check for extra spaces when copying
- Make sure the server was restarted after changing `.env`

### "Database connection failed"
- The token verification will now work
- But you may still have database connection issues
- Check your `DATABASE_URL` in `.env`

### "File .env not found"
- Make sure you're in the project root: `/Users/yuexin/Desktop/yuexin/singhax`
- The file might be named `.env.local` or similar
- You may need to create it from `infra/env.example`

## Quick Reference

**Where to find Supabase credentials:**
1. Dashboard: https://supabase.com/dashboard
2. Your project → **Settings** → **API**
3. Scroll down to see **Project API keys** and **JWT Settings**

**Which keys you need:**
- ✅ `SUPABASE_URL` - From Project API keys
- ✅ `SUPABASE_ANON_KEY` - From Project API keys (anon/public)
- ✅ `SUPABASE_SERVICE_ROLE_KEY` - From Project API keys (service_role)
- ✅ `SUPABASE_JWT_SECRET` - From JWT Settings (**this is the missing one!**)
