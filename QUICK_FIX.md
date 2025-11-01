# Quick Fix for Authentication Issue 🔧

## The Problem
Your `.env` file has placeholder values like `your-anon-key` instead of real Supabase credentials.

## The Solution (3 Steps)

### 1️⃣ Get Credentials from Supabase Dashboard
Visit: **https://supabase.com/dashboard/project/_/settings/api**

Copy these **4 values**:

```
📋 SUPABASE_URL                    → https://your-project.supabase.co
🔑 SUPABASE_ANON_KEY               → eyJhbG... (long key)
🔑 SUPABASE_SERVICE_ROLE_KEY       → eyJhbG... (long key)  
🔐 SUPABASE_JWT_SECRET             → very-long-secret-string (NOT the service role!)
```

⚠️ **IMPORTANT**: Scroll down to "JWT Settings" to find `SUPABASE_JWT_SECRET` - it's different from the service_role key!

### 2️⃣ Update `.env` File

Open: `/Users/yuexin/Desktop/yuexin/singhax/.env`

Replace these lines:
```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret-here  # ← ADD THIS LINE with real value!
```

### 3️⃣ Restart Backend

```bash
# Press Ctrl+C in terminal running the backend, then:
cd apps/backend
python -m uvicorn app.main:app --reload
```

## ✅ Success Looks Like

**On startup:**
```
[CONFIG] Supabase JWT secret configured: True  ← Should be True!
🚀 ConvoTravelInsure v1.0.0 started
```

**When authenticating:**
```
[DEBUG] Will use: JWT_SECRET
[DEBUG] JWT verification successful! User ID: ...
```

## 🆘 Still Not Working?

Check that:
- ✅ All 4 values are real (not placeholders)
- ✅ No extra spaces in `.env` file
- ✅ Server was restarted
- ✅ JWT Secret came from "JWT Settings" (not API keys)

See `HOW_TO_FIX_AUTH.md` for detailed instructions.
