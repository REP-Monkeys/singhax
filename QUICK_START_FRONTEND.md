# Quick Start: Frontend

## What Just Happened?

You tried running `npm run dev` from the **project root** instead of the `apps/frontend` directory.

## ✅ Correct Way to Start Frontend

### Method 1: Navigate to Frontend First

```powershell
# From project root
cd apps\frontend

# Then start the server
npm run dev
```

### Method 2: Specify the Path

```powershell
# From project root
cd apps\frontend; npm run dev
```

## 🎯 Complete Startup Sequence

1. **Start Backend** (required for API):
   ```powershell
   cd apps\backend
   uvicorn app.main:app --reload
   ```

2. **Start Frontend** (new terminal):
   ```powershell
   cd apps\frontend
   npm run dev
   ```

3. **Open Browser**:
   - Frontend: http://localhost:3000
   - API Docs: http://localhost:8000/docs

## ⚠️ Important Note

The `.env.local` file has been created with empty Supabase values.

**For full functionality**, you need to add your Supabase credentials:

```env
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-key-here
```

**Without Supabase**, you can still:
- ✅ View the landing page
- ✅ See the UI/styling
- ❌ Cannot test signup/login
- ❌ Cannot test onboarding
- ❌ Cannot create trips

## 🚀 Start Now!

```powershell
cd apps\frontend
npm run dev
```

Then open: **http://localhost:3000**

---

**Need full setup?** See `FRONTEND_SETUP.md` for detailed instructions.

