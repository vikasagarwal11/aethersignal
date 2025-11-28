# Update .env File - Quick Instructions

## ✅ Your Supabase Credentials

I have your credentials. You need to add them to your `.env` file.

## 📝 Steps to Update .env

1. **Open `.env` file** in: `C:\Vikas\Projects\aethersignal\.env`

2. **Add these lines** (or update if they exist):

```env
# Supabase Configuration (Multi-Tenant System)
SUPABASE_URL=https://scrksfxnkxmvvdzwmqnc.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNjcmtzZnhua3htdnZkendtcW5jIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjM2MDM2NTcsImV4cCI6MjA3OTE3OTY1N30.tumWvHiXv7VsX0QTm-iyc5L0dwGFDTtgEkHAUieMcIY
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNjcmtzZnhua3htdnZkendtcW5jIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MzYwMzY1NywiZXhwIjoyMDc5MTc5NjU3fQ.dUwNCFto69ZqCqcjDUMDlOuEkZ0PArK9B-RkNTp5jmw
```

3. **Save the file**

4. **Restart Streamlit** if it's running

## ✅ Verify

After updating, run:
```bash
python setup_supabase.py
```

You should see all checks pass!

