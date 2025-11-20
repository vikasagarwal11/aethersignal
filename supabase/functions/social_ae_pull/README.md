# Social AE Pull Edge Function

Supabase Edge Function that triggers daily Social AE pulls via your Python API.

## Deployment

```bash
# Install Supabase CLI if not already installed
npm install -g supabase

# Login to Supabase
supabase login

# Link to your project
supabase link --project-ref scrksfxnkxmvvdzwmqnc

# Deploy the function
supabase functions deploy social_ae_pull

# Set environment variables
supabase secrets set SOCIAL_AE_API_ENDPOINT=https://your-api.onrender.com/social/daily
supabase secrets set API_SECRET_KEY=your-secret-key
```

## Setup Cron Job

1. Go to Supabase Dashboard → Database → Cron Jobs
2. Create new cron job:
   - **Name**: `daily_social_ae_pull`
   - **Schedule**: `0 1 * * *` (1 AM UTC daily)
   - **Function**: `social_ae_pull`
   - **Enabled**: Yes

## Environment Variables

Set these in Supabase Dashboard → Project Settings → Edge Functions → Secrets:

- `SOCIAL_AE_API_ENDPOINT`: Your FastAPI endpoint URL
- `API_SECRET_KEY`: Secret key for API authentication (optional)

