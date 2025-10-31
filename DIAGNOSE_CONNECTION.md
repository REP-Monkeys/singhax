# Database Connection Diagnosis

## Current Status
- ❌ Connection refused on both ports (5432 and 6543)
- ✅ DNS resolution works
- ✅ IP not banned in Supabase
- ✅ Code fixes applied (SSL parameter conflicts resolved)

## Likely Causes

### 1. IP Allowlist Restrictions (Most Likely)
Your Supabase project may have IP allowlist restrictions that only allow your friend's IP.

**Check in Supabase Dashboard:**
1. Go to https://supabase.com/dashboard
2. Select project `zwyibrksagddbrqiqaqf`
3. Go to **Settings** → **Database** → **Connection Pooling**
4. Check **Network Restrictions** or **IP Allowlist**
5. If restricted, either:
   - Add your IP: `155.69.194.67`
   - Or remove restrictions (allow all IPs)

### 2. Ask Your Friend
Since your friend can connect, ask them:
- What's their exact `DATABASE_URL` format?
- Are they using a VPN?
- What's their IP address?
- Any special network configuration?

### 3. Network/Firewall Check
Test if you can reach the server:
```bash
nc -zv aws-1-ap-southeast-1.pooler.supabase.com 5432
nc -zv aws-1-ap-southeast-1.pooler.supabase.com 6543
```

## Current Connection String
```
postgresql://postgres.zwyibrksagddbrqiqaqf:yxtheactlgoat@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require
```

## Next Steps
1. Check Supabase IP allowlist settings
2. Compare connection string with your friend's working version
3. Test network connectivity with `nc` command
4. Try connecting from a different network/VPN to isolate the issue

