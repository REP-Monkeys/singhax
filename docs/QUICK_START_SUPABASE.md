# Quick Start: Connect to Supabase

Follow these steps to connect your application to Supabase in 5 minutes.

## 1️⃣ Get Your Connection String

1. Go to [supabase.com](https://supabase.com) and log in
2. Select your project (or create a new one)
3. Go to **Settings** → **Database**
4. Scroll to **Connection string**
5. Copy the **URI** format connection string

It looks like:
```
postgresql://postgres:[YOUR-PASSWORD]@[PROJECT-REF].supabase.co:5432/postgres
```

## 2️⃣ Create .env File

```bash
# From project root
cp infra/env.example .env
```

Edit `.env` and update `DATABASE_URL`:
```env
DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@[PROJECT-REF].supabase.co:5432/postgres?sslmode=require
```

## 3️⃣ Run Migrations

```bash
cd apps/backend
pip install -r requirements.txt
alembic upgrade head
```

## 4️⃣ Test Connection

```bash
# From project root
python scripts/test_supabase_connection.py
```

You should see:
```
✅ Connection successful!
🎉 Connected to Supabase!
📋 Found X table(s): ...
```

## 5️⃣ Start Your Application

```bash
cd apps/backend
python -m app.main
```

## ✅ Done!

Your application is now connected to Supabase. View your tables in the Supabase dashboard under **Table Editor**.

---

## Need Help?

- See [SUPABASE_SETUP.md](./SUPABASE_SETUP.md) for detailed instructions
- Check [Troubleshooting](#troubleshooting) below

## Troubleshooting

### Connection Refused
- Check Supabase firewall settings (allow your IP)
- Verify connection string is correct
- Try adding `?sslmode=require` to the URL

### No Tables Found
- Run: `cd apps/backend && alembic upgrade head`
- Check migration logs for errors

### SSL Error
- Ensure connection string includes `?sslmode=require`
- For connection pooling, use port `6543` instead of `5432`


