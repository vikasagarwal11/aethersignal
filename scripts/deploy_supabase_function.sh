#!/bin/bash
# Deploy Supabase Edge Function
# Usage: ./scripts/deploy_supabase_function.sh

echo "🚀 Deploying Supabase Edge Function..."

# Check if Supabase CLI is installed
if ! command -v supabase &> /dev/null; then
    echo "❌ Supabase CLI not found. Install with: npm install -g supabase"
    exit 1
fi

# Login (if not already)
echo "📝 Checking Supabase login..."
supabase login

# Link project
echo "🔗 Linking to project..."
supabase link --project-ref scrksfxnkxmvvdzwmqnc

# Deploy function
echo "📦 Deploying social_ae_pull function..."
supabase functions deploy social_ae_pull

# Set secrets (prompt for values)
echo ""
echo "🔐 Setting environment variables..."
read -p "Enter your API endpoint URL (e.g., https://your-app.onrender.com/social/daily): " API_ENDPOINT
read -sp "Enter API secret key: " API_SECRET

supabase secrets set SOCIAL_AE_API_ENDPOINT="$API_ENDPOINT"
supabase secrets set API_SECRET_KEY="$API_SECRET"

echo ""
echo "✅ Edge Function deployed!"
echo ""
echo "📋 Next steps:"
echo "1. Go to Supabase Dashboard → Database → Cron Jobs"
echo "2. Create cron job: daily_social_ae_pull"
echo "3. Schedule: 0 1 * * * (1 AM UTC daily)"
echo "4. Function: social_ae_pull"
echo "5. Enable the cron job"

