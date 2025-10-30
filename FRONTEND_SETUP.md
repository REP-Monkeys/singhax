# Frontend Setup and Testing Guide

## ✅ Quick Start

### Prerequisites
- **Node.js** 18+ installed
- **Backend running** on http://localhost:8000
- **Supabase project** configured (for authentication)

---

## 🚀 Step-by-Step Setup

### 1. **Create Environment File**

Create `apps/frontend/.env.local`:

```env
# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Supabase Configuration (get from https://app.supabase.com/project/_/settings/api)
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key
```

**Example:**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_SUPABASE_URL=https://abcdefgh.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFiY2RlZmdoIiwiYXVkIjoiYW5vbiIsInJvbGUiOiJhbm9uIn0.abc123...
```

### 2. **Install Dependencies**

```bash
cd apps/frontend
npm install
```

### 3. **Start Backend First** (Required!)

The frontend needs the backend API running. In a separate terminal:

```bash
cd apps/backend
uvicorn app.main:app --reload
```

Backend should be running on http://localhost:8000

### 4. **Start Frontend**

```bash
cd apps/frontend
npm run dev
```

Frontend will start on http://localhost:3000

---

## 🧪 Testing the Application

### Without Supabase (Limited Testing)

If you don't have Supabase configured yet, you can still test the UI:

1. **Open** http://localhost:3000
2. **See** the landing page
3. **Click** "Get Quote" → Will try to redirect to login
4. **Cannot** test signup/login without Supabase

### With Supabase (Full Testing)

#### A. **Configure Supabase**

1. Go to https://app.supabase.com
2. Create a project or use existing
3. Get credentials from Settings → API
4. Add to `apps/frontend/.env.local`

#### B. **Configure Backend**

Update `apps/backend/.env`:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

#### C. **Test Flow**

1. **Landing Page** → http://localhost:3000
2. **Sign Up** → Click "Get started" → Fill form → Create account
3. **Onboarding** → Complete multi-step form
4. **Dashboard** → See trips (empty initially)
5. **Chat/Quote** → Click "New Trip" → Start conversation with AI
6. **Voice** → Click microphone icon → Speak

---

## 📋 Testing Checklist

### ✅ Basic UI Testing

- [ ] Landing page loads
- [ ] Navigation works
- [ ] Sign up page displays
- [ ] Login page displays
- [ ] Responsive design (try resizing window)

### ✅ Authentication Testing

- [ ] Can create account
- [ ] Can login
- [ ] Protected routes redirect to login
- [ ] Can logout

### ✅ Onboarding Testing

- [ ] All 4 steps display correctly
- [ ] Form validation works
- [ ] Can submit onboarding data
- [ ] Redirects to dashboard after submission

### ✅ Dashboard Testing

- [ ] Dashboard loads
- [ ] Empty state displays
- [ ] "New Trip" button works
- [ ] Can switch tabs (Upcoming/Past)

### ✅ Chat Interface Testing

- [ ] Chat interface loads
- [ ] Can type and send messages
- [ ] Backend responds
- [ ] Messages display correctly
- [ ] Loading states work
- [ ] Error handling works

### ✅ Voice Testing

- [ ] Voice button appears
- [ ] Clicking starts recording
- [ ] Speech recognition works
- [ ] Transcript populates input

---

## 🐛 Troubleshooting

### Frontend Won't Start

**Error:** `Module not found`
```bash
# Solution: Install dependencies
cd apps/frontend
rm -rf node_modules package-lock.json
npm install
```

**Error:** `Port 3000 already in use`
```bash
# Solution: Kill process using port 3000
# Or use different port:
PORT=3001 npm run dev
```

### Backend Connection Errors

**Error:** `Failed to fetch` or CORS errors
- **Check:** Backend is running on http://localhost:8000
- **Check:** `NEXT_PUBLIC_API_URL` is correct
- **Check:** Backend CORS allows `http://localhost:3000`

### Supabase Errors

**Error:** `Supabase URL or Anon Key not found`
- **Check:** `.env.local` file exists in `apps/frontend/`
- **Check:** Environment variables are set correctly
- **Check:** No typos in variable names

**Error:** `Invalid Supabase token`
- **Check:** Supabase credentials are correct
- **Check:** Backend has matching credentials
- **Check:** Supabase project is active

### Authentication Issues

**Error:** Can't login or signup
- **Check:** Supabase is configured correctly
- **Check:** User exists in Supabase Auth
- **Check:** Backend `/auth/sync-user` endpoint works
- **Check:** Browser console for errors

---

## 📁 File Structure

```
apps/frontend/
├── .env.local              # Environment variables (create this)
├── package.json
├── src/
│   ├── app/
│   │   ├── page.tsx        # Landing page
│   │   └── app/
│   │       ├── login/      # Login page
│   │       ├── signup/     # Signup page
│   │       ├── onboarding/ # Onboarding form
│   │       ├── dashboard/  # Trip dashboard
│   │       └── quote/      # Chat interface
│   ├── components/
│   │   ├── CopilotPanel.tsx
│   │   ├── VoiceButton.tsx
│   │   └── ProtectedRoute.tsx
│   ├── contexts/
│   │   └── AuthContext.tsx
│   └── lib/
│       ├── supabase.ts
│       └── utils.ts
└── public/                 # Static assets
```

---

## 🎯 Quick Commands

```bash
# Install dependencies
cd apps/frontend && npm install

# Start development server
cd apps/frontend && npm run dev

# Build for production
cd apps/frontend && npm run build

# Start production server
cd apps/frontend && npm start

# Lint code
cd apps/frontend && npm run lint
```

---

## 🔗 Important URLs

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **Backend Docs:** http://localhost:8000/docs
- **Supabase Dashboard:** https://app.supabase.com

---

## 📝 Environment Variables Explained

| Variable | Required | Description |
|----------|----------|-------------|
| `NEXT_PUBLIC_API_URL` | ✅ Yes | Backend API base URL |
| `NEXT_PUBLIC_SUPABASE_URL` | ✅ Yes | Supabase project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | ✅ Yes | Supabase anonymous key |

**Note:** All `NEXT_PUBLIC_*` variables are exposed to the browser.

---

## 🎓 Development Tips

### Hot Reload

Next.js has hot reload enabled. Changes to `.tsx` files automatically refresh the browser.

### Debugging

1. **Browser Console** → Check for errors
2. **Network Tab** → Check API calls
3. **React DevTools** → Inspect component state
4. **Backend Logs** → Check terminal where uvicorn is running

### Testing Features

- **Landing Page:** Just view http://localhost:3000
- **Auth:** Need Supabase configured
- **Chat:** Need backend + GROQ_API_KEY configured
- **Onboarding:** Need Supabase configured
- **Dashboard:** Need at least one trip created

---

## 📞 Getting Help

If you encounter issues:

1. **Check** browser console for errors
2. **Check** backend logs in terminal
3. **Verify** all environment variables are set
4. **Ensure** backend is running
5. **Read** error messages carefully

---

## ✅ Success Indicators

You know it's working when:

- ✅ Frontend loads without errors
- ✅ Can navigate between pages
- ✅ Backend API responds
- ✅ Can sign up/login
- ✅ Can complete onboarding
- ✅ Chat interface works
- ✅ Messages get AI responses

---

**Good luck! 🚀**

